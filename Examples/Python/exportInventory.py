#!/usr/bin/env python

import sys
import csv
import getopt
from time import localtime, strftime
from jsonrpc import JsonRpcProxy, JsonError

netld_host = 'localhost'
netld_user = 'admin'
netld_pass = 'password'
netld_network = 'Default'

def usageAndExit():
   print 'Usage: ' + sys.argv[0] + ' [OPTIONS] -o <output file>'
   print 'Export the device inventory to a CSV file.'
   print
   print '  -h host --host=host  Hostname or IP address of Net LineDancer server'
   print '  -u username --user=username  Net LineDancer username'
   print '  -p password --password=password  Net LineDancer password'
   print '  -m --managed-network=network  The name of a Net LineDancer network'
   print '  -o The name of the CSV output file'
   sys.exit(2)

_netld_svc = None

def main(argv):
   try:
      opts, args = getopt.getopt(argv,"h:u:p:m:o:", ["host=","user=","password=","--managed-network=","output="])
   except getopt.GetoptError:
      usageAndExit()

   global netld_host, netld_user, netld_pass, netld_network

   outputFile = ''
   netld_network = 'Default'

   for opt, arg in opts:
      if opt in ('-o', '--output'):
         outputFile = arg
      if opt in ('-h', '--host'):
         netld_host = arg
      if opt in ('-u', '--user'):
         netld_user = arg
      if opt in ('-p', '--password'):
         netld_pass = arg
      if opt in ('-m', '--managed-network'):
         netld_network = arg

   if outputFile == '':
      outputFile = "InventoryReport" + strftime("%y%m%d-%H%M%S", localtime()) + ".csv"

   _netld_svc = JsonRpcProxy("https://{0}/rest".format(netld_host), netld_user, netld_pass)

   pageData = {'offset': 0, 'pageSize': 500}

   while True:
      pageData = _netld_svc.call('Inventory.search', ['Default'], 'ipAddress', "", pageData, 'ipAddress', False)

      csvfile = open(outputFile, 'w')
      cw = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)

      for device in pageData['devices']:
         cw.writerow([
            noneSafe(device['backupStatus']),
            noneSafe(device['ipAddress']),
            noneSafe(device['hostname']),
            noneSafe(device['hardwareVendor']),
            noneSafe(device['model']),
            noneSafe(device['deviceType']),
            noneSafe(device['serialNumber']),
            noneSafe(device['adapterId']),
            noneSafe(device['osVersion']),
            noneSafe(device['softwareVendor']),
            noneSafe(device['backupElapsed']),
            noneSafe(device['memoSummary']),
            noneSafe(device['custom1']),
            noneSafe(device['custom2']),
            noneSafe(device['custom3']),
            noneSafe(device['custom4']),
            noneSafe(device['custom5'])
         ])

      if pageData['offset'] + pageData['pageSize'] >= pageData['total']:
         break;

      pageData['offset'] += pageData['pageSize']

   if pageData['total'] == 0:
      quit

   _netld_svc.call('Security.logoutCurrentUser')

def noneSafe(value):
   return "" if value is None else value

if __name__ == "__main__":
   main(sys.argv[1:])
