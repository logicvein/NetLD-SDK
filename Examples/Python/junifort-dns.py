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
from netldexcel import NetLdExcel

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

      devices = NetLdExcel(netld_svc).resolve_from_excel(
         excelFile=excel_file,
         adapters=['Juniper::ScreenOS', 'Fortinet::FortiGate']
      )

      if export_action:
         export_to_excel(devices)
      else:
         exec_from_excel(devices, excel_file)

   except JsonError as ex:
      print 'JsonError: ' + str(ex.value)
   finally:
       netld_svc.call('Security.logoutCurrentUser')

def export_to_excel(devices):
   global exportWorksheet
   exportWb = Workbook()
   exportWorksheet = exportWb.active
   exportWorksheet.append(['IP Address', 'Network', 'MGR', 'DNS1', 'DNS2', 'DNS3'])

   utils = NetLdUtils(netld_svc)

   executions = []
   for adapterId in ['Juniper::ScreenOS', 'Fortinet::FortiGate']:
      csv = ''
      for device in devices.values():
         if device['adapterId'] == adapterId:
            csv += device['ipAddress'] + '@' + device['network'] + ','
      csv = csv[:-1]

      job_data = {
         'jobType': 'Script Tool Job',
         'jobName': 'Export ' + adapterId + ' DNS/Manager to Excel',
         'managedNetworks': utils.get_networks(),
         'description': '',
         'jobParameters': {
            'tool': 'org.ziptie.tools.scripts.commandRunner',
            'input.commandList': juniper_read_template if adapterId == 'Juniper::ScreenOS' else fortinet_read_template,
            'backupOnCompletion': 'false',
            'ipResolutionScheme': 'ipCsv',
            'ipResolutionData': csv,
         }
      }

      if len(csv) == 0:
         continue

      try:
         executions.append( netld_svc.call('Scheduler.runNow', job_data) )
      except JsonError as ex:
         print 'JsonError: ' + str(ex.value)

   try:
      for execution in executions:
         utils.wait_job_completion(execution)

      for execution in executions:
         utils.get_tool_details(execution, append_excel_row)
   except JsonError as ex:
      print 'JsonError: ' + str(ex.value)

   exportWb.save('export.xlsx')


def append_excel_row(ipAddress, network, response):
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
      dns[2] if len(dns) > 2 else '']
   )

def exec_from_excel(devices, excelFile):
   workbook = load_workbook(excelFile)
   ws = workbook.active

   utils = NetLdUtils(netld_svc)

   executions = []
   for adapterId in ['Juniper::ScreenOS', 'Fortinet::FortiGate']:
      # Filter devices by adapterId
      job_devices = {key: device for (key, device) in devices.items() if device['adapterId'] == adapterId}

      # Unique list of networks from the set of job_devices
      networks = {device['network']: True for (key, device) in job_devices.items()}.keys()

      replacements = []
      for row in range(2, ws.max_row + 1):
         ipAddress = ws.cell(row=row, column=1).value
         network   = ws.cell(row=row, column=2).value
         unused    = ws.cell(row=row, column=3).value
         dns1      = ws.cell(row=row, column=4).value
         dns2      = ws.cell(row=row, column=5).value
         dns3      = ws.cell(row=row, column=6).value
         print "DNS1 {0}, DNS2 {1}, DNS3 {2}".format(dns1, dns2, dns3)
         key = ipAddress + network
         device = devices[key]
         replacements.append({
            'ipAddress': ipAddress,
            'network': network,
            'DNS-X1': dns1 if dns1 else '',
            'DNS-X2': dns2 if dns2 else '',
            'DNS-X3': dns3 if dns3 else '',
         })

      job_data = utils.create_smart_change(
         name     = adapterId + ' apply the DNS/Mgr settings',
         template = juniper_write_template if adapterId == 'Juniper::ScreenOS' else fortinet_write_template,
         networks = networks
      )

      try:
         executions.append(
            utils.execute_smart_change(job_data, job_devices, 'perdevice', replacements)
         )
      except JsonError as ex:
         print 'JsonError: ' + str(ex.value)

   try:
      for execution in executions:
         utils.wait_job_completion(execution)

      for execution in executions:
         utils.get_tool_details(execution, append_excel_row)
   except JsonError as ex:
      print 'JsonError: ' + str(ex.value)


if __name__ == "__main__":
   exit(main(sys.argv[1:]))
