#!/usr/bin/env python

import sys
import json
import urllib2
import base64
import datetime
from jsonrpc import JsonRpcProxy, JsonError

netld_host = 'localhost'
netld_user = 'admin'
netld_pass = 'password'
netld_network = 'Default'

### Create a JSON-RPC proxy
###
netld = JsonRpcProxy("https://{0}/rest".format(netld_host), netld_user, netld_pass)

### use the configuration service to retrieve a page of change logs
ipAddress = raw_input('Enter an individual IP address or IP/CIDR (eg. 10.0.0.0/24): ')

print "Snapshot             Path              Timestamp             Size  User"
print "=============================================================================="

pageData= {'offset': 0, 'pageSize': 10}

while True:
    pageData = netld.call('Configuration.retrieveSnapshotChangeLog', 'Default', ipAddress, pageData)

    for changeLog in pageData['changeLogs']:
        snapShot = changeLog['timestamp']

        firstLine = True
        for change in changeLog['changes']:
            if firstLine:
                sys.stdout.write(datetime.datetime.fromtimestamp(snapShot/1000).strftime('%Y-%m-%d %H:%M:%S') + "  ")
                firstLine = False
            else:
                sys.stdout.write('{:<21}'.format(''))

            print '{:<15}'.format(change['path']) + "   " \
                + datetime.datetime.fromtimestamp(change['revisionTime']/1000).strftime('%Y-%m-%d %H:%M:%S') + "  " \
                + '{:>5}'.format(change['size']) + "  " \
                + change['author']

    if pageData['offset'] + pageData['pageSize'] >= pageData['total']:
        break;

    pageData['offset'] += pageData['pageSize']
    pageData['changeLogs'] = None

if pageData['total'] == 0:
    quit

print "\nRetreiving first 10 lines of newest text configuration:"
print "======================================================"

pageData= {'offset': 0, 'pageSize': 1}
pageData = netld.call('Configuration.retrieveSnapshotChangeLog', 'Default', ipAddress, pageData)

if pageData['total'] > 0:
    for change in pageData['changeLogs'][0]['changes']:
        if change['mimeType'] != 'text/plain':
            continue;

        revision = netld.call('Configuration.retrieveRevision', 'Default', ipAddress, change['path'], change['revisionTime'])
        print revision;
        lines = str(base64.b64decode(revision['content'])).split('\n')
        for i in range(10):
            print lines[i]
        break

### Logout using the security service to be nice to the server
###
netld.call('Security.logoutCurrentUser')
