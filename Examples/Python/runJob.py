#!/usr/bin/env python

import re
import sys
import time
import getopt
from jsonrpc import JsonRpcProxy, JsonError

netld_user = 'admin'
netld_pass = 'password'
netld_host = 'localhost'
netld_network = []

def usage_and_exit():
   print 'Usage: runjob.py [OPTIONS]'
   print 'Execute a pre-existing job in Net LineDancer.'
   print
   print '  -h host --host=host  Hostname or IP address of Net LineDancer server'
   print '  -u username --user=username  Net LineDancer username'
   print '  -p password --password=password  Net LineDancer password'
   print '  -j --job=jobname  The name of the job to execute'
   print '  -m --managed-network=network  The name of a Net LineDancer network'
   print '  -w --no-wait  Do not wait until the job completes'
   print
   sys.exit(2)

_netld_svc = None

def main(argv):
   try:
      opts, args = getopt.getopt(argv, "h:u:p:j:m:w"),  ["host=","user=","password=","job=",'--managed-network=','--no-wait'])
   except getopt.GetoptError as err:
      print "Error: " + str(err)
      usage_and_exit()

   global netld_host, netld_user, netld_pass, job_name, netld_network
   no_wait = None
   job_name = None

   for opt, arg in opts:
      if opt in ('-h', '--host'):
         netld_host = arg
      if opt in ('-u', '--user'):
         netld_user = arg
      if opt in ('-p', '--password'):
         netld_pass = arg
      if opt in ('-j', '--job'):
         job_name = arg
      if opt in ('-m', '--managed-network'):
         netld_network = (arg)
      if opt in ('-w', '--no-wait'):
         no_wait = True

   if (job_name is None):
      usage_and_exit()

   ### Create a JSON-RPC proxy
   ###
   global _netld_svc
   _netld_svc = JsonRpcProxy("https://{0}/rest".format(netld_host), netld_user, netld_pass)

   pageData = {'offset': 0, 'pageSize': 1000}
   try:
      pageData = _netld_svc.call('Scheduler.searchJobs', pageData, [netld_network], None, True)
   except JsonError as ex:
      print 'JsonError: ' + str(ex.value)

   jobId = -1
   for job in pageData['jobData']:
      if (job['jobName'] == job_name):
         jobId = job['jobId'];
         break

   if (jobId == -1):
      print "No matching job found."
      exit(1)

   try:
      jobData = _netld_svc.call('Scheduler.getJob', jobId)
      if (jobData):
         execution = _netld_svc.call('Scheduler.runNow', jobData)
      else:
         print "Unexpected error, job with ID " + str(jobId) + " could not be retreived"
         exit(1)
   except JsonError as ex:
      print 'JsonError: ' + str(ex.value)
      exit(1)

   exit_code = 0;
   try:
      if (no_wait is None):
         result = _wait_for_completion(execution)
         exit_code = 0 if result['status'] == 'OK' else 1

         print 'Job status: ' + result['status']
         print 'Start time: ' + time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime(result['startTime'] / 1000))
         print 'End time  : ' + time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime(result['endTime'] / 1000))
         print
   except JsonError as ex:
      print 'JsonError: ' + str(ex.value)
   finally:
      ### Logout using the security service to be nice to the server
      ###
      _netld_svc.call('Security.logoutCurrentUser')

   return exit_code

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

if __name__ == "__main__":
   exit(main(sys.argv[1:]))
