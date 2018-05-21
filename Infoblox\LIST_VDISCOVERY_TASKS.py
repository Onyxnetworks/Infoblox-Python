import json
import sys
import requests
from getpass import getpass
from requests.auth import HTTPBasicAuth
from requests.packages.urllib3.exceptions import InsecureRequestWarning, InsecurePlatformWarning, SNIMissingWarning
from prettytable import PrettyTable

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
requests.packages.urllib3.disable_warnings(InsecurePlatformWarning)
requests.packages.urllib3.disable_warnings(SNIMissingWarning)

base_url = 'https://INFOBLOX_URL_HERE/wapi/v2.7/'
USERNAME = raw_input('Username: ')
PASSWORD = getpass()
headers = {'content-type': 'application/json'}

def blox_login( base_url, username, password ):
    """ Log into IPAM and generate a cookie for future requests """
    session_auth = requests.Session()
    session_auth.get(base_url + 'grid', verify=False, auth=HTTPBasicAuth(username,password))
    blox_login.cookies = session_auth.cookies

### Log into IPAM and generate a cookie for future requests ###
blox_login(base_url, USERNAME, PASSWORD)


### List vdisvoery tasks ###
url = 'vdiscoverytask'
table = PrettyTable(['Name', 'Task ID', 'State'])
g = requests.get(base_url + url, verify=False, cookies=blox_login.cookies)
g_response = g.json()
for tasks in g_response:
    table.add_row([tasks['name'], tasks['_ref'], tasks['state']])
print(table)


session_logout = requests.post(base_url + 'logout', verify=False, cookies=blox_login.cookies)
