import openpyxl
import requests, json, time
from getpass import getpass
from netaddr import IPNetwork, IPAddress
import ipaddress
import argparse

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

def ERRORS():
    print(colour.RED + 'Errors found. Exiting script.' + colour.END)
    time.sleep(2)
    exit()

def OPEN_EXCEL(BASE_URL, DC1, DC2, LAB, SANDBOX):
    #EXCEL_NAME = 'Python Contracts'
    EXCEL_NAME = raw_input("Enter Contract workbook path and name: ")

    try:
        WB = openpyxl.load_workbook('{}.xlsx'.format(EXCEL_NAME), data_only=True)
        if BASE_URL == DC1:
            PY_WS = WB['ACI_DC1']
        elif BASE_URL == DC2:
            PY_WS = WB['ACI_DC2']
        elif BASE_URL == LAB:
            PY_WS = WB['ACI_LAB']
        elif BASE_URL == SANDBOX:
            PY_WS = WB['ACI_SANDBOX']
        return PY_WS


    except:
        print 'Unable to open {}, please check file name and path is correct'.format(EXCEL_NAME)
        exit()
	
	
def BANNER():
    print'>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>'
    print 'Cisco ACI'
    print 'External EPG Provisioning Script '
    print'>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>'
    time.sleep(1)

	
def EXCEL_MUNGER(PY_WS):
    ERROR = False
    SERVICE_LIST = []
    RULE_LIST = []
    INDEX = 1
    # Loops through the rows in the worksheet to build contract information
    try:
        for row in PY_WS.iter_rows(min_row=2, max_col=10):
            CONSUMER_IP_LIST = []
            PROVIDER_IP_LIST = []
            if row[8].value:
                CONSUMER_EPG = row[8].value.upper()
            else:
                CONSUMER_EPG = 'BLANK'
            if row[5].value:
                PROVIDER_EPG = row[5].value.upper()
            else:
                PROVIDER_EPG = 'BLANK'
            if row[9].value:
                CONSUMER_IP_LIST = row[9].value.split()
                i = 0
                for IP in CONSUMER_IP_LIST:
                    if len(IP.split('/')) <= 1:
                        IP_SUBNET = IP + '/32'
                        CONSUMER_IP_LIST[i] = IP_SUBNET
                    i = i + 1
				
            else:
                pass
            if row[6].value:
                PROVIDER_IP_LIST = row[6].value.split()
                i = 0
                for IP in PROVIDER_IP_LIST:
                    if len(IP.split('/')) <= 1:
                        IP_SUBNET = IP + '/32'
                        PROVIDER_IP_LIST[i] = IP_SUBNET
                    i = i + 1			
            else:
                pass
            if row[7].value:
                CONSUMER_L3OUT = row[7].value.upper()
            else:
                CONSUMER_L3OUT = 'INTERNAL'
            if row[4].value:
                PROVIDER_L3OUT = row[4].value.upper()
            else:
                PROVIDER_L3OUT = 'INTERNAL'

            INDEX += 1
            RULE_LIST.append({'LINE': INDEX, 'PROVIDER_L3OUT': PROVIDER_L3OUT, 'CONSUMER_L3OUT': CONSUMER_L3OUT, 'CONSUMER_EPG': CONSUMER_EPG, 'CONSUMER_IP': CONSUMER_IP_LIST, 'PROVIDER_EPG': PROVIDER_EPG, 'PROVIDER_IP': PROVIDER_IP_LIST })

        return RULE_LIST

    except:
        exit( colour.RED + 'Error Reading from excel. Please check all columns are populated\n' + colour.END)

		
def USERNAME_PASSWORD():
    print '\nPlease enter adm credentials.'
    ADM_USER = raw_input("\nEnter Username: ")
    ADM_PASS = getpass("\nEnter Password: ")

    return ADM_USER, ADM_PASS

def EXCEL_FORMAT_VALIDATION(RULE_LIST, args):
    DISPLAY_LIST = []
    TENANT_LIST = ['RED', 'GREEN', 'BLUE']
    ERROR = False

    print(colour.BOLD + '\nValidating EPG names in Workbook.' + colour.END)
    print(colour.BOLD + '-----------------------------\n' + colour.END)
    time.sleep(1)

    #try:
    for rules in RULE_LIST:
        if rules['CONSUMER_EPG'] != 'BLANK' and rules['CONSUMER_L3OUT'] != 'INTERNAL':
            if len(rules['CONSUMER_EPG'].split('_')) > 2:
                DISPLAY_LIST.append(rules['CONSUMER_EPG'])
                ERROR = True
                if args.v:
                    print(colour.RED + 'Error 1 - To many underscores in Consumer EPG Name' + colour.END)

            elif rules['CONSUMER_EPG'].split('_')[1].upper() != 'EPG':
                DISPLAY_LIST.append(rules['CONSUMER_EPG'])
                ERROR = True
                if args.v:
                    print(colour.RED + 'Error 2 - EPG name should end _EPG' + colour.END)
            elif rules['CONSUMER_EPG'].split('-')[0].upper() not in TENANT_LIST:
                DISPLAY_LIST.append(rules['CONSUMER_EPG'])
                ERROR = True
                if args.v:
                    print(colour.RED + 'Error 3 - Prefix of EPG not in the tenant list (RED,GREEN,BLUE)' + colour.END)
            elif rules['CONSUMER_L3OUT'].split('_')[0].endswith('CLOUD'):
		        continue
			# TEMP FIX FOR BLUE INET UNTIL RENAME
            elif rules['CONSUMER_L3OUT'] == 'BLUE-DC1-INET_L3O' or 'BLUE-DC2-INET_L3O':
		        continue
            elif not rules['CONSUMER_EPG'].split('_')[0].startswith(rules['CONSUMER_EPG'].split('_')[0]):
                DISPLAY_LIST.append(rules['CONSUMER_EPG'])
                ERROR = True
                if args.v:
                    print(colour.RED + 'Error 4 - Consumer EPG & L3Out Prefix dont match' + colour.END)
            else:
                pass
        if rules['PROVIDER_EPG'] != 'BLANK' and rules['PROVIDER_L3OUT'] != 'INTERNAL':
            if len(rules['PROVIDER_EPG'].split('_')) > 2:
                DISPLAY_LIST.append(rules['PROVIDER_EPG'])
                ERROR = True
                if args.v:
                    print(colour.RED + 'Error 5 - To many underscores in Provider EPG Name' + colour.END)
            elif rules['PROVIDER_EPG'].split('_')[1].upper() != 'EPG':
                DISPLAY_LIST.append(rules['PROVIDER_EPG'])
                ERROR = True
                if args.v:
                    print(colour.RED + 'Error 6 - EPG name should end _EPG' + colour.END)
            elif rules['PROVIDER_EPG'].split('-')[0].upper() not in TENANT_LIST:
                DISPLAY_LIST.append(rules['PROVIDER_EPG'])
                ERROR = True
                if args.v:
                    print(colour.RED + 'Error 7 - Prefix of EPG not in the tenant list (RED,GREEN,BLUE)' + colour.END)
            elif rules['PROVIDER_L3OUT'].split('_')[0].endswith('CLOUD'):
		        continue
			# TEMP FIX FOR BLUE INET UNTIL RENAME
            elif rules['PROVIDER_L3OUT'] == 'BLUE-DC1-INET_L3O' or 'BLUE-DC2-INET_L3O':
		        continue
            elif not rules['PROVIDER_EPG'].split('_')[0].startswith(rules['PROVIDER_L3OUT'].split('_')[0]):
                DISPLAY_LIST.append(rules['PROVIDER_EPG'])
                ERROR = True
                if args.v:
                    print(colour.RED + 'Error 8 - Provider EPG & L3Out Prefix dont match' + colour.END)
            else:
                pass

        else:
            pass

    DISPLAY_SET = set(DISPLAY_LIST)
    for contracts in DISPLAY_SET:
        print(colour.YELLOW + 'EPG "' + contracts + '" does not conform to the naming standards' + colour.END)
    DISPLAY_LIST = []


    #except:
    #    exit('Errors validating EPG names')

    if ERROR:
        exit(colour.RED + 'Errors validating EPG names' + colour.END)
    else:
        time.sleep(2)
        print('EPG formatting validated successfully')


def APIC_LOGIN(BASE_URL, APIC_USERNAME, APIC_PASSWORD, HEADERS):
    # Log into APIC and generate a cookie for future requests
    login_url = BASE_URL + 'aaaLogin.json'
    auth = {"aaaUser": {"attributes": {"name": APIC_USERNAME, "pwd": APIC_PASSWORD}}}
    auth_payload = json.dumps(auth)
    try:
        post_response = requests.post(login_url, data=auth_payload, headers=HEADERS, verify=False)
        # Take token from response to use for future authentications
        payload_response = json.loads(post_response.text)
        token = payload_response['imdata'][0]['aaaLogin']['attributes']['token']
        APIC_COOKIE = {}
        APIC_COOKIE['APIC-Cookie'] = token
        print('Connected Successfully.')

    except:
        exit(colour.RED + 'Unable to connect to APIC. Please check your credentials' + colour.END)

    return APIC_COOKIE


def L3OUT_SEARCH(BASE_URL, APIC_COOKIE, TENANT, L3OUT_NAME, HEADERS):
    L3OUT_SEARCH_BASE_URL = BASE_URL + 'node/mo/uni/tn-{0}/out-{1}.json?query-target=self'.format(TENANT, L3OUT_NAME)
    L3OUT_SEARCH_CHILDREN_URL = BASE_URL + 'node/mo/uni/tn-{0}/out-{1}.json?query-target=children'.format(TENANT, L3OUT_NAME)

    try:
        get_response = requests.get(L3OUT_SEARCH_BASE_URL, cookies=APIC_COOKIE, headers=HEADERS, verify=False)
        L3OUT_SEARCH_RESPONSE_BASE = json.loads(get_response.text)
        get_response = requests.get(L3OUT_SEARCH_CHILDREN_URL, cookies=APIC_COOKIE, headers=HEADERS, verify=False)
        L3OUT_SEARCH_RESPONSE_CHILDREN = json.loads(get_response.text)
        return L3OUT_SEARCH_RESPONSE_BASE, L3OUT_SEARCH_RESPONSE_CHILDREN


    except:
        exit(colour.RED + 'Failed to search for EPG' + colour.END)


def EXTERNAL_EPG_SEARCH(BASE_URL, APIC_COOKIE, TENANT, L3OUT_NAME, EPG_NAME, HEADERS):
								
    EPG_SEARCH_URL = BASE_URL + '/node/class/l3extInstP.json?query-target-filter=and(eq(l3extInstP.dn,"uni/tn-{0}/out-{1}/instP-{2}"))'.format(TENANT, L3OUT_NAME, EPG_NAME)
    try:
        get_response = requests.get(EPG_SEARCH_URL, cookies=APIC_COOKIE, headers=HEADERS, verify=False)
        EXTERNAL_EPG_SEARCH_RESPONSE = json.loads(get_response.text)
        return EXTERNAL_EPG_SEARCH_RESPONSE


    except:
        exit(colour.RED + 'Failed to search for EPG' + colour.END)
		
		
def VRF_SEARCH(BASE_URL, APIC_COOKIE, VRF_DN, HEADERS):
    VRF_SEARCH_URL = BASE_URL + 'node/mo/{0}.json?query-target=children'.format(VRF_DN)

    try:
        get_response = requests.get(VRF_SEARCH_URL, cookies=APIC_COOKIE, headers=HEADERS, verify=False)
        VRF_SEARCH_RESPONSE = json.loads(get_response.text)
        return VRF_SEARCH_RESPONSE

    except:
        exit(colour.RED + 'Failed to search for VRF' + colour.END)


def SUBNET_SEARCH(BASE_URL, APIC_COOKIE, L3OUT_DN, HEADERS):
    SUBNET_SEARCH_URL = BASE_URL + 'node/class/l3extSubnet.json?query-target-filter=and(wcard(l3extSubnet.dn,"{0}/"))'.format(L3OUT_DN)

    try:
        get_response = requests.get(SUBNET_SEARCH_URL, cookies=APIC_COOKIE, headers=HEADERS, verify=False)
        SUBNET_SEARCH_RESPONSE = json.loads(get_response.text)
        return SUBNET_SEARCH_RESPONSE

    except:
        exit(colour.RED + 'Failed to search for Subnets' + colour.END)


def EXTERNAL_EPG_SUBNET_ADD(BASE_URL, APIC_COOKIE, TENANT, L3OUT_NAME, EPG_NAME, HEADERS, IP, SCOPE):

    ADD_SUBNET_L3OUT_URL = BASE_URL + 'node/mo/uni/tn-{0}/out-{1}/instP-{2}/extsubnet-[{3}].json'.format(TENANT, L3OUT_NAME, EPG_NAME, IP)
    ADD_SUBNET_L3OUT_JSON = {"l3extSubnet": {"attributes": {"ip": IP, "scope": SCOPE, "aggregate": "", "status": "created"}, "children": []}}

    try:
        post_response = requests.post(ADD_SUBNET_L3OUT_URL, cookies=APIC_COOKIE, data=json.dumps(ADD_SUBNET_L3OUT_JSON), headers=HEADERS, verify=False)
        EXTERNAL_EPG_SUBNET_RESPONSE = json.loads(post_response.text)

        if int(EXTERNAL_EPG_SUBNET_RESPONSE['totalCount']) == 0:
            print(colour.DARKCYAN + IP + ' added to ' + EPG_NAME + ' under L3Out ' + L3OUT_NAME + colour.END)
        else:
            print(colour.RED + 'Failed to add ' + IP + 'to :' + EPG_NAME + ' under L3Out ' + L3OUT_NAME + colour.END)
            print(colour.RED + 'Error: ' + post_response.text + colour.END)
    except:
        exit(colour.RED + 'Error Posting JSON: ' + str(ADD_SUBNET_L3OUT_JSON) + colour.END)


def EXTERNAL_EPG_ADD(BASE_URL, APIC_COOKIE, TENANT, L3OUT_NAME, EPG_NAME, HEADERS):

	ADD_EPG_L3OUT_URL = BASE_URL + 'node/mo/uni/tn-{0}/out-{1}/instP-{2}.json'.format(TENANT, L3OUT_NAME, EPG_NAME)
	ADD_EPG_L3OUT_JSON = {"l3extInstP":{"attributes":{"name":EPG_NAME,"status":"created"},"children":[]}}
	
	try:
		post_response = requests.post(ADD_EPG_L3OUT_URL, cookies=APIC_COOKIE, data=json.dumps(ADD_EPG_L3OUT_JSON), headers=HEADERS, verify=False)
		EXTERNAL_EPG_RESPONSE = json.loads(post_response.text)

		if int(EXTERNAL_EPG_RESPONSE['totalCount']) == 0:
			print(colour.DARKCYAN + EPG_NAME + ' added to L3OUT: ' + L3OUT_NAME + colour.END)
		else:
			print(colour.RED + 'Failed to add ' + EPG_NAME + 'to ' + L3OUT_NAME + colour.END)
			print(colour.RED + 'Error: ' + post_response.text + colour.END)
	except:
		exit(colour.RED + 'Error Posting JSON: ' + str(ADD_EPG_L3OUT_JSON) + colour.END)
				

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "-verbose", help="Increase output verbosity", action="store_true")
    args = parser.parse_args()
    if args.v:
	    print('\nDebugging Enabled\n')
    ERROR = False
    HEADERS = {'content-type': 'application/json'}
    SANDBOX = 'https://sandboxapicdc.cisco.com/api/'
    LAB = ''
    DC1 = ''
    DC2 = ''
    TENANT = 'common'
    DC = raw_input('DC: (DC1/DC2/LAB) ').upper()
    USER_DETAILS = USERNAME_PASSWORD()
    APIC_USERNAME = USER_DETAILS[0]
    APIC_PASSWORD = USER_DETAILS[1]

    # Select DC to to run script against
    if DC.upper() == 'DC1':
        BASE_URL = DC1
    elif DC.upper() == 'DC2':
        BASE_URL = DC2
    elif DC.upper() == 'SANDBOX':
        BASE_URL = SANDBOX
    elif DC.upper() == 'LAB':
        BASE_URL = LAB
    else:
        print('\nUnknown location selected. please choose from the following:')
        print('DC1 | DC2 | LAB | SANDBOX')
        exit()


    #Open Excel and build data
    PY_WS = OPEN_EXCEL(BASE_URL, DC1, DC2, LAB, SANDBOX)
    EXCEL_MUNGER(PY_WS)
    RULE_LIST = EXCEL_MUNGER(PY_WS)

    # Validate EPG name follows naming convention.

    EXCEL_FORMAT_VALIDATION(RULE_LIST, args)

    # Validate list contains IPv4 Addressing
    time.sleep(1)
    print(colour.BOLD + '\nValidating IP addresses' + colour.END)
    print(colour.BOLD + '-----------------------------\n' + colour.END)
    for addresses in RULE_LIST:
        if len(addresses['CONSUMER_IP']) >= 1:
            for subnets in addresses['CONSUMER_IP']:
                try:
                    network = ipaddress.IPv4Network(unicode(subnets))
                except ValueError:
                    ERROR = True
                    if args.v:
                        print(colour.RED + 'Error 9 - Not able to validate consumer IP as a valid IP address' + colour.END)
        if len(addresses['PROVIDER_IP']) >= 1:
            for subnets in addresses['PROVIDER_IP']:
                try:
                    network = ipaddress.IPv4Network(unicode(subnets))
                except ValueError:
                    ERROR = True
                    if args.v:
                        print(colour.RED + 'Error 10 - Not able to validate provider IP as a valid IP address' + colour.END)

    if ERROR:
        exit(colour.RED + 'Errors found in IP validation' + colour.END)
    else:
        print('IP validation successful')

    # Login to fabric
    print(colour.BOLD + '\nConnecting to APIC' + colour.END)
    print(colour.BOLD + '-----------------------------\n' + colour.END)
    APIC_COOKIE = APIC_LOGIN(BASE_URL, APIC_USERNAME, APIC_PASSWORD, HEADERS)
    # Search for L3out and build URL to add IP's
    print(colour.BOLD + '\nValidating L3Out Names' + colour.END)
    print(colour.BOLD + '-----------------------------\n' + colour.END)
    time.sleep(1)
    L3OUT_LIST = []

    for rules in RULE_LIST:
        if rules['CONSUMER_L3OUT'] == 'INTERNAL':
            pass
        else:
            L3OUT_NAME = rules['CONSUMER_L3OUT']
            L3OUT_SEARCH_RESPONSE = L3OUT_SEARCH(BASE_URL, APIC_COOKIE,TENANT, L3OUT_NAME, HEADERS)
            if int(L3OUT_SEARCH_RESPONSE[0]['totalCount']) == 1:
                if rules['CONSUMER_L3OUT'] == L3OUT_SEARCH_RESPONSE[0]['imdata'][0]['l3extOut']['attributes']['name']:
                    pass
                else:
                    ERROR = True
                    if args.v:
                        print(colour.RED + 'Error 11 - Unable to pull back name for Consumer L3Out' + colour.END)
            else:
                L3OUT_LIST.append(L3OUT_NAME)
                ERROR = True
                if args.v:
                    print(colour.RED + 'Error 12 - Unable to pull back name for Consumer L3Out' + colour.END)

    for rules in RULE_LIST:
        if rules['PROVIDER_L3OUT'] == 'INTERNAL':
            pass
        else:
            L3OUT_NAME = rules['PROVIDER_L3OUT']
            L3OUT_SEARCH_RESPONSE = L3OUT_SEARCH(BASE_URL, APIC_COOKIE,TENANT, L3OUT_NAME, HEADERS)
            if int(L3OUT_SEARCH_RESPONSE[0]['totalCount']) == 1:
                if rules['PROVIDER_L3OUT'] == L3OUT_SEARCH_RESPONSE[0]['imdata'][0]['l3extOut']['attributes']['name']:
                    pass
                else:
                    ERROR = True
                    if args.v:
                        print(colour.RED + 'Error 13 - Unable to pull back name for Provider L3Out' + colour.END)

            else:
                L3OUT_LIST.append(L3OUT_NAME)
                ERROR = True
                if args.v:
                    print(colour.RED + 'Error 14 - Unable to pull back name for Provider L3Out' + colour.END)


    L3OUT_SET = set(L3OUT_LIST)
    for l3out in L3OUT_SET:
        print(colour.YELLOW + 'L3Out: ' + l3out + ' Does not exist, please check naming.' + colour.END)
    L3OUT_LIST = []

    if ERROR:
        exit(colour.RED + 'Errors found in L3Out validation' + colour.END)
    else:
        print('L3Out validation successful')

    # Check if IP already exists in Same L3Out or same VRF
    print(colour.BOLD + '\nChecking if IP currently exists within VRF' + colour.END)
    print(colour.BOLD + '-----------------------------\n' + colour.END)
    time.sleep(1)
    # Get L3out VRF
    for rules in RULE_LIST:
		print(colour.BOLD + 'Checking subnets for line: ' + str(rules['LINE']) +'\n' + colour.END)
		if rules['CONSUMER_L3OUT'] != 'INTERNAL' and rules['CONSUMER_EPG'] != 'BLANK':
			L3OUT_NAME = rules['CONSUMER_L3OUT']
			L3OUT_SEARCH_RESPONSE = L3OUT_SEARCH(BASE_URL, APIC_COOKIE,TENANT, L3OUT_NAME, HEADERS)
			L3OUT_DATA = L3OUT_SEARCH_RESPONSE[1]['imdata']
			L3OUT_SUBNETS = []
			# Loop througj the VRF pull out all other L3Outs and add any l3extsubnet to a list
			for key in L3OUT_DATA:
				if key.keys() == [u'l3extRsEctx']:
					VRF_DN = key['l3extRsEctx']['attributes']['tDn']
					VRF_SEARCH_RESPONSE = VRF_SEARCH(BASE_URL, APIC_COOKIE, VRF_DN, HEADERS)
					for vrf_l3o in VRF_SEARCH_RESPONSE['imdata']:
						if vrf_l3o.keys() == [u'fvRtEctx']:
							L3OUT_DN = vrf_l3o['fvRtEctx']['attributes']['tDn']
							SUBNET_SEARCH_RESPONSE = SUBNET_SEARCH(BASE_URL, APIC_COOKIE, L3OUT_DN, HEADERS)
							for subnets in SUBNET_SEARCH_RESPONSE['imdata']:
								L3OUT_SUBNETS.append(subnets['l3extSubnet']['attributes']['ip'])
								EXISTING_SUBNET = subnets['l3extSubnet']['attributes']['ip']
								EXISTING_L3OUT = subnets['l3extSubnet']['attributes']['dn'].split('/')[2][4:]
								EXISTING_EPG = subnets['l3extSubnet']['attributes']['dn'].split('/')[3][6:]
								SCOPE = subnets['l3extSubnet']['attributes']['scope'].split(',')
								if EXISTING_SUBNET in rules['CONSUMER_IP']:
									if 'import-security' in SCOPE:
										print(colour.YELLOW + EXISTING_SUBNET + ' already exists within ' + EXISTING_L3OUT + ' under EPG ' + EXISTING_EPG + ' no subnet configuration for this epg will be pushed.' + colour.END)
										ERROR = True
										if args.v:
											print(colour.RED + 'Error 15 - Consumer IP Subnet already exists within VRF' + colour.END)
										rules['CONSUMER_IP'].remove(EXISTING_SUBNET)
								else:
									pass

			if len(rules['CONSUMER_IP']) >= 1:
				print('The Following subnets will be added to the EPG: ' + rules['CONSUMER_EPG'])
				print(str(unicode(rules['CONSUMER_IP'])) + '\n')
			else:
				print('No subnets will be added to EPG: ' + rules['CONSUMER_EPG'] + '\n')
				
		if rules['PROVIDER_L3OUT'] != 'INTERNAL' and rules['PROVIDER_EPG'] != 'BLANK':
			L3OUT_NAME = rules['PROVIDER_L3OUT']
			L3OUT_SEARCH_RESPONSE = L3OUT_SEARCH(BASE_URL, APIC_COOKIE,TENANT, L3OUT_NAME, HEADERS)
			L3OUT_DATA = L3OUT_SEARCH_RESPONSE[1]['imdata']
			L3OUT_SUBNETS = []
			# Loop througj the VRF pull out all other L3Outs and add any l3extsubnet to a list
			for key in L3OUT_DATA:
				if key.keys() == [u'l3extRsEctx']:
					VRF_DN = key['l3extRsEctx']['attributes']['tDn']
					VRF_SEARCH_RESPONSE = VRF_SEARCH(BASE_URL, APIC_COOKIE, VRF_DN, HEADERS)
					for vrf_l3o in VRF_SEARCH_RESPONSE['imdata']:
						if vrf_l3o.keys() == [u'fvRtEctx']:
							L3OUT_DN = vrf_l3o['fvRtEctx']['attributes']['tDn']
							SUBNET_SEARCH_RESPONSE = SUBNET_SEARCH(BASE_URL, APIC_COOKIE, L3OUT_DN, HEADERS)
							for subnets in SUBNET_SEARCH_RESPONSE['imdata']:
								L3OUT_SUBNETS.append(subnets['l3extSubnet']['attributes']['ip'])
								EXISTING_SUBNET = subnets['l3extSubnet']['attributes']['ip']
								EXISTING_L3OUT = subnets['l3extSubnet']['attributes']['dn'].split('/')[2][4:]
								EXISTING_EPG = subnets['l3extSubnet']['attributes']['dn'].split('/')[3][6:]
								SCOPE = subnets['l3extSubnet']['attributes']['scope'].split(',')
								if EXISTING_SUBNET in rules['PROVIDER_IP']:
									if 'import-security' in SCOPE:
										print(colour.YELLOW + EXISTING_SUBNET + ' already exists within ' + EXISTING_L3OUT + ' under EPG ' + EXISTING_EPG + ' no subnet configuration for this epg will be pushed.' + colour.END)
										ERROR = True
										if args.v:
											print(colour.RED + 'Error 16 - Provider IP Subnet already exists within VRF' + colour.END)
										rules['PROVIDER_IP'].remove(EXISTING_SUBNET)
								else:
									pass

			if len(rules['PROVIDER_IP']) >= 1:
				print('The Following subnets will be added to the EPG: ' + rules['PROVIDER_EPG'])
				print(str(unicode(rules['PROVIDER_IP'])) + '\n')
			else:
				print('No subnets will be added to EPG: ' + rules['PROVIDER_EPG'] + '\n')
				
	# Search for VIPs
    print(colour.BOLD + '\nChecking if any EPGs are for VIPS' + colour.END)
    print(colour.BOLD + '-----------------------------\n' + colour.END)
    time.sleep(1)		
    for rules in RULE_LIST:
        if rules['PROVIDER_EPG'].split('_')[0].endswith('VS') and rules['PROVIDER_L3OUT'].endswith('DCI_L3O'):
            for subnets in rules['PROVIDER_IP']:
                if len(subnets.split('/')) != 0:
                    subnet = subnets.split('/')[0]
                else:
                    subnet = subnets
                if not ipaddress.ip_address(unicode(subnet)).is_private:
                    print('\nEPG ' + rules['PROVIDER_EPG'] + ' contains a public address.')
                    print(unicode(subnets) + ' will be imported under the DCI and exported under the INET L3Outs')
				
                elif ipaddress.ip_address(unicode(subnet)).is_private:
                    print('\nEPG ' + rules['PROVIDER_EPG'] + ' contains a private address.')
                    print(unicode(subnets) + ' will be imported under the DCI L3Out')
					
	
			
			
    if ERROR:
        ERRORS()
		
    # End of pre checks
    print('\nPre Checks completed.')
    print('Continue to provisioning?\n')
    USER_CONFIRM = raw_input('Y/N ').upper()
    print USER_CONFIRM
    if USER_CONFIRM != 'Y':
        exit('\nExiting without provisioning.')
    else:
        pass

    # --------------------------------------------------------------------------#
    # Begin Configuration
    # --------------------------------------------------------------------------#

    for rules in RULE_LIST:
        L3OUT_CONSUME_EPG_CREATED = False
        L3OUT_PROVIDE_EPG_CREATED = False
        print(colour.BOLD + '\nAdding EPGs & Subnets for line: ' + str(rules['LINE']) + colour.END)
        if rules['CONSUMER_L3OUT'] != 'INTERNAL' and rules['CONSUMER_EPG'] != 'BLANK':
            EPG_NAME = rules['CONSUMER_EPG']
            L3OUT_NAME = rules['CONSUMER_L3OUT']
            EXTERNAL_EPG_SEARCH_RESPONSE = EXTERNAL_EPG_SEARCH(BASE_URL, APIC_COOKIE, TENANT, L3OUT_NAME, EPG_NAME, HEADERS)
            if int(EXTERNAL_EPG_SEARCH_RESPONSE['totalCount']) == 1:
                print(colour.YELLOW + '\nEPG: ' + EPG_NAME + ' already exists under ' + L3OUT_NAME + ' and wont be created' + colour.END)
                L3OUT_CONSUME_EPG_CREATED = True
            if not L3OUT_CONSUME_EPG_CREATED:
                print('\nAdding External EPG: ' + EPG_NAME + ' TO L3Out: ' + L3OUT_NAME)
                EXTERNAL_EPG_ADD(BASE_URL, APIC_COOKIE, TENANT, L3OUT_NAME, EPG_NAME, HEADERS)
            # Add subnets to external EPG
            if len(rules['CONSUMER_IP']) != 0:
                print('\nAdding Subnets to External EPG: ' )
                time.sleep(1)
                for IP in rules['CONSUMER_IP']:
                    SCOPE = 'import-security'
                    EXTERNAL_EPG_SUBNET_ADD(BASE_URL, APIC_COOKIE, TENANT, L3OUT_NAME, EPG_NAME, HEADERS, IP, SCOPE)
		
        if rules['PROVIDER_L3OUT'] != 'INTERNAL' and rules['PROVIDER_EPG'] != 'BLANK':
            EPG_NAME = rules['PROVIDER_EPG']
            L3OUT_NAME = rules['PROVIDER_L3OUT']
            EXTERNAL_EPG_SEARCH_RESPONSE = EXTERNAL_EPG_SEARCH(BASE_URL, APIC_COOKIE, TENANT, L3OUT_NAME, EPG_NAME, HEADERS)
            if int(EXTERNAL_EPG_SEARCH_RESPONSE['totalCount']) == 1:
                print(colour.YELLOW + '\nEPG: ' + EPG_NAME + ' already exists under ' + L3OUT_NAME + ' and wont be created' + colour.END)
                L3OUT_PROVIDE_EPG_CREATED = True
            if not L3OUT_PROVIDE_EPG_CREATED:
                print('\nAdding External EPG: ' + EPG_NAME + ' TO L3Out: ' + L3OUT_NAME)
                EXTERNAL_EPG_ADD(BASE_URL, APIC_COOKIE, TENANT, L3OUT_NAME, EPG_NAME, HEADERS)
			# Add subnets to external EPG
            if len(rules['PROVIDER_IP']) != 0:
                print('\nAdding Subnets to External EPG: ')
                time.sleep(1)
                for IP in rules['PROVIDER_IP']:
                    if len(IP.split('/')) != 0:
                        subnet = IP.split('/')[0]
                    else:
                        subnet = IP
                    # Check for VS EPGs
                    if rules['PROVIDER_EPG'].split('_')[0].endswith('VS') and rules['PROVIDER_L3OUT'].endswith('DCI_L3O'):

                        if not ipaddress.ip_address(subnet).is_private:
                            # Import Under DCI
                            SCOPE = 'import-rtctrl,import-security'
                            L3OUT_NAME = rules['PROVIDER_L3OUT']
                            EPG_NAME = rules['PROVIDER_EPG']
                            EXTERNAL_EPG_SUBNET_ADD(BASE_URL, APIC_COOKIE, TENANT, L3OUT_NAME, EPG_NAME, HEADERS, IP, SCOPE)
      							
                            # Export Under Inet
                            SCOPE = 'export-rtctrl'
                            # Build L3out name for Inet L3Out
							# Temp fix for BLUE INET
                            if rules['PROVIDER_L3OUT'].split('-')[0] == 'BLUE':
                                L3OUT_NAME = rules['PROVIDER_L3OUT'].split('-')[0] + '-' + DC + '-INET_L3O'
                            else:
                                L3OUT_NAME = rules['PROVIDER_L3OUT'].split('-')[0] + '-INET_L3O'
								
                            EPG_NAME = rules['PROVIDER_L3OUT'].split('_')[0] + '-ROUTING_EPG'
                            EXTERNAL_EPG_SUBNET_ADD(BASE_URL, APIC_COOKIE, TENANT, L3OUT_NAME, EPG_NAME, HEADERS, IP, SCOPE)
							
                        if ipaddress.ip_address(unicode(subnet)).is_private:
                            # Import Under DCI 
                            L3OUT_NAME = rules['PROVIDER_L3OUT']
                            EPG_NAME = rules['PROVIDER_EPG']
                            SCOPE = 'import-rtctrl,import-security'
                            EXTERNAL_EPG_SUBNET_ADD(BASE_URL, APIC_COOKIE, TENANT, L3OUT_NAME, EPG_NAME, HEADERS, IP, SCOPE)
					
                    else:
                        L3OUT_NAME = rules['PROVIDER_L3OUT']
                        EPG_NAME = rules['PROVIDER_EPG']
                        SCOPE = 'import-security'
                        EXTERNAL_EPG_SUBNET_ADD(BASE_URL, APIC_COOKIE, TENANT, L3OUT_NAME, EPG_NAME, HEADERS, IP, SCOPE)


if __name__ == "__main__":
    main()
