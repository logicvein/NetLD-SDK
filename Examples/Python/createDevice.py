#!/usr/bin/env python

import sys
import json
import urllib2
from jsonrpc import JsonRpcProxy, JsonError

### Create a JSON-RPC proxy for the inventory service
###
netld = JsonRpcProxy.fromHost("localhost", "admin", "password")

### use the inventory service to create a device
error = netld.call('Inventory.createDevice', 'Default', '10.10.10.10', 'Cisco::IOS')

print "Create device result: " + ("Created" if (error is None) else error)

### get the device we just created and print it's address from the returned object
device = netld.call('Inventory.getDevice', 'Default', '10.10.10.10');

if device is not None:
    print 'Retrieved device: ' + device['ipAddress'];
else:
    print 'Device does not exist!'

### now delete the device
netld.call('Inventory.deleteDevice', 'Default', '10.10.10.10')
print "Device deleted."

### Logout using the security service to be nice to the server
###
netld.call('Security.logoutCurrentUser')
