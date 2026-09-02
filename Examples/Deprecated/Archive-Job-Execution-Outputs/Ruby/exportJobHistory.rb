#!/usr/bin/env ruby -W0

require 'jimson'
require 'uri'
require 'net/https'
require 'open-uri'
require 'zlib'
require 'optparse'
require 'inifile'
require 'date'

HOST='host'
USERNAME='username'
PASSWORD='password'
LAST_END_TIME='lastEndTime'

RAW_DEFLATE_ENCODING = -15

def main()
    options = {}
    OptionParser.new do |opts|
      opts.banner = "Usage: \n  exportJobHistory.rb [ <output file> ] [ <config file> ]"
    end.parse!
    
    outputFile = nil
    if ARGV.empty?
      outputFile = "JobHistory" + DateTime.parse(Time.now.to_s).strftime("%y%m%d-%H%M%S") + ".txt"
      configFile = './config.ini'
    else
      outputFile = ARGV[0]
      configFile = ARGV[1]
    end
    
    config = IniFile.load(configFile)

    config.each_section { |section|
        host = config[section][HOST]
        user = config[section][USERNAME]
        password = config[section][PASSWORD]
    
        if config[section][LAST_END_TIME]
            iniLastEndTime = config[section][LAST_END_TIME]
        else
            iniLastEndTime = 0
        end
        
        begin
            iniLastEndTime = exportJobHistory(outputFile, host, user, password, iniLastEndTime)
            
            if iniLastEndTime
              config[section][LAST_END_TIME] = iniLastEndTime
              config.write
            end 
        rescue => e
            puts e.to_s
        end
    }
end 

def millisToDate(millis)
    tmp = Time.at(millis / 1000).gmtime.strftime("%Y-%m-%d %H:%M:%S")
    return tmp 
end

def makeJobList(execution)
    startTime = execution['startTime'] / 1000
    endTime = execution['endTime'] / 1000
    
    jobList = "\n[ " + execution['status'].to_s + " / " +
            execution['jobName'].to_s + " / " +
            execution['managedNetwork'].to_s + " / " + 
            execution['executor'].to_s + " / S:" +
            Time.at(startTime).strftime('%Y-%m-%d %H:%M:%S') + " / E:" + 
            Time.at(endTime).strftime('%Y-%m-%d %H:%M:%S') + 
            " ]\n"
            
    return jobList
end

def exportJobHistory(outputFile, host, user, password, inilastEndTime)
  
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
 
    pageData = {'offset' => 0, 'pageSize' => 1000}
    pageData = netld['Scheduler.getExecutionData', pageData, 'endTime', 'True']

    file = nil
    lastExecuteTime = nil
    isFirst = 0

    pageData['executionData'].each { |execution|
      
        startTime = execution['startTime']
        lastEndTime = execution['endTime']
        endTime = millisToDate(lastEndTime)

        execution_id = execution['id']

        details = netld['Plugins.getExecutionDetails', execution_id]
          
        if details and execution['jobType'] == 'Script Tool Job' and lastEndTime > inilastEndTime

          if isFirst
            file = open(outputFile, 'w')
            lastExecuteTime = lastEndTime  
            isFirst = nil
          end
          
          details.each { |detail|
      
            jobList = makeJobList(execution)
            file.write(jobList)
            
            url = URI.parse("https://" + host + "/servlet/pluginDetail?executionId=" + execution_id.to_s + "&recordId=" + detail['id'].to_s)   
            response = https.start { |https|
              https.get(url, 
                {"Cookie" => cookie, "Accept-Encoding" => "deflate;q=0.6"}
              )
            }
            content = Zlib::Inflate.new(RAW_DEFLATE_ENCODING).inflate(response.body)
            
            file.write(content)
          }
        end
    }    

    if File.exist?(outputFile)
      file.close()
      puts "Wrote " + outputFile
    else
      puts "No Job History"
    end
    
    netld['Security.logoutCurrentUser']
    
    return lastExecuteTime
end

if __FILE__ == $0
  main()
end
