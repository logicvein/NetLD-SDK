#!/usr/bin/env python

import re
import sys
import time
import getopt
from jsonrpc import JsonRpcProxy, JsonError

snmp_ro = 'public'
netld_user = 'admin'
netld_pass = 'password'
netld_host = 'localhost'
netld_network = 'Default'

def usage_and_exit():
   print 'Usage: discovery.py [OPTIONS] <ip address|@filename>'
   print 'Discovery one or more devices.'
   print
   print '  -h host --host=host  Hostname or IP address of Net LineDancer server'
   print '  -u username --user=username  Net LineDancer username'
   print '  -p password --password=password  Net LineDancer password'
   print '  -s --snmp-ro=password  SNMP Read-only password'
   print '  -m --managed-network=network  The name of a Net LineDancer network'
   print '  -w --no-wait  Do not wait until discovery completes'
   print
   print '<ip address>  The IP address of the device to discover'
   print '@filename  The name of a file containing IP addresses, one per line'
   sys.exit(2)

_netld_svc = None

def main(argv):
   try:
      opts, args = getopt.getopt(argv, "h:u:p:s:m:w", ["host=","user=","password=","snmp-ro=",'--managed-network=','--no-wait'])
   except getopt.GetoptError:
      usage_and_exit()

   global netld_host, netld_user, netld_pass, snmp_ro, netld_network
   no_wait = None
   for opt, arg in opts:
      if opt in ('-h', '--host'):
         netld_host = arg
      if opt in ('-u', '--user'):
         netld_user = arg
      if opt in ('-p', '--password'):
         netld_pass = arg
      if opt in ('-s', '--snmp-ro'):
         snmp_ro = arg
      if opt in ('-m', '--managed-network'):
         netld_network = arg
      if opt in ('-w', '--no-wait'):
         no_wait = True

   if (len(args) < 1):
      usage_and_exit()

   ip_host_file = _resolve_ipaddrs(args[0])

   ### Create a JSON-RPC proxy for the inventory service
   ###
   global _netld_svc
   _netld_svc = JsonRpcProxy("https://{0}/jsonrpc".format(netld_host), netld_user, netld_pass)

   job_data = {
      'managedNetwork': netld_network,
      'jobName': 'Discovery',
      'jobType': 'Discover Devices',
      'description': '',
      'jobParameters': {
         'addresses': ip_host_file,
         'managedNetwork': netld_network,
         'crawl': 'false',
         'boundaryNetworks': '10.0.0.0/8,192.168.0.0/16,172.16.0.0/12',
         'includeInventory': 'false',
         'communityStrings': snmp_ro
      }
   }

   try:
      execution = _netld_svc.call('Scheduler.runNow', job_data)
   except JsonError as ex:
      print 'JsonError: ' + str(ex.value)

   try:
      if (no_wait is None):
         result = _wait_for_completion(execution)

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


def _resolve_ipaddrs(shape):
   if (shape.startswith('@')):
      # Filename with IP addresses, one per-line
      with open (shape.lstrip('@'), "r") as myfile:
         return myfile.read().replace('\n', ',').rstrip(',')
   else:
      # IP address
      return shape;


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
    main(sys.argv[1:])
