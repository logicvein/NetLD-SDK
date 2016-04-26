#!/usr/bin/env python

import sys
import csv
import getopt
import math
import urllib
import urllib2
import zlib
import pprint

from time import localtime, strftime

def usageAndExit():
    print 'Usage:'
    print '  exportHardware.py [ -o <output file> ]'
    sys.exit(2)

def main(argv):
    try:
        opts, args = getopt.getopt(argv,"o:", ["output="])
    except getopt.GetoptError:
        usageAndExit()

    outputFile = ''

    for opt, arg in opts:
        if opt in ('-o', '--output'):
            outputFile = arg

    if outputFile == '':
        outputFile = "HardwareReport" + strftime("%y%m%d-%H%M%S", localtime()) + ".csv"

    network = 'Default'
    job_name = 'Hardware Report'

    netld = JsonRpcProxy('https://localhost/rest', 'admin', 'password')

    job = {
        'managedNetwork': network,
        'jobName': job_name,
        'jobType': 'Report',
        'description': '',
        'jobParameters': {
            'tool': 'ziptie.reports.hardware',
            'ipResolutionScheme': 'ipAddress',
            'ipResolutionData': '',
            'managedNetwork': network,
            'format': 'csv'
        },
    }

    execution = netld.call('Scheduler.runNow', job)

    print "** executing job **"
    execution_id = execution['id']

    while not execution['endTime']:
        if execution['completionState'] == 1 or execution['completionState'] == 2:
            print '** execution canceled **'
            break

        time.sleep(1)
        execution = netld.call('Scheduler.getExecutionDataById', execution_id)

    response = netld.url_opener().open('https://localhost/servlet/pluginDetail?executionId=' + str(execution_id) )
    
    if response.headers.get('content-encoding', '') == 'deflate':
        resp = zlib.decompressobj(-zlib.MAX_WBITS).decompress(response.read())
    else:
        resp = response.read()

    file = open(outputFile, 'w')
    file.write(resp)
    file.close()

    print "** Hardware Report Export execution complete **"

    netld.call('Security.logoutCurrentUser')

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
from datetime import tzinfo
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
      urllib2.install_opener(self._opener)
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

   def url_opener(self):
      return self._opener

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

class UTC(tzinfo):
   """UTC"""

   def utcoffset(self, dt):
      return timedelta(0)

   def tzname(self, dt):
      return "UTC"

   def dst(self, dt):
      return timedelta(0)

utc = UTC()

if __name__ == "__main__":
    main(sys.argv[1:])
