#!/usr/bin/env python

import sys
import getopt
import pandas as pd
import requests
import urllib.parse

netld_user = 'admin'
netld_pass = 'password'
netld_host = 'localhost'

def usage_and_exit():
    """Print the usage message and exit"""
    print('Usage:')
    print(
        'staticCredentials.py -f <csv input file> -h <netld server> -u <netld username> -p <netld password> -c '
        '<credential config name> [-n <network>]')
    sys.exit(2)

def main(argv):
    try:
        opts, args = getopt.getopt(argv,
                                   "f:h:u:p:c:m:",
                                   ["file=","host=","user=","password=","name=", "credentials=", "network="])
    except getopt.GetoptError:
        usage_and_exit()

    csv_file = ''
    host = ''
    user = ''
    password = ''
    credential_config_name = ''
    network = 'Default'

    for opt, arg in opts:
        if opt in ('-f', '--file'):
            csv_file = arg
        if opt in ('-h', '--host'):
            host = arg
        if opt in ('-u', '--user'):
            user = arg
        if opt in ('-p', '--password'):
            password = arg
        if opt in ('-c', '--credentials'):
            credential_config_name = arg
        if opt in ('-n', '--network'):
            network = arg

    if csv_file == '' or host == '' or user == '' or password == '' or credential_config_name == '':
        usage_and_exit()

    run(host, user, password, network, csv_file, credential_config_name)


def run(host, user, password, network, csv_file, credential_config_name):
    # Read the CSV file into a pandas DataFrame
    df = pd.read_csv(csv_file)

    # Convert the DataFrame to an Excel file
    df.to_excel('credentials.xlsx', index=False)

    fields = {'credentialConfig': credential_config_name, 'network': network}

    # Create a dictionary with the file content and specify the file field name ('file' in this case)
    files = {'Filedata': ('file.xlsx', open('./credentials.xlsx', 'rb'))}

    # URL-encode the user and password values
    escaped_user = urllib.parse.quote(user, safe='')
    escaped_password = urllib.parse.quote(password, safe='')

    # Perform the POST request with the files and additional data
    response = requests.post(
        f'https://{host}/servlet/credentials?j_username={escaped_user}&j_password={escaped_password}',
        data=fields, files=files)

    # Check the response
    if response.status_code == 200:
        print('Credentials upload successful!')
    else:
        print(f'Credentials upload failed with status code: {response.status_code}')
        print(response.text)
