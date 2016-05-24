#!/usr/bin/env python

import sys
from jsonrpc import JsonRpcProxy, JsonError

def main(*args):
   ### Create a JSON-RPC proxy for the inventory service
   ###
   netld = JsonRpcProxy("https://{0}/rest".format('localhost'), 'admin', 'password')

   ### use the inventory service to query for devices
   query = raw_input('Enter an individual IP address or IP/CIDR (eg. 10.0.0.0/24): ')

   pageData= {'offset': 0, 'pageSize': 500}

   # Inventory.search parameters:
   #   network, search scheme, query data, paging data, sort column, descending
   pageData = netld.call('Inventory.search', 'Default', 'ipAddress', query, pageData, 'ipAddress', False)

   print "Search found " + str(pageData['total']) + " devices.";
   print "----------------------------------------------";

   for device in pageData['devices']:
      print device['ipAddress'] + "   " + device['hostname']

   ### Logout using the security service to be nice to the server
   ###
   netld.call('Security.logoutCurrentUser')


if __name__=="__main__":
   main(sys.argv)
