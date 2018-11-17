import json
import os,time
import requests
from prettytable import PrettyTable
from netaddr import IPNetwork,IPAddress
from getpass import getpass
import ipaddress

# Ignore SSL Errors
requests.packages.urllib3.disable_warnings()

class colour:
   PURPLE = '\033[95m'
   CYAN = '\033[96m'
   DARKCYAN = '\033[36m'
   BLUE = '\033[94m'
   GREEN = '\033[92m'
   YELLOW = '\033[93m'
   RED = '\033[91m'
   BOLD = '\033[1m'
   UNDERLINE = '\033[4m'
   END = '\033[0m'
  
# Function to exit script on errors.
def ERRORS():
    exit(colour.RED + 'Errors found. Exiting script.' + colour.END)

def USERNAME_PASSWORD():
    print(colour.BOLD + '\nPlease enter adm credentials.' + colour.END)
    ADM_USER = raw_input("\nEnter Username: ")
    ADM_PASS = getpass("\nEnter Password: ")

    return ADM_USER, ADM_PASS


def BANNER():
    print'>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>'
    print 'Cisco ACI'
    print 'IP Endpoint Search Tool'
    print'>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>'
    time.sleep(1)

 
def APIC_LOGIN(BASE_URL, APIC_USERNAME, APIC_PASSWORD, HEADERS):
    # Log into APIC and generate a cookie for future requests
    login_url = BASE_URL + 'aaaLogin.json'
    auth = {"aaaUser" : {"attributes" : {"name" : APIC_USERNAME,"pwd" : APIC_PASSWORD}}}
    auth_payload = json.dumps(auth)
    try:
        post_response = requests.post(login_url, data=auth_payload, headers=HEADERS, verify=False)
        # Take token from response to use for future authentications
        payload_response = json.loads(post_response.text)
        token = payload_response['imdata'][0]['aaaLogin']['attributes']['token']
        APIC_COOKIE = {}
        APIC_COOKIE['APIC-Cookie'] = token

    except:
        exit(colour.RED + 'Unable to connect to APIC. Please check your credentials' + colour.END)

    return APIC_COOKIE

def GET_ENDPOINT_INTERNAL(BASE_URL, APIC_COOKIE, HEADERS):
    try:
        GET_URL = BASE_URL + 'node/class/fvCEp.json'
        GET_RESPONSE = requests.get(GET_URL, cookies=APIC_COOKIE, headers=HEADERS, verify=False)
        ENDPOINT_INTERNAL_RESPONSE = json.loads(GET_RESPONSE.text)
        return ENDPOINT_INTERNAL_RESPONSE
    except:
        exit(colour.RED + 'Failed to get Internal Endpoint Data.' + colour.END)


def GET_ENDPOINT_EXTERNAL(BASE_URL, APIC_COOKIE, HEADERS):
    try:
        GET_URL = BASE_URL + 'node/class/l3extSubnet.json'
        GET_RESPONSE = requests.get(GET_URL, cookies=APIC_COOKIE, headers=HEADERS, verify=False)
        ENDPOINT_EXTERNAL_RESPONSE = json.loads(GET_RESPONSE.text)
        return ENDPOINT_EXTERNAL_RESPONSE
    except:
        exit(colour.RED + 'Failed to get External Endpoint Data.' + colour.END)

def GET_ENDPOINTS(DC_LIST, APIC_USERNAME, APIC_PASSWORD, HEADERS):

    ENDPOINT_INTERNAL_LIST = []
    ENDPOINT_EXTERNAL_LIST = []
    for BASE_URL in DC_LIST:
        if 'ukdc1' in BASE_URL:
            LOCATION = 'DC1'
        elif 'ukdc2' in BASE_URL:
            LOCATION = 'DC2'
        else:
            LOCATION = 'UNKNOWN'
        # Connect to APIC.
        APIC_COOKIE = APIC_LOGIN(BASE_URL, APIC_USERNAME, APIC_PASSWORD, HEADERS)

        # Get Internal Endpoint data.
        ENDPOINT_INTERNAL_RESPONSE = GET_ENDPOINT_INTERNAL(BASE_URL, APIC_COOKIE, HEADERS)
        for i in ENDPOINT_INTERNAL_RESPONSE['imdata']:
            ENDPOINT_INTERNAL_LIST.append({'Location': LOCATION, 'Tenant': i['fvCEp']['attributes']['dn'].split('/')[1][3:].encode('utf-8'),'App Profile': i['fvCEp']['attributes']['dn'].split('/')[2][3:].encode('utf-8'),'EPG': i['fvCEp']['attributes']['dn'].split('/')[3][4:].encode('utf-8'),'Endpoint': i['fvCEp']['attributes']['ip'].encode('utf-8')})

        # Get External Endpoint data.
        ENDPOINT_EXTERNAL_RESPONSE = GET_ENDPOINT_EXTERNAL(BASE_URL, APIC_COOKIE, HEADERS)
        for i in ENDPOINT_EXTERNAL_RESPONSE['imdata']:
			IMPORT = ''
			EXPORT = ''
			SECURITY = ''
			if 'import-rtctrl' in i['l3extSubnet']['attributes']['scope']:
				IMPORT = 'I '
			if 'export-rtctrl' in i['l3extSubnet']['attributes']['scope']:
				EXPORT = 'E '
			if 'import-security' in i['l3extSubnet']['attributes']['scope']:
				SECURITY = 'S '
            
			SCOPE = IMPORT + EXPORT + SECURITY
				
			ENDPOINT_EXTERNAL_LIST.append({'Location': LOCATION, 'Tenant': i['l3extSubnet']['attributes']['dn'].split('/')[1][3:].encode('utf-8'), 'L3Out': i['l3extSubnet']['attributes']['dn'].split('/')[2][4:].encode("utf-8"), 'EPG': i['l3extSubnet']['attributes']['dn'].split('/')[3][6:].encode("utf-8") ,'Endpoint': i['l3extSubnet']['attributes']['ip'], 'Scope': SCOPE })


    return ENDPOINT_INTERNAL_LIST, ENDPOINT_EXTERNAL_LIST


def main():
    BANNER()
    DC_LIST = ['', '']
    USER_DETAILS = USERNAME_PASSWORD()
    APIC_USERNAME = USER_DETAILS[0]
    APIC_PASSWORD = USER_DETAILS[1]
    print(colour.BOLD + '\nFilter migration L3Outs?' + colour.END)
    print(colour.YELLOW + 'This will remove all network centric 0.0.0.0/0 External Subnets from search results' + colour.END)
    MIGRATION_FILTER = raw_input('\ny/n:   ').upper()
    HEADERS = {'content-type': 'application/json'}

    # Build endpoint list.
    time.sleep(1)
    print(colour.BOLD + '\nGetting Endpoint data.\n' + colour.END)
    # Returns a list for internal and external endpoints place [0] is internal and [1] external.
    ENDPOINT_LISTS = GET_ENDPOINTS(DC_LIST, APIC_USERNAME, APIC_PASSWORD, HEADERS)

    # Build table structure
    TABLE_ENDPOINT = PrettyTable(['Location', 'Tenant', 'App Profile/L3Out', 'EPG Name', 'Endpoint', 'Scope', 'Internal/External'])
    USER_INPUT = ''
    QUIT = 'quit'
    print(colour.BOLD + 'Type "quit" to close application and "refresh" to update Endpoint data' + colour.END)

    while USER_INPUT != QUIT:
        USER_INPUT=raw_input(colour.BOLD + 'Enter Network: ' + colour.END)    
        if len(USER_INPUT) == 0 or USER_INPUT.startswith('!'):
            pass

        elif USER_INPUT == 'refresh':
            print(colour.BOLD + '\nUpdataing data...' + colour.END)
            ENDPOINT_LISTS = GET_ENDPOINTS(DC_LIST, APIC_USERNAME, APIC_PASSWORD, HEADERS)
            print(colour.BOLD + '\nEndpoint data updated' + colour.END)

        elif USER_INPUT !=QUIT:
            print(colour.BOLD + '\nScope Key: I = Import Route Control, E = Export Route Control, S = Security\n' + colour.END)
            try:
                network = ipaddress.IPv4Network(unicode(USER_INPUT))
                for i in ENDPOINT_LISTS[1]:
                    if MIGRATION_FILTER == 'Y' and i['Tenant'].startswith(('PRD', 'PPE', 'DC1-SBS', 'DC2-SBS', 'DC1-STS', 'DC2-STS', 'DC1-REP', 'DC2-REP', 'DC1-OTV', 'DC2-OTV')) and i['L3Out'].endswith('L3O'):
                        continue
                    elif IPNetwork(USER_INPUT) in IPNetwork(i['Endpoint']) or IPNetwork(i['Endpoint']) in IPNetwork(USER_INPUT):
                        TABLE_ENDPOINT.add_row([i['Location'], i['Tenant'], i['L3Out'], i['EPG'], i['Endpoint'], i['Scope'], 'EXTERNAL'])
                for i in ENDPOINT_LISTS[0]:
                    if IPAddress(i['Endpoint']) in IPNetwork(USER_INPUT):
                        TABLE_ENDPOINT.add_row([i['Location'], i['Tenant'], i['App Profile'], i['EPG'], i['Endpoint'], 'N/A', 'INTERNAL'])
                print(TABLE_ENDPOINT)
                TABLE_ENDPOINT = PrettyTable(['Location', 'Tenant', 'App Profile/L3Out', 'EPG Name', 'Endpoint', 'Scope', 'Internal/External'])
            except ValueError:
                print(colour.YELLOW + USER_INPUT + ' is not a valid network.' + colour.END)
		

if __name__ == "__main__":
    main()
