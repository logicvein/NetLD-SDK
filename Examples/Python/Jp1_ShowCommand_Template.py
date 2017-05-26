#!/usr/bin/env python

import os
import re
import sys
import time
import zlib
import getopt
from jsonrpc import JsonRpcProxy, JsonError

# Commands to be executed should be added/removed between the line
# """ markers.
#
commands = """

show version

"""

netld_host = 'localhost'
netld_user = 'admin'
netld_pass = 'password'
netld_network = 'Default'

output_dir = './netld-output'
output_onefile = True
output_file = re.sub('\.py', '', sys.argv[0])

# Edit the job_name variable to display a different name in netLD job history
#
job_name = "Show version";

#
# ----------------------- NO MORE EDITS NEEDED BELOW THIS LINE ------------------------
#

def main(argv):
   try:
      opts, args = getopt.getopt(argv, "h:u:p:m:w", ["host=","user=","password=",'--managed-network=','--no-wait'])
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
      if opt in ('-w', '--no-wait'):
         no_wait = True

   if (len(args) > 0):
      device = args[0]
   else:
      _usage_and_exit()

   ### Create a JSON-RPC proxy for the inventory service
   ###
   global _netld_svc
   _netld_svc = JsonRpcProxy("https://{0}/jsonrpc".format(netld_host), netld_user, netld_pass)

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
      if (no_wait is None):
         result = _wait_for_completion(execution)

         _save_job_ouptut(execution, device)
   except JsonError as ex:
      print 'JsonError: ' + str(ex.value)
   finally:
      ### Logout using the security service to be nice to the server
      ###
      _netld_svc.call('Security.logoutCurrentUser')


def _usage_and_exit():
   print 'Usage: ' + sys.argv[0] + ' [OPTIONS] <device>'
   print 'Discovery one or more devices.'
   print
   print '  -h host --host=host  Hostname or IP address of Net LineDancer server'
   print '  -u username --user=username  Net LineDancer username'
   print '  -p password --password=password  Net LineDancer password'
   print '  -m --managed-network=network  The name of a Net LineDancer network'
   print '  -w --no-wait  Do not wait until the job completes'
   print
   print '<device>  The IP address or hostname of the device'
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


def _save_job_ouptut(execution, device):
   execution_id = execution['id']

   try:
      details = _netld_svc.call('Plugins.getExecutionDetails', execution_id)
   except JsonError as ex:
      print 'JsonError: ' + str(ex.value)
      sys.exit(-1)

   if (details):
      opener = urllib2.build_opener(_netld_svc._cookie_processor, _netld_svc._https_handler)

      for detail in details:
         filename = (output_file if output_onefile else device) + '.log'

         try:
            url = 'https://{0}/servlet/pluginDetail?executionId={1}&recordId={2}'.format(netld_host, execution_id, detail['id'])
            resp = opener.open(url)
            respdata = str(zlib.decompress(resp.read(), -zlib.MAX_WBITS))

            directory = output_dir if output_onefile else '{0}/{1}'.format(output_dir, output_file)
            if (not os.path.exists(directory)):
               os.makedirs(directory)

            with open('{0}/{1}'.format(directory, filename), 'a') as f:
               for line in respdata.split('\n'):
                  line = re.sub('[\r\n]+', '', line)
                  f.write("[{0}] [{1}]: {2}\n".format(time.strftime('%Y/%m/%d %H:%M:%S', time.localtime(detail['startTime'] / 1000)), device, line))

         except urllib2.URLError as ex:
            print 'Connection error: ' + str(ex)
            sys.exit(-1)


def _scriptname():
   return re.sub('.py', '', sys.argv[0])


if __name__ == "__main__":
    main(sys.argv[1:])
