#!/usr/bin/env python

import re
import sys
import time
import getopt
import ConfigParser
from jsonrpc import JsonRpcProxy, JsonError
from openpyxl import Workbook

netld_user = 'admin'
netld_pass = 'password'
netld_host = 'localhost'
netld_network = []

def usage_and_exit(argv):
   print 'Usage: ' + argv[0] + ' [OPTIONS]'
   print 'Execute a pre-existing job in Net LineDancer.'
   print
   print '  -h host --host=host  Hostname or IP address of Net LineDancer server'
   print '  -u username --user=username  Net LineDancer username'
   print '  -p password --password=password  Net LineDancer password'
   print '  -x --excel=filename  The name of the Excel file to read/write'
   print '  -m --managed-network=network  The name of a Net LineDancer network'
   print
   sys.exit(2)

_netld_svc = None

def main(argv):
   try:
      opts, args = getopt.getopt(argv, "h:u:p:x:m:"),  ["host=","user=","password=","excel=",'--managed-network='])
   except getopt.GetoptError as err:
      print "Error: " + str(err)
      usage_and_exit()

   global netld_host, netld_user, netld_pass, excel_file, netld_network
   excel_file = None

   if os.path.exists(configFile):
      config = ConfigParser.RawConfigParser()
      config.read('junifort.ini')
      for section in config.sections():
         netld_host = config.get(section, 'host')
         netld_user = config.get(section, 'username')
         netld_pass = config.get(section, 'password')

   for opt, arg in opts:
      if opt in ('-h', '--host'):
         netld_host = arg
      if opt in ('-u', '--user'):
         netld_user = arg
      if opt in ('-p', '--password'):
         netld_pass = arg
      if opt in ('-x', '--excel'):
         excel_file = arg
      if opt in ('-m', '--managed-network'):
         netld_network = (arg)

   if (job_name is None):
      usage_and_exit(argv)


if __name__ == "__main__":
   exit(main(sys.argv[1:]))
