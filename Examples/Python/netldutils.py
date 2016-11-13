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
      xml = """
         <?xml version="1.0" encoding="UTF-8"?>
         <templateXml>
            <text>{0}</text>
         """.format(base64.b64encode(template))

      replacements = {}
      for replacement in re.findall(r"\{.*?\}", template):
         replacements[replacement] = True

      for key in replacements.keys():
         replacement = re.match(r"\{(.*?)\}", key)
         xml += """
            <replacement name="{0}" type="string" group="" originalIsDefault="false">
               <original></original>
               <values></values>
               <replace>{1}</replace>
            </replacement>
            """.format(replacement.group(1), base64.b64encode(replacement.group(0)))

      xml += "</templateXml>"

      # Delete job
      # Scheduler.saveJob
      job_data = {
         'managedNetworks': networks,
         'jobName': name,
         'jobType': 'Bulk Update',
         'description': '',
         'jobParameters': {
            'backupOnCompletion': 'false',
            'ipResolutionScheme': 'ipCsv',
            'ipResolutionData': '',
            'templateXml': xml,
            'replacementMode': 'perdevice'
         }
      }

      job_data = self._netld_svc.call('Scheduler.saveJob', job_data)

      return job_data

   def execute_smart_change(jobData, replacementMode, replacements):
      jobData['jobParameters']['replacementMode'] = replacementMode
      jobData['jobParameters']['replacements'] = replacements
      return 0
