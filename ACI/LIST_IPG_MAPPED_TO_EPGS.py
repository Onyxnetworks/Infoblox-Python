import json
import sys
import requests
from getpass import getpass
from prettytable import PrettyTable
from requests.auth import HTTPBasicAuth
from requests.packages.urllib3.exceptions import InsecureRequestWarning, InsecurePlatformWarning, SNIMissingWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
requests.packages.urllib3.disable_warnings(InsecurePlatformWarning)
requests.packages.urllib3.disable_warnings(SNIMissingWarning)

DC1 = ''
DC2 = ''


DC_SELECTION = raw_input('Enter DC: DC1/DC2  ')
USERNAME = raw_input('Username: ')
PASSWORD = getpass()
headers = {'content-type': 'application/json'}
""" DC Selection """
if DC_SELECTION == 'DC1':
	base_url = DC1
elif DC_SELECTION == 'DC2':
    base_url = DC2
else:
    print('Invalid DC Argument')


def apic_login( base_url, username, password ):

    """ Log into APIC and generate a cookie for future requests """
    headers = {'content-type': 'application/json'}
    login_url = base_url + 'aaaLogin.json'
    auth = {"aaaUser" : {"attributes" : {"name" : username,"pwd" : password}}}
    auth_payload = json.dumps(auth)
    post_response = requests.post(login_url, data=auth_payload, headers=headers, verify=False)

    """ Take token from response to use for future authentications """
    payload_response = json.loads(post_response.text)
    token = payload_response['imdata'][0]['aaaLogin']['attributes']['token']
    apic_login.cookies = {}
    apic_login.cookies['APIC-Cookie'] = token
    # Debug - Valid cookie being returned
    #print(apic_login.cookies )

### Log into APIC and generate a cookie for future requests ###
apic_login(base_url, USERNAME, PASSWORD)

# List all IPG's in fabric
list_ipg = base_url + 'node/class/fabricPathEp.json'
get_response = requests.get(list_ipg, cookies=apic_login.cookies, verify=False)
ipg_all = json.loads(get_response.text)
ipg_list = []
# loop through output and add IPG names to list
i = 0
for ipg in ipg_all['imdata']:
    ipg_list.append(ipg['fabricPathEp']['attributes']['name'].encode("utf-8"))
    i += 1


# List all EPG for selected
IPG_NAME = raw_input('IPG Name: ')
if IPG_NAME in ipg_list:
    mapped_ipg = base_url + 'node/class/fvRsPathAtt.json?query-target-filter=and(wcard(fvRsPathAtt.tDn,"' + IPG_NAME + '"))'
    get_response = requests.get(mapped_ipg, cookies=apic_login.cookies, verify=False)
    epg_all = json.loads(get_response.text)
    epg_ipg_list = []
    table = PrettyTable(['Tenant', 'EPG'])

    # loop through output, print and add EPG's to list
    i = 0
    for epg in epg_all['imdata']:
        epg_ipg_list.append(epg['fvRsPathAtt']['attributes']['dn'].split('/')[3][3:].encode("utf-8"))
        table.add_row([epg['fvRsPathAtt']['attributes']['dn'].split('/')[1][3:], epg['fvRsPathAtt']['attributes']['dn'].split('/')[3][4:]])
        #print('| Tenant: ' + [epg['fvRsPathAtt']['attributes']['dn'].split('/')[1][3:] + ' | EPG: ' + epg['fvRsPathAtt']['attributes']['dn'].split('/')[3][4:] + ' |')
        i += 1
else:
    print('IPG not found!')
print(table)
