#!/usr/bin/env python

import sys
import json
import urllib2
import getopt
import urllib
import os
import csv
import time
import math

from jsonrpc.proxy import JSONRPCProxy

# Main
def main(argv):

    creds = urllib.urlencode({'j_username': user, 'j_password': password})
    netld = JSONRPCProxy.from_url("https://" + host + "/rest?%s" % creds)

    page = {
        offset: 0,
        pageSize: 100,
        total: 0,
        credentialSets: [],
    }

    credentialConfigName = 'My Static Credentials'
    network = 'default'
    ipOrCidr = None
    sortBy = 'ipAddress'
    sortDescending = True

    page = netld.call('Credentials.getCredentialSets', page, credentialConfigName, network, ipOrCidr, sortBy, sortDescending)

# Main
if __name__ == "__main__":
    main(sys.argv[1:])