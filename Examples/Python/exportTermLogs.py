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
from jsonrpc import JsonRpcProxy, JsonError

HOST='host'
USERNAME='username'
PASSWORD='password'
LAST_SESSION_END='lastSessionEnd'

def usageAndExit():
   print 'Usage:'
   print '  exportTermLogs.py -o <output directory> -c <config file>'
   sys.exit(2)

host = None
user = None
password = None
_netld_svc = None

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

   global host, user, password
   for section in config.sections():
      host = config.get(section, HOST)
      user = config.get(section, USERNAME)
      password = config.get(section, PASSWORD)

      if config.has_option(section, LAST_SESSION_END):
         lastSessionEnd = config.getint(section, LAST_SESSION_END)
      else:
         lastSessionEnd = 0

      try:
         global _netld_svc
         _netld_svc = JsonRpcProxy("https://{0}/jsonrpc".format(host), user, password)

         lastSessionEnd = exportTermLogs(output, lastSessionEnd)
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

def exportTermLogs(output, lastSessionEnd):
   opener = urllib2.build_opener(_netld_svc._cookie_processor, _netld_svc._https_handler)

   firstSessionEnd = millisToDate(lastSessionEnd)
   scheme = 'since'
   data = firstSessionEnd.isoformat()

   termlogs = _netld_svc.call('TermLogs.search', scheme, data, "sessionEnd", False)
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

      response = opener.open(url)
      file = open(filename, 'w')
      file.write(response.read())
      file.close()

      print "Wrote " + filename

   _netld_svc.call('Security.logoutCurrentUser')

   return lastSessionEnd


if __name__ == "__main__":
   main(sys.argv[1:])
