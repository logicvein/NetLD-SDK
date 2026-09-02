#!/usr/bin/env ruby -W0

require 'jimson'

### Create a JSON-RPC proxy for the inventory service
###
netld = Jimson::Client.new("https://localhost/rest?j_username=admin&j_password=password")

### use the inventory service to create a device
error = netld['Inventory.createDevice', 'Default', '10.10.10.10', 'Cisco::IOS']

print "Create device result: " + (error ? error : "Created") + "\n"

### get the device we just created and print it's address from the returned object
device = netld['Inventory.getDevice', 'Default', '10.10.10.10']

if device
   print 'Retrieved device: ' + device['ipAddress'] + "\n"
else
   print "Device does not exist!\n"
end

### now delete the device
netld['Inventory.deleteDevice', 'Default', '10.10.10.10']
print "Device deleted.\n"

### Logout using the security service to be nice to the server
###
netld['Security.logoutCurrentUser']
