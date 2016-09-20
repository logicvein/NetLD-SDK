#!/usr/bin/env python

import sys
import csv
import getopt
import math
import time
import urllib
import urllib2
import zlib
import pprint
from time import localtime, strftime
from jsonrpc import JsonRpcProxy, JsonError

netld_host = 'localhost'
netld_user = 'admin'
netld_pass = 'password'
netld_network = 'Default'

def usageAndExit():
   print 'Usage: ' + sys.argv[0] + ' [OPTIONS] -o <output file>'
   print 'Export the hardware inventory to a CSV file.'
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
      outputFile = "HardwareReport" + strftime("%y%m%d-%H%M%S", localtime()) + ".csv"

   _netld_svc = JsonRpcProxy("https://{0}/rest".format(netld_host), netld_user, netld_pass)

   job = {
      'managedNetwork': netld_network,
      'jobName': 'Hardware Report',
      'jobType': 'Report',
      'description': '',
      'jobParameters': {
         'tool': 'ziptie.reports.hardware',
         'ipResolutionScheme': 'ipAddress',
         'ipResolutionData': '',
         'managedNetwork': netld_network,
         'format': 'csv'
      },
   }

   execution = _netld_svc.call('Scheduler.runNow', job)

   print "** executing job **"
   execution_id = execution['id']

   opener = urllib2.build_opener(_netld_svc._cookie_processor, _netld_svc._https_handler)
   while not execution['endTime']:
      if execution['completionState'] == 1 or execution['completionState'] == 2:
         print '** execution canceled **'
         break

      time.sleep(1)
      execution = _netld_svc.call('Scheduler.getExecutionDataById', execution_id)

   url = 'https://{0}/servlet/pluginDetail?executionId={1}'.format(netld_host, str(execution_id))
   response = opener.open(url)

   if response.headers.get('content-encoding', '') == 'deflate':
      resp = zlib.decompressobj(-zlib.MAX_WBITS).decompress(response.read())
   else:
      resp = response.read()

   file = open(outputFile, 'w')
   file.write(resp)
   file.close()

   print "** Hardware Report Export execution complete **"

   _netld_svc.call('Security.logoutCurrentUser')

if __name__ == "__main__":
   main(sys.argv[1:])
