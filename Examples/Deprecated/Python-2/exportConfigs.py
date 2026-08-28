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
LAST_TIMESTAMP='lastConfigTimestamp'

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
      print 'Setting file does not exist: ' + configFile
      sys.exit(3)

   config = ConfigParser.RawConfigParser()
   config.read(configFile)

   global host, user, password
   for section in config.sections():
      host = config.get(section, HOST)
      user = config.get(section, USERNAME)
      password = config.get(section, PASSWORD)

      if config.has_option(section, LAST_TIMESTAMP):
         lastTimestamp = config.getint(section, LAST_TIMESTAMP)
      else:
         lastTimestamp = 0

      try:
         global _netld_svc
         _netld_svc = JsonRpcProxy("https://{0}/jsonrpc".format(host), user, password)

         lastTimestamp = exportConfigs(output, lastTimestamp)
         config.set(section, LAST_TIMESTAMP, lastTimestamp)
      except urllib2.URLError as e:
         print "Error exporting configurations for host: " + host
         print str(e)

   file = open(configFile, 'w')
   config.write(file)
   file.close()


def millisToDate(millis):
   return datetime.datetime.utcfromtimestamp(millis / 1000)

def utc_to_local(utc_dt):
   # get integer timestamp to avoid precision lost
   timestamp = calendar.timegm(utc_dt.timetuple())
   local_dt = datetime.datetime.fromtimestamp(timestamp)
   assert utc_dt.resolution >= datetime.timedelta(microseconds=1)
   return local_dt.replace(microsecond=utc_dt.microsecond)

def createFilename(output, network, ipAddress, path, timestamp):
   localPath = path
   if localPath[0] == '/':
      localPath = localPath[1:]

   localTime = utc_to_local(timestamp)

   return output + '/' + network + '/' + ipAddress + '/' + localTime.strftime('%Y-%m-%d_%H-%M_') + localPath

def exportConfigs(output, lastTimestamp):
   opener = urllib2.build_opener(_netld_svc._cookie_processor, _netld_svc._https_handler)

   configs = _netld_svc.call('Configuration.retrieveConfigsSince', lastTimestamp)
   for config in configs:
      lastTimestamp = config['lastChanged']
      timestamp = millisToDate(lastTimestamp)

      network = config['managedNetwork']
      ipAddress = config['ipAddress']
      path = config['path']

      filename = createFilename(output, network, ipAddress, path, timestamp)

      directory = os.path.dirname(filename)
      if not os.path.exists(directory):
         os.makedirs(directory)

      params = urllib.urlencode({
            'op': 'config',
            'ipAddress': ipAddress,
            'managedNetwork': network.encode('utf-8'),
            'configPath': path,
            'timestamp': timestamp.isoformat(),
            'j_username': user,
            'j_password': password
            })
      url = 'https://' + host + '/servlet/inventoryServlet?%s' % params
      response = opener.open(url)
      file = open(filename, 'w')
      file.write(response.read())
      file.close()

      print "Wrote " + filename

   _netld_svc.call('Security.logoutCurrentUser')

   return lastTimestamp


if __name__ == "__main__":
   main(sys.argv[1:])
