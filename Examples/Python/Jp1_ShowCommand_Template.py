#!/usr/bin/env python

import os
import re
import sys
import zlib
import getopt

# Commands to be executed should be added/removed between the line
# """ markers.
#
commands = """

show version

"""

netld_host = '192.168.20.10'
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
# ----------------------- NO MORE EDITS BELOW THIS LINE ------------------------
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
   _netld_svc = JsonRpcProxy("https://{0}/rest".format(netld_host), netld_user, netld_pass)

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

### ---------------------------------------------------------------------------
### You can copy the code below into any python script that needs to interact
### with the Net LineDancer JSON-RPC 2.0 API

import ssl
import json
import time
import random
import urllib
import urllib2
import cookielib
import functools
from hashlib import sha1

class JsonRpcProxy(object):
   '''A class implementing a JSON-RPC Proxy.'''

   def __init__(self, url, username, password):
      self._url = url
      self._username = username
      self._password = password

      ctx = ssl.create_default_context()
      ctx.check_hostname = False
      ctx.verify_mode = ssl.CERT_NONE
      self._https_handler = urllib2.HTTPSHandler(context=ctx)
      self._cookie_processor = urllib2.HTTPCookieProcessor(cookielib.CookieJar())

      self._hasher = sha1()
      self._id = 0
      self._opener = urllib2.build_opener(self._cookie_processor, self._https_handler)
      self._opener.add_handler(JsonRpcProcessor())

   def _next_id(self):
      self._id += 1
      self._hasher.update(str(self._id))
      self._hasher.update(time.ctime())
      self._hasher.update(str(random.random))
      return self._hasher.hexdigest()

   def call(self, method, *args, **kwargs):
      '''call a JSON-RPC method'''

      url = self._url
      if (self._id == 0):
         url = url + '?' + urllib.urlencode([('j_username', self._username), ('j_password', self._password)])

      postdata = {
        'jsonrpc': '2.0',
        'method': method,
        'id': self._next_id(),
        'params': args
      }

      encoded = encode(postdata)
      try:
         respdata = self._opener.open(url, encoded).read()
      except urllib2.URLError as ex:
         print 'Connection error: ' + str(ex)
         sys.exit(-1)

      jsondata = json.loads(respdata)

      if ('error' in jsondata):
         raise JsonError(jsondata['error'])

      return jsondata['result']

class JsonRpcProcessor(urllib2.BaseHandler):
   def __init__(self):
      self.handler_order = 100

   def http_request(self, request):
      request.add_header('content-type', 'application/json')
      request.add_header('user-agent', 'jsonrpc/netld')
      return request

   https_request = http_request

class JsonError(Exception):
   def __init__(self, value):
      self.value = value
   def __str__(self):
      return repr(self.value)

def dict_encode(obj):
   items = getattr(obj, 'iteritems', obj.items)
   return dict( (encode_(k),encode_(v)) for k,v in items() )

def list_encode(obj):
   return list(encode_(i) for i in obj)

def safe_encode(obj):
   '''Always return something, even if it is useless for serialization'''
   try: json.dumps(obj)
   except TypeError: obj = str(obj)
   return obj

def encode_(obj, **kw):
   obj = getattr(obj, 'json_equivalent', lambda: obj)()
   func = lambda x: x
   if hasattr(obj, 'items'):
      func = dict_encode
   elif hasattr(obj, '__iter__'):
      func = list_encode
   else:
      func = safe_encode
   return func(obj)

encode = functools.partial(json.dumps, default=encode_)

if __name__ == "__main__":
    main(sys.argv[1:])
