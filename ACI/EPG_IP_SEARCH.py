import requests, json, time
from getpass import getpass

# Ignore SSL Errors
requests.packages.urllib3.disable_warnings()

def APIC_LOGIN(BASE_URL, APIC_USERNAME, APIC_PASSWORD, HEADERS ):
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
        print('Unable to connect to APIC. Please check your credentials')
        exit()

    return APIC_COOKIE

def INTERNAL_EPG_SEARCH(BASE_URL, APIC_COOKIE, EPG_NAME, HEADERS):

    EPG_SEARCH_URL = BASE_URL + 'node/class/fvAEPg.json?query-target-filter=and(eq(fvAEPg.name,"{0}"))'.format(EPG_NAME)
    try:
        get_response = requests.get(EPG_SEARCH_URL, cookies=APIC_COOKIE, headers=HEADERS, verify=False)
        INTERNAL_EPG_SEARCH_RESPONSE = json.loads(get_response.text)
        return INTERNAL_EPG_SEARCH_RESPONSE

    except:
        print('Failed to search for EPG')
        exit()

def INTERNAL_ENDPOINTS(BASE_URL, APIC_COOKIE, TENANT, APP_PROF, EPG_NAME, HEADERS):
    INTERNAL_ENDPOINTS_LIST = []

    try:
		GET_URL = BASE_URL + 'node/mo/uni/tn-{0}/ap-{1}/epg-{2}.json?query-target=children'.format(TENANT, APP_PROF, EPG_NAME)
		GET_RESPONSE = requests.get(GET_URL, cookies=APIC_COOKIE, headers=HEADERS, verify=False)
		PROVIDER_EPG_RESPONSE = json.loads(GET_RESPONSE.text)
		# print(PROVIDER_EPG_RESPONSE)
		for epgs in PROVIDER_EPG_RESPONSE['imdata']:
			if epgs.keys() == [u'fvCEp']:
				INTERNAL_ENDPOINTS_LIST.append(epgs['fvCEp']['attributes']['ip'].encode() + '/32')
		return INTERNAL_ENDPOINTS_LIST			

    except:
		print('Failed to get EPG IPs')
		exit()


def USERNAME_PASSWORD():
    print '\nPlease enter adm credentials.'
    ADM_USER = raw_input("\nEnter Username: ")
    ADM_PASS = getpass("\nEnter Password: ")

    return ADM_USER, ADM_PASS

def main():

    HEADERS = {'content-type': 'application/json'}
    DC = raw_input('DC: (DC1/DC2) ')
    USER_DETAILS = USERNAME_PASSWORD()
    APIC_USERNAME = USER_DETAILS[0]
    APIC_PASSWORD = USER_DETAILS[1]
    ENDPOINTS = []
    EPG_NAME = raw_input('\nEnter EPG Name: ')
    SANDBOX = 'https://sandboxapicdc.cisco.com/api/'
    LAB = ''
    DC1 = ''
    DC2 = ''
    

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
        print('\nUnknown location selected. please chose from the following:')
        print('DC1 | DC2 | LAB | SANDBOX')
        exit()


    APIC_COOKIE = APIC_LOGIN(BASE_URL, APIC_USERNAME, APIC_PASSWORD, HEADERS)
    INTERNAL_EPG_SEARCH_RESPONSE = INTERNAL_EPG_SEARCH(BASE_URL, APIC_COOKIE, EPG_NAME, HEADERS)
    TENANT = INTERNAL_EPG_SEARCH_RESPONSE['imdata'][0]['fvAEPg']['attributes']['dn'].split('/')[1][3:]
    APP_PROF = INTERNAL_EPG_SEARCH_RESPONSE['imdata'][0]['fvAEPg']['attributes']['dn'].split('/')[2][3:]
    INTERNAL_ENDPOINTS_LIST = INTERNAL_ENDPOINTS(BASE_URL, APIC_COOKIE, TENANT, APP_PROF, EPG_NAME, HEADERS)
    print(str(INTERNAL_ENDPOINTS_LIST))
   

    #Check if EPG was located
   # i#f int(INTERNAL_EPG_SEARCH_RESPONSE['totalCount']) == 1:
   #     for attributes in INTERNAL_EPG_SEARCH_RESPONSE['imdata']:
   #         if attributes
   # else:
   #     exit('EPG Not located.')

   #else:

if __name__ == "__main__":
    main()