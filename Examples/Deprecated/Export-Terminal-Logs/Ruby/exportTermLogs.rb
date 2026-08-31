#!/usr/bin/env ruby -W0

require 'jimson'
require 'uri'
require 'net/http'
require 'optparse'
require 'inifile'
require 'fileutils'

HOST='host'
USERNAME='username'
PASSWORD='password'
LAST_SESSION_END='lastSessionEnd'

RAW_DEFLATE_ENCODING = -15

def usageAndExit()
    puts 'Usage:'
    puts '  exportTermLogs.rb <output directory> <config file>'
    exit
end

def main()
  
    output = ARGV[0]
    configFile = ARGV[1]
  
    if ARGV.empty?
        usageAndExit()
    end
  
    unless File.exist?(output)
        puts 'Output directory does not exist: ' + output
        exit
    end
    unless File.file?(configFile)
        puts 'Config file does not exist: ' + configFile
        exit
    end
    
    config = IniFile.load(configFile)

    config.each_section { |section|
        host = config[section][HOST]
        user = config[section][USERNAME]
        password = config[section][PASSWORD]
    
        if config[section][LAST_SESSION_END]
          lastSessionEnd = config[section][LAST_SESSION_END]
        else
          lastSessionEnd = 0
        end
        
        begin
            lastSessionEnd = exportJobHistory(output, host, user, password, lastSessionEnd)
            
            if lastSessionEnd
              config[section][LAST_SESSION_END] = lastSessionEnd
              config.write
            end 
        rescue => e
            puts e.to_s
        end
    }
end 

def createFilename(output, startTime, termlog)
    count = 0
    localStart = Time.at(startTime/1000).strftime("%Y-%m-%d %H:%M:%S")
    filename = output + filenamePrefix(startTime, termlog) + '_' + Time.at(startTime/1000).strftime('%H-%M') + '.log'
    while File.exist?(filename)
        count = count + 1
        filename = output + filenamePrefix(startTime, termlog) + Time.at(startTime/1000).strftime('%H-%M-%S') + '-' + count.to_s + '.log'
    end

    return filename
end  

def filenamePrefix(startTime, termlog)
    return '/' + Time.at(startTime/1000).strftime('%Y-%m-%d') + '/' + termlog['ipAddress'].to_s + '_' + termlog['hostname'].to_s + '_'
end

def millisToDate(millis)
    tmp = Time.at(millis / 1000).gmtime.strftime("%Y-%m-%d %H:%M:%S")
    return tmp 
end


def hash_to_query(hash)
  return URI.encode(hash.map{|k,v| "#{k}=#{v}"}.join("&"))
end 

def exportJobHistory(output, host, user, password, lastSessionEnd)
    uri = URI.parse("https://" + host)
    https = Net::HTTP.new(uri.host, uri.port)
    https.use_ssl = true
    https.verify_mode = OpenSSL::SSL::VERIFY_NONE
    response = https.start { |https|
      https.get("/rest?j_username=" + user + "&j_password=" + password)
    }
    cookie = response['set-cookie'].split(';', 2)[0] 
  
    netld = Jimson::Client.new("https://" + host + "/rest?j_username=" + user + "&j_password=" + password, 
              "Cookie" => cookie)
    firstSessionEnd = millisToDate(lastSessionEnd)
    scheme = 'since'
    data = Time.at(lastSessionEnd / 1000).gmtime.strftime("%Y-%m-%d")

    termlogs = netld['TermLogs.search', scheme, data, "sessionEnd", 'False']
    termlogs.each { |termlog|
        sessionStart = millisToDate(termlog['sessionStart'])
        lastSessionEnd = termlog['sessionEnd']
        sessionEnd = millisToDate(lastSessionEnd)

        puts termlog['ipAddress'] + ': ' + sessionEnd
        puts " Last: " + lastSessionEnd.to_s

        filename = createFilename(output, termlog['sessionStart'], termlog)

        directory = File.dirname filename
        unless File.exist?(directory)
            FileUtils.mkdir_p(directory)
        end
        
        params = {
          'op' => 'content',
          'sessionStart' => Time.at(termlog['sessionStart'] / 1000).gmtime.strftime("%Y-%m-%dT%H:%M:%S"),
          'ipAddress' => termlog['ipAddress'],
          'managedNetwork' => termlog['managedNetwork'].encode('utf-8'),
          'stripXml' => 'true',
          'j_username' => user,
          'j_password' => password
        }
        
        url = URI.parse("https://" + host + "/servlet/termlog?" + hash_to_query(params))
        response = https.start { |https|
          https.get(url,
            {"Cookie" => cookie, "Accept-Encoding" => "deflate;q=0.6"}
          )
        }

        file = open(filename, 'w')
        file.write(response.body)
        file.close()

        print "Wrote " + filename
    }
    
    netld['Security.logoutCurrentUser']

    return lastSessionEnd
end

if __FILE__ == $0
  main()
end
