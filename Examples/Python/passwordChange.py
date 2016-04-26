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

def usage_and_exit():
    """Print the usage message and exit"""
    print 'Usage:'
    print '  passwordChange.py -f <csv input file> -h <netld server> -u <netld username> -p <netld password> -c <credential config name> [-n <job name>]'
    sys.exit(2)

# Main
def main(argv):
    try:
        opts, args = getopt.getopt(argv,"f:h:u:p:n:c:m:",["file=","host=","user=","password=","name=", "credentials=", "network="])
    except getopt.GetoptError:
        usage_and_exit()

    csv_file = ''
    host = ''
    user = ''
    password = ''
    credential_config_name = ''
    job_name = 'Password Change'
    network = 'Default'

    for opt, arg in opts:
        if opt in ('-h', '--host'):
            host = arg
        if opt in ('-f', '--file'):
            csvFile = arg
        if opt in ('-u', '--user'):
            user = arg
        if opt in ('-p', '--password'):
            password = arg
        if opt in ('-n', '--name'):
            job_name = arg
        if opt in ('-c', '--credentials'):
            credential_config_name = arg
        if opt in ('-m', '--network'):
            network = arg

    if csv_file == '' or host == '' or user == '' or password == '' or credential_config_name == '':
        usage_and_exit()

    run(host, user, password, network, csv_file, job_name, credential_config_name)

# Run the job
def run(host, user, password, network, csv_file, job_name, credential_config_name):
    with open(csv_file, 'rb') as f:
        reader = csv.reader(f)
        for row in reader:
            print row

    target_tag = ''
    # TODO lbayer: use user inputed values...
    new_password = 'newPassword'
    new_enable_password = 'newEnablePassword'

    creds = urllib.urlencode({'j_username': user, 'j_password': password})
    netld = JSONRPCProxy.from_url("https://" + host + "/rest?%s" % creds)

    job = {
        'managedNetwork': network,
        'jobName': job_name,
        'jobType': 'Script Tool Job',
        'description': '',
        'jobParameters': {
            'tool': 'org.ziptie.tools.scripts.changemultipassword',
            'ipResolutionScheme': 'tag',
            'ipResolutionData': target_tag,
            'managedNetwork': network,
            'backupOnCompletion': 'false',
            'input.newPassword': new_password,
            'input.newEnablePassword': new_enable_password,
        },
    }

    execution = netld.call('Scheduler.runNow', job)

    print '** executing job **'

    execution_id = execution['id'];

    x = 0
    # wait for completion
    while not execution['endTime']:
        if execution['completionState'] == 1 or execution['completionState'] == 2:
            print '** execution canceled **'
            break

        x += .1
        time.sleep(math.atan(x)) # gradually increase wait time, so we don't have to wait very long for short jobs, but we don't make too many calls for long jobs
        execution = netld.call('Scheduler.getExecutionDataById', execution_id)

    ips_to_update = {}

    # print individual script run details...
    tool_run_details = netld.call('Plugins.getExecutionDetails', executionId)
    for detail in tool_run_details:
        print_details(host, user, password, executionId, detail)
        ips_to_update[detail.ipAddress] = True;

    update_credentials(network, credential_config_name, ips_to_update, new_password, new_enable_password)

    print "** password change execution complete **"

def update_credentials(network, credential_config_name, ips_to_update, new_password, new_enable_password):
    """Updates the static credential configuration to reflect the new passwords."""

    print '** updating static credential mappings **'

    page = {
        offset: 0,
        pageSize: 1000,
        total: 0,
        credentialSets: [],
    }

    while True:
        page = netld.call('Credentials.getCredentialSets', page, credential_config_name, network, None, "ipAddress", True)

        creds = []
        for set in page.credentialSets:
            if set.name in ips_to_update:
                del ips_to_update[set.name]
                set.password = new_password
                set.enablePassword = new_enable_password
                creds.append(set)

        if creds:
            netld.call('Credentials.saveCredentialSets', network, credential_config_name, creds)

        page.offset = page.offset + page.pageSize
        if page.offset > page.total:
            break

    for ip in ips_to_update.keys():
        print "! no credentials defined in static credential set for " + ip

    netld.call('Credentials.commitEdits')

def print_details(host, user, password, execution_id, detail):
    """Load and print the script output details to stdout for the given tool record"""
    params = urllib.urlencode({
        'executionId': execution_id,
        'recordId': detail.id,
        'j_username': user,
        'j_password': password
    })

    response = urllib2.urlopen('https://' + host + '/servlet/pluginDetail?%s' % params)
    print response.read()

# Main
if __name__ == "__main__":
    main(sys.argv[1:])
