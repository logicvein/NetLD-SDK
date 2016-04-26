#!/usr/bin/env python

import sys

def main(*args):
   ### Create a JSON-RPC proxy for the inventory service
   ###
   netld = JsonRpcProxy('https://localhost/rest', 'admin', 'password')

   ### use the inventory service to query for devices
   query = raw_input('Enter an individual IP address or IP/CIDR (eg. 10.0.0.0/24): ')

   pageData= {'offset': 0, 'pageSize': 500}

   # Inventory.search parameters:
   #   network, search scheme, query data, paging data, sort column, descending
   pageData = netld.call('Inventory.search', 'Default', 'ipAddress', query, pageData, 'ipAddress', False)

   print "Search found " + str(pageData['total']) + " devices.";
   print "----------------------------------------------";

   for device in pageData['devices']:
      print device['ipAddress'] + "   " + device['hostname']

   ### Logout using the security service to be nice to the server
   ###
   netld.call('Security.logoutCurrentUser')


### You can copy the code below into any python script that needs to interact
### with Net LineDancer

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
      self._hasher = sha1()
      self._id = 0
      self._opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookielib.CookieJar()))
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
      respdata = self._opener.open(url, encoded).read()
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

if __name__=="__main__":
   main(sys.argv)
