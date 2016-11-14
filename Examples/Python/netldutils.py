import re
import time
import zlib
import base64
import urllib2
from jsonrpc import JsonRpcProxy, JsonError

class NetLdUtils:
   '''A utility class with miscellaneous functions'''

   def __init__(self, netldService):
      self._netld_svc = netldService

   def get_networks(self):
      return self._netld_svc.call('Networks.getManagedNetworkNames')

   def wait_job_completion(self, execution):
      execution_id = execution['id']

      # wait for completion
      while (execution['endTime'] is None):
         state = execution['completionState']
         if (state == 1 or state == 2):
            print "FAILED $state"

         # wait one second so that we don't spam the server
         time.sleep(1)

         execution = self._netld_svc.call('Scheduler.getExecutionDataById', execution_id)

      return execution

   def get_tool_details(self, execution, callback):
      execution_id = execution['id']

      try:
         details = self._netld_svc.call('Plugins.getExecutionDetails', execution_id)
      except JsonError as ex:
         print 'JsonError: ' + str(ex.value)
         sys.exit(-1)

      if details is None:
         return None

      opener = urllib2.build_opener(self._netld_svc._cookie_processor, self._netld_svc._https_handler)

      for detail in details:
         try:
            url = 'https://{0}/servlet/pluginDetail?executionId={1}&recordId={2}'.format(self._netld_svc._host, execution_id, detail['id'])
            resp = opener.open(url)
            respdata = str(zlib.decompress(resp.read(), -zlib.MAX_WBITS))

            callback(detail['ipAddress'], detail['managedNetwork'], respdata)
         except urllib2.URLError as ex:
            raise StandardError('Unable to get details for execution with id=' + execution_id + ' and detail id=' + detail['id'])

      return None

   def create_smart_change(self, name, template, networks):
      xml = r"""
         <templateXml>
            <text>{0}</text>
         """.format(base64.b64encode(template))

      replacements = {}
      for replacement in re.findall(r"\{.*?\}", template):
         replacements[replacement] = True

      for key in replacements.keys():
         replacement = re.match(r"\{(.*?)\}", key)
         xml += r"""
            <replacement name="{0}" type="string" group="" originalIsDefault="false">
               <original></original>
               <values></values>
               <replace>{1}</replace>
            </replacement>
            """.format(replacement.group(1), base64.b64encode(replacement.group(0)))

      xml += r'</templateXml>'

      # Delete job
      # Scheduler.saveJob
      job_data = {
         'managedNetworks': networks,
         'jobName': name,
         'jobType': 'Bulk Update',
         'description': '',
         'jobParameters': {
            'backupOnCompletion': 'false',
            'ipResolutionScheme': 'managedNetwork',
            'ipResolutionData': '',
            'templateXml': xml,
            'replacementMode': 'perdevice'
         }
      }

      job_data = self._netld_svc.call('Scheduler.saveJob', job_data)

      return job_data

   def execute_smart_change(self, jobData, devices, replacementMode, replacements):
      r'''A method to execute a Smart Change with the specified replacementMode
          and replacement values.

          The replacementMode parameter is either 'perjob' or 'perdevice'.

          If the replacementMode is 'perjob' then the expected type of the
          replacements parameter is dictionary:

            {'Name_1': 'Value_1', 'Name_2': 'Value_2', ...}

          where 'Name_1', 'Name_2', etc. are names of replacements that are
          defined in the Smart Change template.

          If the replacementMode is 'perdevice' then the expected type of the
          replacements parameter is a "list of dictionaries", with each
          dictionary instance also defining 'ipAddress' and 'network' entries:

            (
             {'ipAddress': '10.0.0.1', 'network': 'Tokyo', 'Name_1': 'Value_1', ...},
             {'ipAddress': '10.0.0.1', 'network': 'Tokyo', 'Name_2': 'Value_2', ...},
             {'ipAddress': '10.0.2.6', 'network': 'Tokyo', 'Name_1': 'Value_1', ...},
             {'ipAddress': '10.0.2.6', 'network': 'Tokyo', 'Name_2': 'Value_2', ...},
            )

          This method returns an ExecutionData object.
      '''

      jobData['jobParameters']['replacementMode'] = replacementMode

      csv = ','.join( [device['ipAddress'] + '@' + device['network'] for device in devices.values()] )
      jobData['jobParameters']['ipResolutionData'] = csv
      jobData['jobParameters']['ipResolutionScheme'] = 'ipCsv'

      xml = '<configs>'
      if replacementMode == 'perjob':
         xml += '<config>'
         for key, value in replacements:
            xml += r"""<replacement name='{0}'>{1}</replacement>""".format(key, base64.b64encode(value))
         xml += '</config>'
      else:
         for replacement in replacements:
            xml += r"""<config device='{0}@{1}'>""".format(replacement['ipAddress'], replacement['network'])
            for key, value in replacement.items():
               if key == 'ipAddress' or key == 'network':
                  continue
               xml += r"""<replacement name='{0}'>{1}</replacement>""".format(key, base64.b64encode(value))
            xml += r"""</config>"""
      xml += '</configs>'

      jobData['jobParameters']['replacements'] = xml

      print jobData
      return self._netld_svc.call('Scheduler.runNow', jobData)
