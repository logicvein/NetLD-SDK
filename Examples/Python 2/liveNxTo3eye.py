#!/usr/bin/env python

import os
import csv
import sys
import ssl
import json
import math
import time
import urllib
import urllib2
from jsonrpc import JsonRpcProxy, JsonError

liveNxHost = "10.0.0.1"
liveNxApiPort = "8093"
liveNxToken = "5WuHhswF5CzGOZ7v12g8iu5+F8PqpmHoOGSt3wWP9rs="

thirdeyeHost = "10.0.40.110"
thirdeyeUser = "admin"
thirdeyePass = "password"
thirdeyeNetwork = 'Default'

def main(*args):
   ctx = ssl.create_default_context()
   ctx.check_hostname = False
   ctx.verify_mode = ssl.CERT_NONE

   # export CSV file from LiveNX
   headers = {
      "accept": "text/csv",
      "Authorization": "Bearer " + liveNxToken
   }
   request = urllib2.Request("https://" + liveNxHost + ":" + liveNxApiPort + "/v1/devices/export/csv", None, headers) # , "mp3.mp3")
   f = urllib2.urlopen(url=request, context=ctx)

   # Open our local CSV file for writing
   with open(os.path.basename("inventory.csv"), "wb") as local_file:
      local_file.write(f.read())

   # read CSV into a dictionary (hash) where the IP address is the key
   addresses = {}
   with open('inventory.csv', 'rb') as csvfile:
      reader = csv.DictReader(csvfile)
      for row in reader:
         if len(row['VENDOR']) > 0:
            addresses[row['IP ADDRESS']] = True

   ### Create a JSON-RPC proxy for the inventory service
   ###
   _netld_svc = JsonRpcProxy.fromHost(thirdeyeHost, thirdeyeUser, thirdeyePass)

   # page data object for iterating ThirdEye inventory search results
   pageData = {'offset': 0, 'pageSize': 500}

   while True:
      pageData = _netld_svc.call('Inventory.search', [thirdeyeNetwork], 'ipAddress', "", pageData, 'ipAddress', False)

      if pageData['total'] == 0:
         break

      # remove IPs from 'addresses' that already exist in ThirdEye
      for device in pageData['devices']:
         addresses.pop(device['ipAddress'], None)

      # break if we've reached the end
      if pageData['offset'] + pageData['pageSize'] >= pageData['total']:
         break

      # next page
      pageData['offset'] += pageData['pageSize']

   if len(addresses.keys()):
      quit

   ipCSV = ','.join(addresses.keys())

   for addr in addresses.keys():
      print addr

   job = {
      'managedNetworks': thirdeyeNetwork,
      'jobName': 'Discover',
      'jobType': 'Discover Devices',
      'description': '',
      'jobParameters': {
         'includedAddresses': ipCSV,
         'crawl': False
      },
   }

   # execute discovery job
   print "Waiting for end of discovery."
   execution = _netld_svc.call('Scheduler.runNow', job)

   execution_id = execution['id'];

   # wait for discovery job completion
   x = 0
   while not execution['endTime']:
      if execution['completionState'] == 1 or execution['completionState'] == 2:
         print '** execution canceled **'
         break

      x += .1
      time.sleep(math.atan(x)) # gradually increase wait time, so we don't have to wait very long for short jobs, but we don't make too many calls for long jobs
      execution = _netld_svc.call('Scheduler.getExecutionDataById', execution_id)

   ### Logout using the security service to be nice to the server
   ###
   _netld_svc.call('Security.logoutCurrentUser')


if __name__=="__main__":
   main(sys.argv)
