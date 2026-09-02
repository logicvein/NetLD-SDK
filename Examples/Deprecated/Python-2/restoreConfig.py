#!/usr/bin/env python

import os
import re
import sys
import time
import getopt
import zlib
from datetime import datetime, timedelta, tzinfo
from jsonrpc import JsonRpcProxy, JsonError

netld_host = 'localhost'
netld_user = 'admin'
netld_pass = 'password'
netld_network = 'Default'

output_dir = './netld-output'
output_onefile = True
output_file = re.sub('\.py', '', sys.argv[0])

# Edit the job_name variable to display a different name in netLD job history
#
job_name = "Restore configuration";

#
# ----------------------- NO MORE EDITS NEEDED BELOW THIS LINE ------------------------
#

def main(argv):
   try:
      opts, args = getopt.getopt(argv, "h:u:p:m:w:c:t:", ['host=','user=','password=','managed-network=','--no-wait','config=','timestamp='])
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
      if opt in ('-c', '--config'):
         configPath = arg
      if opt in ('-t', '--timestamp'):
         timestamp = arg

   if (len(args) > 0):
      device = args[0]
   else:
      _usage_and_exit()

   ### Create a JSON-RPC proxy for the inventory service
   ###
   global _netld_svc
   _netld_svc = JsonRpcProxy("https://{0}/jsonrpc".format(netld_host), netld_user, netld_pass)

   pageData = _netld_svc.call('Configuration.retrieveSnapshotChangeLog', 'Default', device, {'offset': 0, 'pageSize': 1000})
   for changeLog in pageData['changeLogs']:
      snapShot = datetime.fromtimestamp(changeLog['timestamp'] / 1000)
      if (snapShot.strftime('%Y-%m-%d %H:%M:%S') > timestamp):
         targetTime = datetime.utcfromtimestamp(changeLog['timestamp'] / 1000)
         localTargetTime = snapShot
      else:
         print "Restoring configuration from snapshot: " + str(localTargetTime)
         break

   job_data = {
      'managedNetwork': netld_network,
      'jobName': job_name,
      'jobType': 'Restore Configuration',
      'description': '',
      'jobParameters': {
         'managedNetwork': netld_network,
         'ipResolutionScheme': _resolution_scheme(device),
         'ipResolutionData': device,
         'configPath': configPath,
         'configTimestamp': targetTime.strftime('%Y-%m-%dT%H:%M:%S')
      }
   }

   try:
      execution = _netld_svc.call('Scheduler.runNow', job_data)
   except JsonError as ex:
      print 'JsonError: ' + str(ex.value)

   try:
      if (no_wait is None):
         result = _wait_for_completion(execution)

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
   print '  -c --config  Path of the configuration, eg. "/startup-config"'
   print '  -t --timestamp  Timestamp equal or less than the desired snapshot version'
   print "                  with format 'yyyy-mm-ddThh:mm:ss' (GMT): 2014-10-24T21:45:00"
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


def _scriptname():
   return re.sub('.py', '', sys.argv[0])


if __name__ == "__main__":
    main(sys.argv[1:])
