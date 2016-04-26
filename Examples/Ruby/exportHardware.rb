#!/usr/bin/env ruby -W0

require 'jimson'
require 'csv'
require 'net/https'
require 'open-uri'
require 'zlib'
require 'optparse'

RAW_DEFLATE_ENCODING = -15

outputFile = ''

options = {}
OptionParser.new do |opts|
  opts.banner = "Usage: \n  exportHardware.rb [ <output file> ]"
end.parse!

if ARGV.empty?
  outputFile = "HardwareReport" + DateTime.parse(Time.now.to_s).strftime("%y%m%d-%H%M%S") + ".csv"
else
  outputFile = ARGV[0]
end

uri = URI.parse('https://localhost')
https = Net::HTTP.new(uri.host, uri.port)
https.use_ssl = true
https.verify_mode = OpenSSL::SSL::VERIFY_NONE
response = https.start { |https|
  https.get("/rest?j_username=admin&j_password=password")
}
cookie = response['set-cookie'].split(';', 2)[0] 
  
netld = Jimson::Client.new("https://localhost/rest?j_username=admin&j_password=password", 
          "Cookie" => cookie)

network = 'Default'
job_name = 'Hardware Report'

job = {
    'managedNetwork' => network,
    'jobName' => job_name,
    'jobType' => 'Report',
    'description' => '',
    'jobParameters' => {
        'tool' => 'ziptie.reports.hardware',
        'ipResolutionScheme' => 'ipAddress',
        'ipResolutionData' => '',
        'managedNetwork' => network,
        'format' => 'csv'
    },
}

execution = netld['Scheduler.runNow', job]

puts "** executing job **"
execution_id = execution['id']
 
while not execution['endTime']
    if execution['completionState'] == 1 or execution['completionState'] == 2
        print '** execution canceled **'
        break
    end
    sleep(1)
    execution = netld['Scheduler.getExecutionDataById', execution_id]
end

url = URI.parse("https://localhost/servlet/pluginDetail?executionId=" + execution_id.to_s)   

response = https.start { |https|
  https.get(url, 
    {"Cookie" => cookie, 
      "Accept-Encoding" => "deflate;q=0.6"}
  )
}

content = Zlib::Inflate.new(RAW_DEFLATE_ENCODING).inflate(response.body)

file = open(outputFile, 'w')
file.write(content)
file.close()

puts "** Hardware Report Export execution complete **"  

netld['Security.logoutCurrentUser']
