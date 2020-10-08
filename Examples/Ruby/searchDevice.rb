#!/usr/bin/env ruby -W0

require 'jimson'

OpenSSL::SSL::VERIFY_PEER = OpenSSL::SSL::VERIFY_NONE

### Create a JSON-RPC proxy for the inventory service
###
netld = Jimson::Client.new("https://10.0.40.50/rest?j_username=admin&j_password=password")

### Search the inventory
print "Enter an individual IP address or IP/CIDR (eg. 10.0.0.0/24): ";
query = gets.strip

pageData = { 'offset' => 0, 'pageSize' => 500 }

pageData = netld['Inventory.search', 'Default', 'ipAddress', query, pageData, 'ipAddress', false]

print "Search found " + pageData['total'].to_s() + " devices.\n"
print "----------------------------------------------\n"

for device in pageData['devices']
   print device['ipAddress'] + "\t" + device['hostname'] + "\n";
end

### Logout using the security service to be nice to the server
###
netld['Security.logoutCurrentUser']
