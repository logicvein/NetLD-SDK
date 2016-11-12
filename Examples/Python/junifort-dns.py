#!/usr/bin/env python

import os
import re
import sys
import time
import getopt
import ipaddress
import ConfigParser
from openpyxl import Workbook, load_workbook
from jsonrpc import JsonRpcProxy, JsonError
from netldutils import NetLdUtils

# Non-standard required modules: ipaddress, openpyxl

netld_user = 'admin'
netld_pass = 'password'
netld_host = 'localhost'
netld_network = []

juniper_read_template = """
get nsm | i server
get conf | i "host dns[1-3]"
"""

fortinet_read_template = """
show | grep 'set fmg'
Config global
Config system dns
Get
"""

def usage_and_exit(argv):
   print 'Usage: ' + sys.argv[0] + ' [OPTIONS]'
   print 'Execute a pre-existing job in Net LineDancer.'
   print
   print '  -x --excel=filename  The name of the Excel file to read/write'
   print '  -h host --host=host  Hostname or IP address of Net LineDancer server'
   print '  -u username --user=username  Net LineDancer username'
   print '  -p password --password=password  Net LineDancer password'
   print
   sys.exit(2)

netld_svc = None

def main(argv):
   try:
      opts, args = getopt.getopt(argv, "h:u:p:x:", ["host=","user=","password=","excel="])
   except getopt.GetoptError as err:
      print "Error: " + str(err)
      usage_and_exit(argv)

   global netld_host, netld_user, netld_pass, excel_file, netld_network
   excel_file = None

   if os.path.exists('junifort.ini'):
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

   if (excel_file is None):
      usage_and_exit(argv)

   try:
      global netld_svc
      netld_svc = JsonRpcProxy("https://{0}/rest".format(netld_host), netld_user, netld_pass)

      workbook = load_workbook(excel_file)
      cols = detect_excel_columns(workbook)

      devices = resolve_from_excel(workbook, cols['netColumn'], cols['startRow'])
      for device in devices.values():
         print device

   except JsonError as ex:
      print 'JsonError: ' + str(ex.value)
   finally:
       netld_svc.call('Security.logoutCurrentUser')


def detect_excel_columns(workbook):
   startRow = 1
   netColumn = None
   ws = workbook.active
   if (ws['A1'].value == 'IP Address'):
      startRow = 2
   else:
      try:
         ipaddress.ip_address(ws['A1'].value)
      except ValueError:
         raise ValueError('IP address column could not be identified.')

   for row in ws.iter_rows(min_row=1, max_row=1):
      for cell in row:
         if (cell.value == 'Network'):
            netColumn = cell.col_idx

   return {'netColumn': netColumn, 'startRow': startRow}


# The provided Excel had 'IP Address' and 'Network' columns, so read those
# from the sheet and generate an array of 'ipaddress@network' entries.
def resolve_from_excel(workbook, netColumn, startRow):
   ws = workbook.active
   devices = {}

   network = None
   for row in range(startRow, ws.max_row):
      ipAddress = ws.cell(row=row, column=1).value
      key = ipAddress
      if netColumn is not None:
         network = ws.cell(row=row, column=netColumn).value
         key = ipAddress + network
      devices[key] = {'ipAddress': ipAddress, 'network': network}

   networks = NetLdUtils(netld_svc).get_networks()
   pageData= {'offset': 0, 'pageSize': 500}
   while True:
      pageData = netld_svc.call('Inventory.search', networks, 'ipAddress', '', pageData, 'ipAddress', False)
      for device in pageData['devices']:
         ipAddress = device['ipAddress']
         network = device['network']
         vendor = device['hardwareVendor']
         if vendor != 'Juniper' and vendor != 'Fortinet':
            continue

         key = ipAddress + network
         candidate = devices.get(key)
         if candidate is None:
            candidate = devices.get(ipAddress)
            if candidate is None:
               continue
         if candidate['network'] is None:
            candidate['network'] = network
            candidate['resolved'] = True
         elif candidate['network'] != network or candidate.get('resolved'):
            continue
         candidate['vendor'] = vendor

      if pageData['offset'] + pageData['pageSize'] > pageData['total']:
         break;
      else:
         pageData['offset'] += pageData['pageSize']

   return devices

def export_to_excel(devices):
   networks = NetLdUtils(netld_svc).get_networks()
   for vendor in ('Juniper', 'Fortinet'):
      csv = ''
      for device in devices.values():
         if device['vendor'] == vendor:
            csv += device['ipAddress'] + '@' + device['network'] + ','

      csv = csv[:-1]

      job_data = {
         'managedNetwork': netld_network,
         'jobName': 'Export Juniper and Fortinet DNS/Manager to Excel',
         'jobType': 'Script Tool Job',
         'description': '',
         'jobParameters': {
            'tool': 'org.ziptie.tools.scripts.commandRunner',
            'managedNetwork': networks,
            'backupOnCompletion': 'false',
            'ipResolutionScheme': 'ipCsv',
            'ipResolutionData': csv,
            'input.commandList': juniper_read_template if vendor == 'Juniper' else fortinet_read_template
         }
      }

      try:
         execution = _netld_svc.call('Scheduler.runNow', job_data)
         NetLdUtils(netld_svc).wait_for_completion(execution)

         details = _netld_svc.call('Plugins.getExecutionDetails', execution['id'])

      except JsonError as ex:
         print 'JsonError: ' + str(ex.value)



if __name__ == "__main__":
   exit(main(sys.argv[1:]))
