#!/usr/bin/env python

import sys
import json
import urllib2
import base64
import datetime
import pprint
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
archivePath = raw_input('Enter the configuration archive path as it appears in NetLD: ')

print "Snapshot             Path              Timestamp             Size  User"
print "=============================================================================="

changeLog = netld.call('Configuration.retrieveArchiveChangeLog', netld_network, ipAddress, archivePath, None)

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

print "" #blank line
configPath = raw_input('Enter the path of an archive file to display it: ')
revision = netld.call('Configuration.retrieveRevision', netld_network, ipAddress, archivePath + '!' + configPath, None)

print "\nRevision: "
pp = pprint.PrettyPrinter(indent=3)
pp.pprint(revision)
print "\n" + configPath + " content:\n"
lines = str(base64.b64decode(revision['content'])).split('\n')
for i in lines:
   print i

### Logout using the security service to be nice to the server
###
netld.call('Security.logoutCurrentUser')
