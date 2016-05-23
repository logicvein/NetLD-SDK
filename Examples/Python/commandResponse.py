#!/usr/bin/env python

import os
import re
import sys
import time
import urllib
import urllib2
import zlib
import getopt
from jsonrpc import JsonRpcProxy, JsonError

netld_host = '192.168.20.10'
netld_user = 'admin'
netld_pass = 'password'
netld_network = 'Default'

# Edit the job_name variable to display a different name in netLD job history
#
job_name = "Show version";

#
# ----------------------- NO MORE EDITS BELOW THIS LINE ------------------------
#

def main(argv):
   try:
      opts, args = getopt.getopt(argv, "h:u:p:m:", ["host=","user=","password=",'--managed-network='])
   except getopt.GetoptError:
      _usage_and_exit()

   global netld_host, netld_user, netld_pass, netld_network

   no_wait = None
   for opt, arg in opts:
      if opt in ('-h', '--host'):
         netld_host = arg
      if opt in ('-u', '--user'):
         netld_user = arg
      if opt in ('-p', '--password'):
         netld_pass = arg
      if opt in ('-m', '--managed-network'):
         netld_network = arg

   if (len(args) > 0):
      device = args[0]
      commands = args[1]
   else:
      _usage_and_exit()

   ### Create a JSON-RPC proxy for the inventory service
   ###
   global _netld_svc
   _netld_svc = JsonRpcProxy("https://{0}/rest".format(netld_host), netld_user, netld_pass)

   job_data = {
      'managedNetwork': netld_network,
      'jobName': job_name,
      'jobType': 'Script Tool Job',
      'description': '',
      'jobParameters': {
         'tool': 'org.ziptie.tools.scripts.commandRunner',
         'managedNetwork': netld_network,
         'backupOnCompletion': 'false',
         'ipResolutionScheme': _resolution_scheme(device),
         'ipResolutionData': device,
         'input.commandList': commands
      }
   }

   try:
      execution = _netld_svc.call('Scheduler.runNow', job_data)
   except JsonError as ex:
      print 'JsonError: ' + str(ex.value)

   try:
      result = _wait_for_completion(execution)

      _print_job_ouptut(execution, device)
   except JsonError as ex:
      print 'JsonError: ' + str(ex.value)
   finally:
      ### Logout using the security service to be nice to the server
      ###
      _netld_svc.call('Security.logoutCurrentUser')


def _usage_and_exit():
   print 'Usage: ' + sys.argv[0] + ' [OPTIONS] <device> <command>'
   print 'Run a command for one device and display the result.'
   print
   print '  -h host --host=host  Hostname or IP address of Net LineDancer server'
   print '  -u username --user=username  Net LineDancer username'
   print '  -p password --password=password  Net LineDancer password'
   print '  -m --managed-network=network  The name of a Net LineDancer network'
   print
   print '<device>   The IP address or hostname of the device'
   print '<command>  The command to execute'
   sys.exit(2)

_netld_svc = None

def _wait_for_completion(execution):
   execution_id = execution['id']

   # wait for completion
   while (execution['endTime'] is None):
      state = execution['completionState']
      if (state == 1 or state == 2):
         print "FAILED $state"

      # wait one second so that we don't spam the server
      time.sleep(1)

      execution = _netld_svc.call('Scheduler.getExecutionDataById', execution_id)

   return execution


def _resolution_scheme(shape):
   return 'hostname' if (re.match('[a-zA-Z]{3}', shape) or re.match('\.', shape) != None) else 'interfaceIpAddress'


def _print_job_ouptut(execution, device):
   execution_id = execution['id']

   try:
      details = _netld_svc.call('Plugins.getExecutionDetails', execution_id)
   except JsonError as ex:
      print 'JsonError: ' + str(ex.value)
      sys.exit(-1)

   if (details):
      opener = urllib2.build_opener(_netld_svc._cookie_processor, _netld_svc._https_handler)

      for detail in details:
         try:
            url = 'https://{0}/servlet/pluginDetail?executionId={1}&recordId={2}'.format(netld_host, execution_id, detail['id'])
            resp = opener.open(url)
            respdata = str(zlib.decompress(resp.read(), -zlib.MAX_WBITS))
            print respdata

#            with open('{0}/{1}'.format(directory, filename), 'a') as f:
#               for line in respdata.split('\n'):
#                  line = re.sub('[\r\n]+', '', line)
#                  f.write("[{0}] [{1}]: {2}\n".format(time.strftime('%Y/%m/%d %H:%M:%S', time.localtime(detail['startTime'] / 1000)), device, line))

         except urllib2.URLError as ex:
            print 'Connection error: ' + str(ex)
            sys.exit(-1)

if __name__ == "__main__":
    main(sys.argv[1:])
