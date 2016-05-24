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
import pprint
import zlib
from time import localtime, strftime
from jsonrpc import JsonRpcProxy, JsonError

HOST='host'
USERNAME='username'
PASSWORD='password'
LAST_END_TIME='lastEndTime'

def usageAndExit():
   print 'Usage: ' + sys.argv[0] + ' -o <output file> -c <settings file>'
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

   outputFile = ''
   configFile = ''

   for opt, arg in opts:
      if opt in ('-o', '--output'):
         outputFile = arg
      if opt in ('-c', '--config'):
         configFile = arg

   if outputFile == '':
      outputFile = "JobHistory" + strftime("%y%m%d-%H%M%S", localtime()) + ".txt"

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

      if config.has_option(section, LAST_END_TIME):
         inilastEndTime = config.getint(section, LAST_END_TIME)
      else:
         inilastEndTime = 0

      try:
         global _netld_svc
         _netld_svc = JsonRpcProxy("https://{0}/rest".format(host), user, password)

         inilastEndTime = exportJobHistory(outputFile, inilastEndTime)
         config.set(section, LAST_END_TIME, inilastEndTime)
      except urllib2.URLError as e:
         print "Error exporting Job History for host: " + host
         print str(e)

   file = open(configFile, 'w')
   config.write(file)
   file.close()


def millisToDate(millis):
   return datetime.datetime.utcfromtimestamp(millis / 1000)

def makeJobList(execution):
   jobList = '\n[ ' + \
      str(execution['status']) + ' / ' + str(execution['jobName']) + ' / ' + \
      str(execution['managedNetwork']) + ' / ' + str(execution['executor']) + ' / S:' + \
      millisToDate(execution['startTime']).strftime('%Y-%m-%d %H:%M:%S') + ' / E:' + \
      millisToDate(execution['endTime']).strftime('%Y-%m-%d %H:%M:%S') + \
      ' ]\n'
   return jobList


def exportJobHistory(outputFile, inilastEndTime):
   opener = urllib2.build_opener(_netld_svc._cookie_processor, _netld_svc._https_handler)

   pageData = {'offset': 0, 'pageSize': 1000}
   pageData = _netld_svc.call('Scheduler.getExecutionData', pageData, 'endTime', True)

   for execution in pageData['executionData']:
      startTime = millisToDate(execution['startTime'])
      lastEndTime = execution['endTime']
      EndTime = millisToDate(lastEndTime)

      execution_id = execution['id']

      details = _netld_svc.call('Plugins.getExecutionDetails', execution_id)

      if (details):
         for detail in details:
            if execution['jobType'] == 'Script Tool Job' and lastEndTime > inilastEndTime:
               file = open(outputFile, 'a')
               url = 'https://{0}/servlet/pluginDetail?executionId={1}&recordId={2}'.format(host, execution_id, detail['id'])
               response = opener.open(url)
               if response.headers.get('content-encoding', '') == 'deflate':
                  resp = zlib.decompressobj(-zlib.MAX_WBITS).decompress(response.read())
               else:
                  resp = response.read()

               file.write(makeJobList(execution))
               file.write(resp)
               file.close()

   _netld_svc.call('Security.logoutCurrentUser')

   return lastEndTime

if __name__ == "__main__":
   main(sys.argv[1:])
