#!/usr/bin/env python

from jsonrpc import JsonRpcProxy, JsonError

def notnull(value):
    if value is None:
        return ''
    return value

### Create a JSON-RPC proxy for the inventory service
###
netld = JsonRpcProxy.fromHost("localhost", "admin", "password")

###Print column headers of the report
print "IP Address,Hostname,Interface Name,Type,Interface IP,MAC"

offset=0
total = 0

while True:
    pageData= {'offset': offset, 'pageSize': 500, 'total': total}

    #use the inventory service to retrieve device
    pageData = netld.call('Inventory.search', [], 'ipAddress', '', pageData, 'ipAddress', False)

    for device in pageData['devices']:
        #use the inventory service to retrieve interfaces for device
        interfaces = netld.call('Inventory.getDeviceInterfaces', device['network'], device['ipAddress'])

        for interface in interfaces:
            print device['ipAddress'] + ',' + notnull(device['hostname']) + ',' + notnull(interface['name']) + ',' + notnull(interface['type']) + ',' + ' '.join(map(lambda x: x['ipAddress'], interface['ipAddresses'])) +',' + notnull(interface['macAddress'])

    offset = offset + pageData['pageSize']
    total = pageData['total']

    if offset >= total:
        break

### Logout using the security service to be nice to the server
###
netld.call('Security.logoutCurrentUser')
