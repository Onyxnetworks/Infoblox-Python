import socket
import binascii
import json
import os
import sys
import requests
from prettytable import PrettyTable
from netaddr import IPNetwork,IPAddress
from getpass import getpass
import ipaddress
from requests.auth import HTTPBasicAuth
from requests.packages.urllib3.exceptions import InsecureRequestWarning, InsecurePlatformWarning, SNIMissingWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
requests.packages.urllib3.disable_warnings(InsecurePlatformWarning)
requests.packages.urllib3.disable_warnings(SNIMissingWarning)

# Replace URL's with correct URL'a
dc1 = 'https://DC1_URL/api/'
dc2 = 'https://DC2_URL/api/'
USERNAME = raw_input('Username: ')
PASSWORD = getpass()
headers = {'content-type': 'application/json'}
 
def apic_login( base_url, username, password ):
    """ Log into APIC and generate a cookie for future requests """
    eaders = {'content-type': 'application/json'}
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

def get_endpoints():
	try:
		# Log into fabtic and pull back details for Endpoints:
		apic_login(dc1, USERNAME, PASSWORD)
		list_endpoint = dc1 + 'node/class/fvCEp.json'  
		get_response = requests.get(list_endpoint, cookies=apic_login.cookies, headers=headers, verify=False)
		endpoint_all = json.loads(get_response.text)
		get_endpoints.endpoint_list = []    
		for i in endpoint_all['imdata']:                                         
			get_endpoints.endpoint_list.append({'Location': 'DC1', 'Tenant': i['fvCEp']['attributes']['dn'].split('/')[1][3:].encode('utf-8') ,'App Profile': i['fvCEp']['attributes']['dn'].split('/')[2][3:].encode('utf-8'),'EPG': i['fvCEp']['attributes']['dn'].split('/')[3][4:].encode('utf-8'),'Endpoint': i['fvCEp']['attributes']['ip'].encode('utf-8')})		# Log into fabtic and pull back details for L3Out Subnets:
		list_epg_subnet = dc1 + 'node/class/l3extSubnet.json'  
		get_response = requests.get(list_epg_subnet, cookies=apic_login.cookies, headers=headers, verify=False)
		epg_subnet_all = json.loads(get_response.text)
		get_endpoints.external_epg_list = []    
		for i in epg_subnet_all['imdata']:                                         
			get_endpoints.external_epg_list.append({'Location': 'DC1', 'Tenant': i['l3extSubnet']['attributes']['dn'].split('/')[1][3:].encode('utf-8'), 'L3Out': i['l3extSubnet']['attributes']['dn'].split('/')[2][4:].encode("utf-8"), 'EPG': i['l3extSubnet']['attributes']['dn'].split('/')[3][6:].encode("utf-8") ,'Endpoint': i['l3extSubnet']['attributes']['ip']})

		apic_login(dc2, USERNAME, PASSWORD)
		list_endpoint = dc2 + 'node/class/fvCEp.json'  
		get_response = requests.get(list_endpoint, cookies=apic_login.cookies, headers=headers, verify=False)
		endpoint_all = json.loads(get_response.text)
		for i in endpoint_all['imdata']:                                         
			get_endpoints.endpoint_list.append({'Location': 'DC2', 'Tenant': i['fvCEp']['attributes']['dn'].split('/')[1][3:].encode('utf-8') ,'App Profile': i['fvCEp']['attributes']['dn'].split('/')[2][3:].encode('utf-8'),'EPG': i['fvCEp']['attributes']['dn'].split('/')[3][4:].encode('utf-8'),'Endpoint': i['fvCEp']['attributes']['ip'].encode('utf-8')})		# Log into fabtic and pull back details for L3Out Subnets:
		list_epg_subnet = dc2 + 'node/class/l3extSubnet.json'  
		get_response = requests.get(list_epg_subnet, cookies=apic_login.cookies, headers=headers, verify=False)
		epg_subnet_all = json.loads(get_response.text)
		for i in epg_subnet_all['imdata']:                                         
			get_endpoints.external_epg_list.append({'Location': 'DC2', 'Tenant': i['l3extSubnet']['attributes']['dn'].split('/')[1][3:].encode('utf-8'), 'L3Out': i['l3extSubnet']['attributes']['dn'].split('/')[2][4:].encode("utf-8"), 'EPG': i['l3extSubnet']['attributes']['dn'].split('/')[3][6:].encode("utf-8") ,'Endpoint': i['l3extSubnet']['attributes']['ip']})

	except:
		print('Error!')

def main():
	get_endpoints()
	tableEndpint = PrettyTable(['Location', 'Tenant', 'App Profile/L3Out', 'EPG Name', 'Endpoint', 'Internal/External'])
	migration_filter = raw_input('Filter migration L3Outs?: y/n ')
	USER_INPUT = ''
	quit = 'quit'
	print('Type "quit" to close application and "refresh" to update Endpoint data')

	while USER_INPUT != quit:
		USER_INPUT=raw_input('Enter Network: ')
		os.system('clear')
		if len(USER_INPUT) == 0 or USER_INPUT.startswith('!'):
			pass

		elif USER_INPUT == 'refresh':
			print('Updataing data...')
			get_endpoints()
			print('Data updated')

		elif USER_INPUT !=quit:
			try:
				network = ipaddress.IPv4Network(unicode(USER_INPUT))
				for i in get_endpoints.external_epg_list:
					if migration_filter == 'y' and i['Tenant'].startswith(('PRD', 'PPE', 'DC1-SBS', 'DC2-SBS', 'DC1-STS', 'DC2-STS', 'DC1-REP', 'DC2-REP')) and i['L3Out'].endswith('L3O'):
						continue
					elif IPNetwork(USER_INPUT) in IPNetwork(i['Endpoint']) or IPNetwork(i['Endpoint']) in IPNetwork(USER_INPUT):
						tableEndpint.add_row([i['Location'], i['Tenant'], i['L3Out'], i['EPG'], i['Endpoint'], 'EXTERNAL'])
				for i in get_endpoints.endpoint_list:
				    if IPAddress(i['Endpoint']) in IPNetwork(USER_INPUT):
				    	tableEndpint.add_row([i['Location'], i['Tenant'], i['App Profile'], i['EPG'], i['Endpoint'], 'INTERNAL'])
				print(tableEndpint)
				tableEndpint = PrettyTable(['Location', 'Tenant', 'App Profile/L3Out', 'EPG Name', 'Endpoint', 'Internal/External'])
			except ValueError:
			    print(USER_INPUT + ' is not a valid network.')


if __name__ == "__main__":
main()
