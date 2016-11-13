#!/usr/bin/env python

# Non-default required modules: ipaddress, openpyxl
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

juniper_read_template = """
get nsm | i server
get conf | i "host dns[1-3]"
"""

juniper_nsm_regex = re.compile(r"(?:host: (\S+),)")
juniper_dns_regex = re.compile(r"(?:dns[1-3] (\S+))")

juniper_write_template = """
set dns host dns1 {DNS-X1}
set dns host dns2 {DNS-X2}
set dns host dns3 {DNS-X3}
set dns server-select domain * primary-server {DNS-X1} secondary-server {DNS-X2} tertiary-server {DNS-X3} failover
save
"""

fortinet_read_template = """
show | grep 'set fmg'
config global
config system dns
get
"""

fortinet_fmg_regex = re.compile(r"(?:fmg \"(\S+)\")")
fortinet_dns_regex = re.compile(r"(?:^(?:primary|secondary).*?: (\S+))", re.MULTILINE)

fortinet_write_template = """
config global
config system dns
set primary {DNS-X1}
set secondary {DNS-X2}
"""

netld_user = 'admin'
netld_pass = 'password'
netld_host = 'localhost'

def usage_and_exit(argv):
   print 'Usage: ' + sys.argv[0] + ' [OPTIONS]'
   print 'Execute a pre-existing job in Net LineDancer.'
   print
   print '  -f --excel=filename  The name of the Excel file to read/write'
   print '  -e --export Read the Excel file and export the DNS/Mgr settings'
   print '  -x --exec Read an Excel file and apply the DNS/Mgr settings'
   print '  -h host --host=host  Hostname or IP address of Net LineDancer server'
   print '  -u username --user=username  Net LineDancer username'
   print '  -p password --password=password  Net LineDancer password'
   print
   sys.exit(2)

netld_svc = None

def main(argv):
   try:
      opts, args = getopt.getopt(argv, "h:u:p:f:e:x:", ["host=","user=","password=","excel=","export","exec"])
   except getopt.GetoptError as err:
      print "Error: " + str(err)
      usage_and_exit(argv)

   global netld_host, netld_user, netld_pass, excel_file
   excel_file = None
   export_action = False
   exec_action = False

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
      if opt in ('-f', '--excel'):
         excel_file = arg
      if opt in ('-e', '--export'):
         export_action = True
      if opt in ('-x', '--exec'):
         exec_action = True

   if excel_file is None or (not export_action and not exec_action):
      usage_and_exit(argv)

   try:
      global netld_svc
      netld_svc = JsonRpcProxy.fromHost(netld_host, netld_user, netld_pass)

      workbook = load_workbook(excel_file)
      cols = detect_excel_columns(workbook)

      devices = resolve_from_excel(workbook, cols['networkColumn'], cols['startRow'])

      if export_action:
         print NetLdUtils(netld_svc).create_smart_change('apply the DNS/Mgr settings', juniper_write_template, ['Default'])
         export_to_excel(devices)
      else:
         exec_from_excel(devices)

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

   return {'networkColumn': netColumn, 'startRow': startRow}


# The provided Excel had 'IP Address' and 'Network' columns, so read those
# from the sheet and generate an array of 'ipaddress@network' entries.
def resolve_from_excel(workbook, networkColumn, startRow):
   ws = workbook.active
   devices = {}

   network = None
   for row in range(startRow, ws.max_row):
      ipAddress = ws.cell(row=row, column=1).value
      key = ipAddress
      if networkColumn is not None:
         network = ws.cell(row=row, column=networkColumn).value
         key = ipAddress + network
      devices[key] = {'ipAddress': ipAddress, 'network': network}

   networks = NetLdUtils(netld_svc).get_networks()
   pageData= {'offset': 0, 'pageSize': 1000}
   while True:
      pageData = netld_svc.call('Inventory.search', networks, 'ipAddress', '', pageData, 'ipAddress', False)
      for invDevice in pageData['devices']:
         ipAddress = invDevice['ipAddress']
         network = invDevice['network']
         adapter = invDevice['adapterId']
         if adapter != 'Juniper::ScreenOS' and adapter != 'Fortinet::FortiGate':
            continue

         key = ipAddress + network
         device = devices.get(key)
         if device is None:
            device = devices.get(ipAddress)
            if device is None:
               continue
         if device['network'] is None:
            device['network'] = network
         elif device['network'] != network or device.get('resolved'):
            continue
         device['adapter'] = adapter
         device['resolved'] = True

      if pageData['offset'] + pageData['pageSize'] > pageData['total']:
         break;
      else:
         pageData['offset'] += pageData['pageSize']

   for key, device in devices.items():
      if not 'resolved' in device:
         del devices[key]

   return devices

def export_to_excel(devices):
   global exportWorksheet
   exportWb = Workbook()
   exportWorksheet = exportWb.active
   exportWorksheet.append(['IP Address', 'Network', 'MGR', 'DNS1', 'DNS2', 'DNS3'])

   for adapter in ['Juniper::ScreenOS', 'Fortinet::FortiGate']:
      csv = ''
      for device in devices.values():
         if device['adapter'] == adapter:
            csv += device['ipAddress'] + '@' + device['network'] + ','
      csv = csv[:-1]

      job_data = {
         'managedNetworks': NetLdUtils(netld_svc).get_networks(),
         'jobName': 'Export ' + adapter + ' DNS/Manager to Excel',
         'jobType': 'Script Tool Job',
         'description': '',
         'jobParameters': {
            'tool': 'org.ziptie.tools.scripts.commandRunner',
            'backupOnCompletion': 'false',
            'ipResolutionScheme': 'ipCsv',
            'ipResolutionData': csv,
            'input.commandList': juniper_read_template if adapter == 'Juniper::ScreenOS' else fortinet_read_template
         }
      }

      try:
         execution = netld_svc.call('Scheduler.runNow', job_data)

         utils = NetLdUtils(netld_svc)
         utils.wait_job_completion(execution)
         utils.get_tool_details(execution, print_detail)

      except JsonError as ex:
         print 'JsonError: ' + str(ex.value)

   exportWb.save('export.xlsx')


def print_detail(ipAddress, network, response):
   if 'set dns' in response:
      result = juniper_nsm_regex.search(response)
      mgr = result.group(1) if result else ''
      dns = juniper_dns_regex.findall(response)
   elif 'dns-cache-limit' in response:
      result = fortinet_fmg_regex.search(response)
      mgr = result.group(1) if result else ''
      dns = fortinet_dns_regex.findall(response)
   else:
      print 'Unexpected response from ' + ipAddress + ' in network ' + network
      return

   exportWorksheet.append([
      ipAddress,
      network,
      mgr if mgr else '',
      dns[0] if len(dns) > 0 else '',
      dns[1] if len(dns) > 1 else '',
      dns[2] if len(dns) > 2 else ''
      ])

def export_to_excel(devices):
   for adapter in ['Juniper::ScreenOS', 'Fortinet::FortiGate']:
      for row in range(startRow, ws.max_row):
         ipAddress = ws.cell(row=row, column=1).value

      csv = ''
      for device in devices.values():
         if device['adapter'] == adapter:
            csv += device['ipAddress'] + '@' + device['network'] + ','
      csv = csv[:-1]

      job_data = {
         'managedNetworks': NetLdUtils(netld_svc).get_networks(),
         'jobName': 'Apply ' + adapter + ' DNS/Manager settings from Excel',
         'jobType': 'Script Tool Job',
         'description': '',
         'jobParameters': {
            'tool': 'org.ziptie.tools.scripts.commandRunner',
            'backupOnCompletion': 'false',
            'ipResolutionScheme': 'ipCsv',
            'ipResolutionData': csv,
            'input.commandList': (
                  juniper_write_template if adapter == 'Juniper::ScreenOS' else fortinet_write_template
               ).format(**{'DNS-X1': '', 'DNS-X2': '', 'DNS-X3': ''})
         }
      }

   return 0

if __name__ == "__main__":
   exit(main(sys.argv[1:]))
