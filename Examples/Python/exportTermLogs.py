#!/usr/bin/env python

import sys
import json
import urllib2
import datetime
import calendar
import urllib
import os
import ConfigParser
import getopt

# from jsonrpc.proxy import JSONRPCProxy

HOST='host'
USERNAME='username'
PASSWORD='password'
LAST_SESSION_END='lastSessionEnd'

def usageAndExit():
    print 'Usage:'
    print '  exportTermLogs.py -o <output directory> -c <config file>'
    sys.exit(2)

def main(argv):
    try:
        opts, args = getopt.getopt(argv,"o:c:",["output=","config="])
    except getopt.GetoptError:
        usageAndExit()

    output = ''
    configFile = ''

    for opt, arg in opts:
        if opt in ('-o', '--output'):
            output = arg
        if opt in ('-c', '--config'):
            configFile = arg

    if output == '':
        usageAndExit()

    if configFile == '':
        usageAndExit()

    if not os.path.exists(configFile):
        print 'Configuration file does not exist: ' + configFile
        sys.exit(3)

    config = ConfigParser.RawConfigParser()
    config.read(configFile)

    for section in config.sections():

        host = config.get(section, HOST)
        user = config.get(section, USERNAME)
        password = config.get(section, PASSWORD)

        if config.has_option(section, LAST_SESSION_END):
            lastSessionEnd = config.getint(section, LAST_SESSION_END)
        else:
            lastSessionEnd = 0

        try:
            lastSessionEnd = exportTermLogs(output, host, user, password, lastSessionEnd)
            config.set(section, LAST_SESSION_END, lastSessionEnd)
        except urllib2.URLError as e:
            print "Error exporting terminal logs for host: " + host
            print str(e)

    file = open(configFile, 'w')
    config.write(file)
    file.close()


def createFilename(output, sessionStart, termlog):
    count = 0
    localStart = utc_to_local(sessionStart)
    filename = output + filenamePrefix(localStart, termlog) + localStart.strftime('%H-%M') + '.log'
    while os.path.exists(filename):
        count += 1
        filename = output + filenamePrefix(localStart, termlog) + localStart.strftime('%H-%M-%S') + '-' + str(count) + '.log'

    return filename

def filenamePrefix(sessionStart, termlog):
    return '/' + sessionStart.strftime('%Y-%m-%d') + '/' + termlog['ipAddress'] + '_' + termlog['hostname'] + '_'

def millisToDate(millis):
    tmp = datetime.datetime.utcfromtimestamp(millis / 1000)
    return tmp 

def utc_to_local(utc_dt):
    # get integer timestamp to avoid precision lost
    timestamp = calendar.timegm(utc_dt.timetuple())
    local_dt = datetime.datetime.fromtimestamp(timestamp)
    assert utc_dt.resolution >= datetime.timedelta(microseconds=1)
    return local_dt.replace(microsecond=utc_dt.microsecond)

def exportTermLogs(output, host, user, password, lastSessionEnd):
    netld = JsonRpcProxy("https://{0}/rest".format(host), user, password)

    firstSessionEnd = millisToDate(lastSessionEnd)
    scheme = 'since'
    data = firstSessionEnd.isoformat()

    termlogs = netld.call('TermLogs.search', scheme, data, "sessionEnd", False)
    for termlog in termlogs:
        sessionStart = millisToDate(termlog['sessionStart'])
        lastSessionEnd = termlog['sessionEnd']
        sessionEnd = millisToDate(lastSessionEnd)

        print termlog['ipAddress'] + ': ' + sessionEnd.isoformat()
        print " Last: " + str(lastSessionEnd)

        filename = createFilename(output, sessionStart, termlog)

        directory = os.path.dirname(filename)
        if not os.path.exists(directory):
            os.makedirs(directory)

        params = urllib.urlencode({
                'op': 'content',
                'sessionStart': sessionStart.isoformat(),
                'ipAddress': termlog['ipAddress'],
                'managedNetwork': termlog['managedNetwork'].encode('utf-8'),
                'stripXml': 'true',
                'j_username': user,
                'j_password': password
                })
        url = 'https://' + host + '/servlet/termlog?%s' % params
        
        response = urllib2.urlopen(url)
        file = open(filename, 'w')
        file.write(response.read())
        file.close()

        print "Wrote " + filename

    netld.call('Security.logoutCurrentUser')

    return lastSessionEnd


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
