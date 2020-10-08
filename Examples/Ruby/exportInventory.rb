#!/usr/bin/env ruby -W0

require 'jimson'
require 'csv'

OpenSSL::SSL::VERIFY_PEER = OpenSSL::SSL::VERIFY_NONE

if ARGV.empty?
  outputFile = "InventoryReport" + DateTime.parse(Time.now.to_s).strftime("%y%m%d-%H%M%S") + ".csv"
else
  outputFile = ARGV[0]
end

netld = Jimson::Client.new("https://10.0.40.50/rest?j_username=admin&j_password=password")

pageData = { 'offset' => 0, 'pageSize' => 100, 'total' => 500 }

until pageData['offset'] + pageData['pageSize'] >= pageData['total'] do   
  pageData = netld['Inventory.search', 'Default', 'ipAddress', "", pageData, 'ipAddress', false]
  
  CSV.open(outputFile, "wb") do |csv|
    for device in pageData['devices']
      csv << [device['backupStatus'], device['ipAddress'], device['hostname'], device['hardwareVendor'],                
              device['model'], device['deviceType'], device['serialNumber'],device['adapterId'],                 
              device['osVersion'], device['softwareVendor'], device['backupElapsed'], device['memoSummary'],                
              device['custom1'], device['custom2'], device['custom3'], device['custom4'], 
              device['custom5']]
    end
  end
  pageData['offset'] += pageData['pageSize']
end

netld['Security.logoutCurrentUser']
