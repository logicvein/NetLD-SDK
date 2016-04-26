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
LAST_TIMESTAMP='lastConfigTimestamp'

def usageAndExit()
    puts 'Usage:'
    puts '  exportConfigs.py <output directory> <settings file>'
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
        puts 'Setting file does not exist: ' + configFile
        exit
    end

    config = IniFile.load(configFile)
  
    config.each_section { |section|
        host = config[section][HOST]
        user = config[section][USERNAME]
        password = config[section][PASSWORD]
    
        if config[section][LAST_TIMESTAMP]
            lastTimestamp = config[section][LAST_TIMESTAMP]
        else
            lastTimestamp = 0
        end
        
        begin
            lastTimestamp = exportConfigs(output, host, user, password, lastTimestamp)
            
            if lastTimestamp
              config[section][LAST_TIMESTAMP] = lastTimestamp
              config.write
            end 
        rescue => e
            puts e.to_s
        end
      }  
end


def createFilename(output, network, ipAddress, path, timestamp)
    localPath = path
    if localPath.index('/') == 0
        localPath = localPath[1..-1]
    end  

    return output + '/' + network + '/' + ipAddress + '/' + Time.at(timestamp/1000).strftime('%Y-%m-%d_%H-%M_') + localPath
end  

def millisToDate(millis)
    tmp = Time.at(millis / 1000).gmtime.strftime("%Y-%m-%d %H:%M:%S")
    return tmp 
end

def hash_to_query(hash)
  return URI.encode(hash.map{|k,v| "#{k}=#{v}"}.join("&"))
end 

def exportConfigs(output, host, user, password, lastTimestamp)
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
    
    configs = netld['Configuration.retrieveConfigsSince', lastTimestamp]
    configs.each { |config|
        lastTimestamp = config['lastChanged']
        timestamp = millisToDate(lastTimestamp)

        network = config['managedNetwork']
        ipAddress = config['ipAddress']
        path = config['path']
        
        filename = createFilename(output, network, ipAddress, path, lastTimestamp)

        directory = File.dirname filename
        unless File.exist?(directory)
            FileUtils.mkdir_p(directory)
        end
        
        params = {
                'op' => 'config',
                'ipAddress' => ipAddress,
                'managedNetwork' => network,
                'configPath' => path,
                'timestamp' => Time.at(config['lastChanged'] / 1000).gmtime.strftime("%Y-%m-%dT%H:%M:%S"),
                'j_username' => user,
                'j_password' => password
                }
        
        url = URI.parse("https://" + host + "/servlet/inventoryServlet?" + hash_to_query(params))
        response = https.start { |https|
          https.get(url,
            {"Cookie" => cookie, "Accept-Encoding" => "deflate;q=0.6"}
          )
        }
        
        file = open(filename, 'w')
        file.write(response.body)
        file.close()

        puts "Wrote " + filename
    }
        
    netld['Security.logoutCurrentUser']

    return lastTimestamp
end

if __FILE__ == $0
  main()
end