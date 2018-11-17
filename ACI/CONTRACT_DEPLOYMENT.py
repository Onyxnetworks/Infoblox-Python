import openpyxl
import requests, json, time
import getpass
import signal
import socket
import binascii
import os
import sys
from prettytable import PrettyTable
from netaddr import IPNetwork,IPAddress
from getpass import getpass
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

# Function used to compare two lists and return missing values.
def LIST_COMPARE(a, b):
    return [[x for x in a if x not in b]]

# Function to exit script on errors.
def ERRORS():
    print(colour.RED + 'Errors found. Exiting script.' + colour.END)
    time.sleep(2)
    exit()

#
def BANNER():
    print'>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>'
    print 'Cisco ACI'
    print 'Contract Provisioning Script '
    print'>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>'
    time.sleep(1)


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
        exit(colour.RED + 'Unable to open {}, please check file name and path is correct'.format(EXCEL_NAME) + colour.END)


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
        exit(colour.RED + 'Unable to connect to APIC. Please check your credentials' + colour.END)

    return APIC_COOKIE

# Function to build list of required rules
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
            CONTRACT_NAME = row[2].value.upper()
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
            else:
                pass
            if row[6].value:
                PROVIDER_IP_LIST = row[6].value.split()
            else:
                pass
            if row[3].value:
                SERVICE_LIST = row[3].value.upper().split()
            if row[7].value:
                CONSUMER_L3OUT = row[7].value.upper()
            else:
                CONSUMER_L3OUT = 'INTERNAL'
            if row[4].value:
                PROVIDER_L3OUT = row[4].value.upper()
            else:
                PROVIDER_L3OUT = 'INTERNAL'

            INDEX += 1
            RULE_LIST.append({'LINE': INDEX, 'PROVIDER_L3OUT': PROVIDER_L3OUT, 'CONSUMER_L3OUT': CONSUMER_L3OUT, 'NAME': CONTRACT_NAME, 'CONSUMER_EPG': CONSUMER_EPG, 'CONSUMER_IP': CONSUMER_IP_LIST, 'PROVIDER_EPG': PROVIDER_EPG, 'PROVIDER_IP': PROVIDER_IP_LIST, 'SERVICE': SERVICE_LIST})

        return RULE_LIST

    except:
        exit(colour.RED + 'Error Reading from excel. Please check all columns are populated\n' + colour.END)

# Function to validate the formating of rules
def EXCEL_FORMAT_VALIDATION(RULE_LIST, args):
    DISPLAY_LIST = []
    TENANT_LIST = ['RED', 'GREEN', 'BLUE']
    ERROR = False

    # Validate Contract Name formatting
    print(colour.BOLD + '\nValidating Contract names in Workbook.' + colour.END)
    print(colour.BOLD + '-----------------------------\n' + colour.END)

    time.sleep(1)
    try:
        for rules in RULE_LIST:
            if (len(rules['NAME'].split('_'))) > 2:
                DISPLAY_LIST.append(rules['NAME'])
                ERROR = True
                if args.v:
                    print(colour.RED + 'Error 1 - Too many underscores in Contract Name' + colour.END)
            elif rules['NAME'].split('_')[1].upper() != 'GCTR':
                DISPLAY_LIST.append(rules['NAME'])
                ERROR = True
                if args.v:
                    print(colour.RED + 'Error 2 - Contract name should end _GCTR' + colour.END)
            elif rules['NAME'].split('-')[0].upper() not in TENANT_LIST:
                DISPLAY_LIST.append(rules['NAME'])
                ERROR = True
                if args.v:
                    print(colour.RED + 'Error 3 - Prefix of Contract not in the tenant list (RED,GREEN,BLUE)' + colour.END)

            else:
                pass


        DISPLAY_SET = set(DISPLAY_LIST)
        for contracts in DISPLAY_SET:
            print(colour.YELLOW + 'Contract "' + contracts + '" does not conform to the naming standard' + colour.END)
        DISPLAY_LIST = []

    except:
        exit(colour.RED + 'Errors validating Contract names' + colour.END)

    if ERROR:
        ERRORS()
    else:
        time.sleep(2)
        print('Contract formatting validated successfully')


    print(colour.BOLD + '\nValidating EPG names in Workbook.' + colour.END)
    print(colour.BOLD + '-----------------------------\n' + colour.END)

    time.sleep(1)

    for rules in RULE_LIST:
        if rules['CONSUMER_EPG'] != 'BLANK':
            if len(rules['CONSUMER_EPG'].split('_')) > 2:
                DISPLAY_LIST.append(rules['CONSUMER_EPG'])
                ERROR = True
                if args.v:
                    print(colour.RED + 'Error 4 - Too many underscores in Consumer EPG' + colour.END)
            elif rules['CONSUMER_EPG'].split('_')[1].upper() != 'EPG':
                DISPLAY_LIST.append(rules['CONSUMER_EPG'])
                ERROR = True
                if args.v:
                    print(colour.RED + 'Error 5 - Consumer EPG should end _EPG' + colour.END)
            elif rules['CONSUMER_EPG'].split('-')[0].upper() not in TENANT_LIST:
                DISPLAY_LIST.append(rules['CONSUMER_EPG'])
                ERROR = True
                if args.v:
                    print(colour.RED + 'Error 6 - Prefix of EPG not in the tenant list (RED,GREEN,BLUE)' + colour.END)
            else:
                pass
        if rules['PROVIDER_EPG'] != 'BLANK':
            if len(rules['PROVIDER_EPG'].split('_')) > 2:
                DISPLAY_LIST.append(rules['PROVIDER_EPG'])
                ERROR = True
                if args.v:
                    print(colour.RED + 'Error 7 - Too many underscores in Consumer EPG' + colour.END)
            elif rules['PROVIDER_EPG'].split('_')[1].upper() != 'EPG':
                DISPLAY_LIST.append(rules['PROVIDER_EPG'])
                ERROR = True
                if args.v:
                    print(colour.RED + 'Error 8 - Provider EPG should end _EPG' + colour.END)
            elif rules['PROVIDER_EPG'].split('-')[0].upper() not in TENANT_LIST:
                DISPLAY_LIST.append(rules['PROVIDER_EPG'])
                ERROR = True
                if args.v:
                    print(colour.RED + 'Error 9 - Prefix of EPG not in the tenant list (RED,GREEN,BLUE)' + colour.END)
            else:
                pass


        DISPLAY_SET = set(DISPLAY_LIST)
        for contracts in DISPLAY_SET:
            print(colour.YELLOW + 'EPG "' + contracts + '" does not conform to the naming standard' + colour.END)
        DISPLAY_LIST = []


    if ERROR:
        ERRORS()
    else:
        time.sleep(2)
        print('EPG formatting validated successfully')


    print(colour.BOLD + '\nValidating Contract and EPG locality.' + colour.END)
    print(colour.BOLD + '-----------------------------\n' + colour.END)

    time.sleep(1)
    for rules in RULE_LIST:

        if rules['CONSUMER_EPG'] != 'BLANK':
            if rules['CONSUMER_EPG'].split('-')[0].upper() != rules['NAME'].split('-')[0].upper():
                DISPLAY_LIST.append(rules['CONSUMER_EPG'])
                ERROR = True
                if args.v:
                    print(colour.RED + 'Error 10 - Prefix of Consumer EPG: ' + rules['CONSUMER_EPG'] + ' and Contract ' + rules['NAME'] + ' not in the same tenant' + colour.END)
        if rules['PROVIDER_EPG'] != 'BLANK':
            if rules['PROVIDER_EPG'].split('-')[0].upper() != rules['NAME'].split('-')[0].upper():
                DISPLAY_LIST.append(rules['PROVIDER_EPG'])
                ERROR = True
                if args.v:
                    print(colour.RED + 'Error 11 - Prefix of Provider EPG: ' + rules['PROVIDER_EPG'] + ' and Contract ' + rules['NAME'] + ' not in the same tenant' + colour.END)
        else:
            pass

    DISPLAY_SET = set(DISPLAY_LIST)
    for contracts in DISPLAY_SET:
        print(colour.YELLOW + 'Error ' + contracts + ' and Contract named for different Tenants.' + colour.END)
    DISPLAY_LIST = []

    if ERROR:
        ERRORS()
    else:
        time.sleep(2)
        print('EPG formatting validated successfully')

    print(colour.BOLD + '\nValidating Services in Workbook.' + colour.END)
    print(colour.BOLD + '-----------------------------\n' + colour.END)

    time.sleep(1)
    for rules in RULE_LIST:
        for services in rules['SERVICE']:
            PROTOCOLS = ['TCP', 'UDP']
            try:
                value = int(services.split('-')[1])
            except:
                exit(colour.RED  + 'Service port not correct format for ' + services + ' on line ' + str(rules['LINE']) + colour.END)
            if services.split('-')[0] not in PROTOCOLS:
                print('Error in TCP or UDP not specified for service ' + services)
                ERROR = True
                if args.v:
                    print(colour.RED + 'Error 12 - Prefix not equal to TCP or UDP for service ' + services)
            elif int(services.split('-')[1]) == 0:
                print('Error Port out of range ' + services)
                ERROR = True
                if args.v:
                    print(colour.RED + 'Error 13 - ' + services + ' not in range 1-65535')
            elif int(services.split('-')[1]) not in range(1, 65536):
                print('Error Port out of range ' + services)
                ERROR = True
                if args.v:
                    print(colour.RED + 'Error 14 - ' + services + ' not in range 1-65535')
            elif len(services.split('-')) == 3:
                if int(services.split('-')[2]) not in range(1, 65536):
                    print('Error Port out of range ' + services)
                    ERROR = True
                    if args.v:
                        print(colour.RED + 'Error 13 - ' + services + ' not in range 1-65535')
            else:
                pass
    if ERROR:
            ERRORS()


    else:
        time.sleep(2)
        print('Service formatting validated successfully')


def CONTRACT_SEARCH(BASE_URL, APIC_COOKIE, CONTRACT_NAME, HEADERS):

    CONTRACT_SEARCH_URL = BASE_URL + 'node/class/vzBrCP.json?query-target-filter=and(eq(vzBrCP.name,"{0}"))'.format(CONTRACT_NAME)
    try:
        get_response = requests.get(CONTRACT_SEARCH_URL, cookies=APIC_COOKIE, headers=HEADERS, verify=False)
        CONTRACT_SEARCH_RESPONSE = json.loads(get_response.text)
        return CONTRACT_SEARCH_RESPONSE

    except:
        exit(colour.RED + 'Failed to search for contracts' + colour.END)


def FILTER_SEARCH(BASE_URL, APIC_COOKIE, FILTER_NAME, HEADERS):
								   
    FILTER_SEARCH_URL = BASE_URL + 'node/class/vzFilter.json?query-target-filter=and(eq(vzFilter.dn,"uni/tn-common/flt-{0}"))'.format(FILTER_NAME)
    try:
        get_response = requests.get(FILTER_SEARCH_URL, cookies=APIC_COOKIE, headers=HEADERS, verify=False)
        FILTER_SEARCH_RESPONSE = json.loads(get_response.text)
        return FILTER_SEARCH_RESPONSE


    except:
        exit(colour.RED + 'Failed to search for filters' + colour.END)


def SUBJECT_SEARCH(BASE_URL, APIC_COOKIE, CONTRACT_NAME, TENANT, CONTRACT_SUBJECT, HEADERS):

    SUBJECT_SEARCH_URL = BASE_URL + 'node/mo/uni/tn-{0}/brc-{1}/subj-{2}.json?query-target=children'.format(TENANT, CONTRACT_NAME, CONTRACT_SUBJECT)
    try:
        get_response = requests.get(SUBJECT_SEARCH_URL, cookies=APIC_COOKIE, headers=HEADERS, verify=False)
        SUBJECT_SEARCH_RESPONSE = json.loads(get_response.text)
        return SUBJECT_SEARCH_RESPONSE


    except:
        exit(colour.RED + 'Failed to search for subjects' + colour.END)


def INTERNAL_EPG_SEARCH(BASE_URL, APIC_COOKIE, EPG_NAME, HEADERS):

    EPG_SEARCH_URL = BASE_URL + 'node/class/fvAEPg.json?query-target-filter=and(eq(fvAEPg.name,"{0}"))'.format(EPG_NAME)
    try:
        get_response = requests.get(EPG_SEARCH_URL, cookies=APIC_COOKIE, headers=HEADERS, verify=False)
        INTERNAL_EPG_SEARCH_RESPONSE = json.loads(get_response.text)
        return INTERNAL_EPG_SEARCH_RESPONSE

    except:
        exit(colour.RED + 'Failed to search for EPG' + colour.END)


def EXTERNAL_EPG_SEARCH(BASE_URL, APIC_COOKIE, L3OUT_NAME, EPG_NAME, HEADERS):
    EPG_SEARCH_URL = BASE_URL + 'node/class/l3extInstP.json?query-target-filter=and(wcard(l3extInstP.dn,"/out-{0}/instP-{1}"))'.format(L3OUT_NAME, EPG_NAME)
    try:
        get_response = requests.get(EPG_SEARCH_URL, cookies=APIC_COOKIE, headers=HEADERS, verify=False)
        EXTERNAL_EPG_SEARCH_RESPONSE = json.loads(get_response.text)
        return EXTERNAL_EPG_SEARCH_RESPONSE


    except:
        exit(colour.RED + 'Failed to search for EPG' + colour.END)


def L3OUT_SEARCH(BASE_URL, APIC_COOKIE, L3OUT_NAME, HEADERS):

    L3OUT_SEARCH_URL = BASE_URL + 'node/mo/uni/tn-common/out-{0}.json?query-target=self'.format(L3OUT_NAME)
    try:
        get_response = requests.get(L3OUT_SEARCH_URL, cookies=APIC_COOKIE, headers=HEADERS, verify=False)
        L3OUT_SEARCH_RESPONSE = json.loads(get_response.text)
        return L3OUT_SEARCH_RESPONSE


    except:
        exit(colour.RED + 'Failed to search for EPG'  + colour.END)


def FILTER_CREATE(FILTER_SET, BASE_URL, APIC_COOKIE, HEADERS):
    # Loop through filter set to build filters
    for filters in FILTER_SET:
        FILTER_NAME = filters.encode()
        FILTER_PROTOCOL = filters.split('-')[0].encode().lower()
        FILTER_DEST_PORT_FROM = filters.split('-')[1].encode()
        if len(filters.split('-')) == 3:
            FILTER_DEST_PORT_TO = filters.split('-')[2].encode()
        else:
            FILTER_DEST_PORT_TO = filters.split('-')[1].encode()
        FILTER_TEMPLATE_URL = BASE_URL + 'node/mo/uni/tn-common/flt-{0}.json'.format(FILTER_NAME)
        FILTER_TEMPLATE_JSON = {"vzFilter": {"attributes": {"name": FILTER_NAME, "status": "created"},"children": [{"vzEntry": {"attributes": {"name": FILTER_NAME, "etherT": "ip","prot": FILTER_PROTOCOL,"dFromPort": FILTER_DEST_PORT_FROM,"dToPort": FILTER_DEST_PORT_TO, "status": "created"}, "children": []}}]}}
        try:
            post_response = requests.post(FILTER_TEMPLATE_URL, cookies=APIC_COOKIE,data=json.dumps(FILTER_TEMPLATE_JSON), headers=HEADERS ,verify=False)
            FILTER_CREATE_RESPONSE = json.loads(post_response.text)

            if int(FILTER_CREATE_RESPONSE['totalCount']) == 0:
                print(colour.DARKCYAN + 'Created Filter for ' + FILTER_NAME + colour.END)
            else:
                print(colour.RED + 'Failed to create Filter for:' + FILTER_NAME + colour.END)
                print(colour.RED + 'Error: ' + post_response.text + colour.END)

        except:
            print(colour.RED + 'Error Posting JSON: ' + FILTER_TEMPLATE_JSON + colour.END)


def CONTRACT_CREATE(CONTRACT_SET, BASE_URL, APIC_COOKIE, HEADERS):
    # Loop through contract set and build contracts and subjects
    for contracts in CONTRACT_SET:
        CONTRACT_NAME = contracts
        CONTRACT_DESCRIPTION = ''
        SUBJECT_NAME = CONTRACT_NAME.split('_')[0] + '_SBJ'
        CONTRACT_TAG = 'TEST'
        CONTRACT_TEMPLATE_URL =  BASE_URL + 'node/mo/uni/tn-common/brc-{0}.json'.format(CONTRACT_NAME)
        CONTRACT_TEMPLATE_JSON = {"vzBrCP":{"attributes":{"name": CONTRACT_NAME,"scope":"global","descr": CONTRACT_DESCRIPTION,"status":"created"},"children":[{"vzSubj":{"attributes":{"name":SUBJECT_NAME, "status":"created"},"children":[]}}]}}

        try:
            post_response = requests.post(CONTRACT_TEMPLATE_URL, cookies=APIC_COOKIE, data=json.dumps(CONTRACT_TEMPLATE_JSON),headers=HEADERS, verify=False)
            CONTRACT_CREATE_RESPONSE = json.loads(post_response.text)

            if int(CONTRACT_CREATE_RESPONSE['totalCount']) == 0:
                print(colour.DARKCYAN + 'Created Contract for ' + CONTRACT_NAME + colour.END)
            else:
                print(colour.RED + 'Failed to create Contract for:' + CONTRACT_NAME + colour.END)
                print(colour.RED + 'Error: ' + post_response.text + colour.END)
        except:
            print(colour.RED + 'Error Posting JSON: ', CONTRACT_TEMPLATE_JSON + colour.END)


def FILTER_ATTACH(BASE_URL, APIC_COOKIE, CONTRACT_NAME, CONTRACT_SUBJECT, FILTER, HEADERS):

    CONTRACT_SUBJECT_URL = BASE_URL + 'node/mo/uni/tn-common/brc-{0}/subj-{1}.json'.format(CONTRACT_NAME, CONTRACT_SUBJECT)
    CONTRACT_SUBJECT_JSON = {"vzRsSubjFiltAtt":{"attributes":{"tnVzFilterName":FILTER,"status":"created,modified"},"children":[]}}
    try:
        post_response = requests.post(CONTRACT_SUBJECT_URL, cookies=APIC_COOKIE, data=json.dumps(CONTRACT_SUBJECT_JSON), headers=HEADERS, verify=False)
        CONTRACT_SUBJECT_RESPONSE = json.loads(post_response.text)
        if int(CONTRACT_SUBJECT_RESPONSE['totalCount']) == 0:
            print(colour.DARKCYAN + 'Attached filter: ' + FILTER + ' to Contract: ' + CONTRACT_NAME + colour.END)
        else:
            print(colour.RED + 'Failed to attach filter: ' + FILTER + 'to Contract: ' + CONTRACT_NAME + colour.END)
            print(colour.RED + 'Error: ' + post_response.text + colour.END)

    except:
        print(colour.RED + 'Error Posting JSON: ', CONTRACT_SUBJECT_JSON + colour.END)


def INTERNL_EPG_CONTRACT_CONSUME(BASE_URL, EPG_NAME, CONTRACT_NAME, APIC_COOKIE, HEADERS):

    INTERNAL_EPG_SEARCH_RESPONSE = INTERNAL_EPG_SEARCH(BASE_URL, APIC_COOKIE, EPG_NAME, HEADERS)
    TENANT = INTERNAL_EPG_SEARCH_RESPONSE['imdata'][0]['fvAEPg']['attributes']['dn'].split('/')[1][3:]
    APP_PROFILE = INTERNAL_EPG_SEARCH_RESPONSE['imdata'][0]['fvAEPg']['attributes']['dn'].split('/')[2][3:]
    CONTRACT_ATTACH_URL =  BASE_URL + 'node/mo/uni/tn-{0}/ap-{1}/epg-{2}.json'.format(TENANT, APP_PROFILE, EPG_NAME)
    CONTRACT_ATTACH_JSON = {"fvRsCons": {"attributes": {"tnVzBrCPName": CONTRACT_NAME, "status": "created,modified"}, "children": []}}

    try:
        post_response = requests.post(CONTRACT_ATTACH_URL, cookies=APIC_COOKIE, data=json.dumps(CONTRACT_ATTACH_JSON), headers=HEADERS, verify=False)
        CONTRACT_CONSUME_RESPONSE = json.loads(post_response.text)

        if int(CONTRACT_CONSUME_RESPONSE['totalCount']) == 0:
            print(colour.DARKCYAN + 'Contract:  ' + CONTRACT_NAME + ' Consumed on EPG: ' + EPG_NAME + colour.END)
        else:
            print(colour.RED + 'Failed to consume Contract: ' + CONTRACT_NAME + 'on EPG: ' + EPG_NAME + colour.END)
            print(colour.RED + 'Error: ' + post_response.text + colour.END)
    except:
        print(colour.RED + 'Error Posting JSON: ',  CONTRACT_ATTACH_JSON + colour.END)


def INTERNL_EPG_CONTRACT_PROVIDE(BASE_URL, EPG_NAME, CONTRACT_NAME, APIC_COOKIE, HEADERS):

    INTERNAL_EPG_SEARCH_RESPONSE = INTERNAL_EPG_SEARCH(BASE_URL, APIC_COOKIE, EPG_NAME, HEADERS)
    TENANT = INTERNAL_EPG_SEARCH_RESPONSE['imdata'][0]['fvAEPg']['attributes']['dn'].split('/')[1][3:]
    APP_PROFILE = INTERNAL_EPG_SEARCH_RESPONSE['imdata'][0]['fvAEPg']['attributes']['dn'].split('/')[2][3:]
    CONTRACT_ATTACH_URL =  BASE_URL + 'node/mo/uni/tn-{0}/ap-{1}/epg-{2}.json'.format(TENANT, APP_PROFILE, EPG_NAME)
    CONTRACT_ATTACH_JSON = {"fvRsProv": {"attributes": {"tnVzBrCPName": CONTRACT_NAME, "status": "created,modified"}, "children": []}}

    try:
        post_response = requests.post(CONTRACT_ATTACH_URL, cookies=APIC_COOKIE, data=json.dumps(CONTRACT_ATTACH_JSON), headers=HEADERS, verify=False)
        CONTRACT_PROVIDE_RESPONSE = json.loads(post_response.text)

        if int(CONTRACT_PROVIDE_RESPONSE['totalCount']) == 0:
            print(colour.DARKCYAN + 'Contract:  ' + CONTRACT_NAME + ' Provided on EPG: ' + EPG_NAME + colour.END)
        else:
            print(colour.RED + 'Failed to provide Contract: ' + CONTRACT_NAME + 'on EPG: ' + EPG_NAME + colour.END)
            print(colour.RED + 'Error: ' + post_response.text + colour.END)
    except:
        print(colour.RED + 'Error Posting JSON: ',  CONTRACT_ATTACH_JSON + colour.END)


def EXTERNAL_EPG_CONTRACT_CONSUME(L3OUT_NAME, EPG_NAME, CONTRACT_NAME, BASE_URL, APIC_COOKIE, HEADERS, args):

    # Search for External EPG to build DN.
    EXTERNAL_EPG_SEARCH_RESPONSE = EXTERNAL_EPG_SEARCH(BASE_URL, APIC_COOKIE, L3OUT_NAME, EPG_NAME, HEADERS)

    if int(EXTERNAL_EPG_SEARCH_RESPONSE['totalCount']) == 1:
        TENANT = EXTERNAL_EPG_SEARCH_RESPONSE['imdata'][0]['l3extInstP']['attributes']['dn'].split('/')[1][3:]
        L3OUT = EXTERNAL_EPG_SEARCH_RESPONSE['imdata'][0]['l3extInstP']['attributes']['dn'].split('/')[2][4:]
        L3OUT_CREATED = True

    else:
        L3OUT_CREATED = False
        if args.v:
            print(colour.RED + 'Error 14 - ' + EPG_NAME + ' does not exist')
        ERRORS()

    # Attach Contract if EPG created
    if L3OUT_CREATED:

        CONTRACT_ATTACH_URL =  BASE_URL + 'node/mo/uni/tn-{0}/out-{1}/instP-{2}.json'.format(TENANT, L3OUT, EPG_NAME)
        CONTRACT_ATTACH_JSON = {"fvRsCons":{"attributes":{"tnVzBrCPName": CONTRACT_NAME ,"status":"created,modified"},"children":[]}}

        try:
            post_response = requests.post(CONTRACT_ATTACH_URL, cookies=APIC_COOKIE, data=json.dumps(CONTRACT_ATTACH_JSON), headers=HEADERS, verify=False)
            if post_response.text == '{"totalCount":"0","imdata":[]}':
                print(colour.DARKCYAN + 'Contract:  ' + CONTRACT_NAME + ' Consumed on EPG: ' + EPG_NAME + ' Under L3Out ' + L3OUT + colour.END)
            else:
                print(colour.RED + 'Failed to consume contract: ' + CONTRACT_NAME + 'on EPG: ' + EPG_NAME + ' under L3Out ' + L3OUT + colour.END)
                print(colour.RED + 'Error: ' + post_response.text + colour.END)
        except:
            print(colour.RED + 'Error Posting JSON: ', CONTRACT_ATTACH_JSON + colour.END)


def EXTERNAL_EPG_CONTRACT_PROVIDE(L3OUT_NAME, EPG_NAME, CONTRACT_NAME, BASE_URL, APIC_COOKIE, HEADERS, args):

    # Search for External EPG to build DN.
    EXTERNAL_EPG_SEARCH_RESPONSE = EXTERNAL_EPG_SEARCH(BASE_URL, APIC_COOKIE, L3OUT_NAME, EPG_NAME, HEADERS)

    if int(EXTERNAL_EPG_SEARCH_RESPONSE['totalCount']) == 1:
        TENANT = EXTERNAL_EPG_SEARCH_RESPONSE['imdata'][0]['l3extInstP']['attributes']['dn'].split('/')[1][3:]
        L3OUT = EXTERNAL_EPG_SEARCH_RESPONSE['imdata'][0]['l3extInstP']['attributes']['dn'].split('/')[2][4:]
        L3OUT_CREATED = True

    else:
        L3OUT_CREATED = False
        if args.v:
            print(colour.RED + 'Error 15 - ' + EPG_NAME + ' does not exist' + colour.END)
        ERRORS()

    # Attach Contract if EPG created
    if L3OUT_CREATED:

        CONTRACT_ATTACH_URL =  BASE_URL + 'node/mo/uni/tn-{0}/out-{1}/instP-{2}.json'.format(TENANT, L3OUT, EPG_NAME)
        CONTRACT_ATTACH_JSON = {"fvRsProv":{"attributes":{"tnVzBrCPName": CONTRACT_NAME ,"status":"created,modified"},"children":[]}}

        try:
            post_response = requests.post(CONTRACT_ATTACH_URL, cookies=APIC_COOKIE, data=json.dumps(CONTRACT_ATTACH_JSON), headers=HEADERS, verify=False)
            if post_response.text == '{"totalCount":"0","imdata":[]}':
                print(colour.DARKCYAN + 'Contract:  ' + CONTRACT_NAME + ' Provided on EPG: ' + EPG_NAME + ' Under L3Out ' + L3OUT + colour.END)
            else:
                print(colour.RED + 'Failed to provide contract: ' + CONTRACT_NAME + 'on EPG: ' + EPG_NAME + ' under L3Out ' + L3OUT + colour.END)
                print(colour.RED + 'Error: ' + post_response.text + colour.END)
        except:
            print(colour.RED + 'Error Posting JSON: ', CONTRACT_ATTACH_JSON + colour.END)


def USERNAME_PASSWORD():
    print '\nPlease enter adm credentials.'
    ADM_USER = raw_input("\nEnter Username: ")
    ADM_PASS = getpass("\nEnter Password: ")

    return ADM_USER, ADM_PASS

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "-verbose", help="Increase output verbosity", action="store_true")
    args = parser.parse_args()
    if args.v:
	    print('\nDebugging Enabled\n')
    HEADERS = {'content-type': 'application/json'}
    CONTRACT_LIST = []
    FILTER_LIST = []
    DISPLAY_LIST = []
    ERROR = False
    BANNER()
    DC = raw_input('DC: (DC1/DC2/LAB) ')

    USER_DETAILS = USERNAME_PASSWORD()
    APIC_USERNAME = USER_DETAILS[0]
    APIC_PASSWORD = USER_DETAILS[1]
    SANDBOX = 'https://sandboxapicdc.cisco.com/api/'
    LAB = ''
    DC1 = ''
    DC2 = ''

    if DC.upper() == 'DC1':
        BASE_URL = DC1
    elif DC.upper() == 'DC2':
        BASE_URL = DC2
    elif DC.upper() == 'SANDBOX':
        BASE_URL = SANDBOX
    elif DC.upper() == 'LAB':
        BASE_URL = LAB
    else:
        print(colour.RED + '\nUnknown location selected. please chose from the following:' + colour.END)
        print(colour.RED + 'DC1 | DC2 | LAB | SANDBOX' + colour.END)
        exit()


    PY_WS = OPEN_EXCEL(BASE_URL, DC1, DC2, LAB, SANDBOX)
    EXCEL_MUNGER(PY_WS)
    RULE_LIST = EXCEL_MUNGER(PY_WS)
    time.sleep(1)
    APIC_COOKIE = APIC_LOGIN(BASE_URL, APIC_USERNAME, APIC_PASSWORD, HEADERS)
    if APIC_COOKIE:
        print('\nSuccessfully generated authentication cookie')
    else:
        exit(colour.RED + '\nUnable to connect to APIC. Please check your credentials' + colour.END)
    time.sleep(1)
    EXCEL_FORMAT_VALIDATION(RULE_LIST, args)
    time.sleep(1)
    print(colour.BOLD + '\nChecking if Contracts exist' + colour.END)
    print(colour.BOLD + '-----------------------------\n' + colour.END)

    for rules in RULE_LIST:
        CONTRACT_NAME = rules['NAME']
        CONTRACT_SEARCH_RESPONSE = CONTRACT_SEARCH(BASE_URL, APIC_COOKIE, CONTRACT_NAME, HEADERS)
        if int(CONTRACT_SEARCH_RESPONSE['totalCount']) == 1:
            pass
        else:
            CONTRACT_LIST.append(CONTRACT_NAME)

    CONTRACT_SET = set(CONTRACT_LIST)
    for contracts in CONTRACT_SET:
        print('Contract ' + contracts + ' will be created')

    time.sleep(1)
    print(colour.BOLD + '\nChecking if Filters exist' + colour.END)
    print(colour.BOLD + '-----------------------------\n' + colour.END)


    for rules in RULE_LIST:
        for services in rules['SERVICE']:
            FILTER_NAME = services
            FILTER_SEARCH_RESPONSE = FILTER_SEARCH(BASE_URL, APIC_COOKIE, FILTER_NAME, HEADERS)
            if int(FILTER_SEARCH_RESPONSE['totalCount']) == 1:
                pass
            else:
                FILTER_LIST.append(FILTER_NAME)

    FILTER_SET = set(FILTER_LIST)
    for filters in FILTER_SET:
        print('Filter ' + filters + ' will be created')

    time.sleep(1)
    print(colour.BOLD + '\nChecking if Filters are applied to contracts' + colour.END)
    print(colour.BOLD + '-----------------------------\n' + colour.END)

    for rules in RULE_LIST:
        # Use the contract search to locate subject
        CONTRACT_NAME = rules['NAME']
        CONTRACT_SEARCH_RESPONSE = CONTRACT_SEARCH(BASE_URL, APIC_COOKIE, CONTRACT_NAME, HEADERS)
        # Validate that a contract can be located
        if int(CONTRACT_SEARCH_RESPONSE['totalCount']) == 1:
            TENANT = CONTRACT_SEARCH_RESPONSE['imdata'][0]['vzBrCP']['attributes']['dn'].split('/')[1][3:]
            CONTRACT_SUBJECT = CONTRACT_SEARCH_RESPONSE['imdata'][0]['vzBrCP']['attributes']['dn'].split('/')[2][4:].split('_')[0] + '_SBJ'
            SUBJECT_SEARCH_RESPONSE = SUBJECT_SEARCH(BASE_URL, APIC_COOKIE, CONTRACT_NAME, TENANT, CONTRACT_SUBJECT, HEADERS)

            # Add all filters for a subject to a list to be used for comparison.
            SUBJECT_FILTERS = []
            for filters in SUBJECT_SEARCH_RESPONSE['imdata']:
                SUBJECT_FILTERS.append(filters['vzRsSubjFiltAtt']['attributes']['tnVzFilterName'])

            # compare list of filters to those already in subject

            FILTER_COMPARE = LIST_COMPARE(rules['SERVICE'], SUBJECT_FILTERS)
            if len(FILTER_COMPARE[0]) ==  0:
                #print('\nAll filters presant for contract ' + CONTRACT_NAME)
                pass

            elif len(FILTER_COMPARE[0]) > 0:
                print('\nThe below filters will be added to contract ' + CONTRACT_NAME)
                print(FILTER_COMPARE[0])

            else:
                ERROR = True
        else:
            pass

    time.sleep(1)
    print(colour.BOLD + '\nChecking if L3Outs exist' + colour.END)
    print(colour.BOLD + '-----------------------------\n' + colour.END)


    for rules in RULE_LIST:
        if rules['CONSUMER_L3OUT'] == 'INTERNAL':
            pass
        else:
            L3OUT_NAME = rules['CONSUMER_L3OUT']
            L3OUT_SEARCH_RESPONSE = L3OUT_SEARCH(BASE_URL, APIC_COOKIE, L3OUT_NAME, HEADERS)
            if int(L3OUT_SEARCH_RESPONSE['totalCount']) == 1:
                if rules['CONSUMER_L3OUT'] == L3OUT_SEARCH_RESPONSE['imdata'][0]['l3extOut']['attributes']['name']:
                    pass
                else:
                    ERROR = True
                    if args.v:
                        print(colour.RED + 'Error 16 - ' + L3OUT_NAME + ' does not exist' + colour.END)
            else:
                DISPLAY_LIST.append(L3OUT_NAME)
                ERROR = True
                if args.v:
                    print(colour.RED + 'Error 17 - ' + L3OUT_NAME + ' does not exist or more than one search result retunred'  + colour.END)

    for rules in RULE_LIST:
        if rules['PROVIDER_L3OUT'] == 'INTERNAL':
            pass
        else:
            L3OUT_NAME = rules['PROVIDER_L3OUT']
            L3OUT_SEARCH_RESPONSE = L3OUT_SEARCH(BASE_URL, APIC_COOKIE, L3OUT_NAME, HEADERS)
            if int(L3OUT_SEARCH_RESPONSE['totalCount']) == 1:
                if rules['PROVIDER_L3OUT'] == L3OUT_SEARCH_RESPONSE['imdata'][0]['l3extOut']['attributes']['name']:
                    pass
                else:
                    ERROR = True
                    if args.v:
                        print(colour.RED + 'Error 18 - ' + L3OUT_NAME + ' does not exist' + colour.END)
            else:
                DISPLAY_LIST.append(L3OUT_NAME)
                ERROR = True
                if args.v:
                    print(colour.RED + 'Error 19 - ' + L3OUT_NAME + ' does not exist or more than one search result retunred'  + colour.END)

    DISPLAY_SET = set(DISPLAY_LIST)
    for l3out in DISPLAY_SET:
        print(colour.RED + 'L3Out: ' + l3out + ' Does not exist, please check naming.' + colour.END)
    DISPLAY_LIST = []

    time.sleep(1)
    print(colour.BOLD + '\nChecking if Internal EPGs are created' + colour.END)
    print(colour.BOLD + '-----------------------------\n' + colour.END)

    EPG_LIST = []
    # Search to validate internal EPG's are created
    for rules in RULE_LIST:
        if rules['CONSUMER_L3OUT'] == 'INTERNAL':
            if rules['CONSUMER_EPG'] != 'BLANK':
                CONSUMER_EPG = rules['CONSUMER_EPG']
                # Search for consumer EPG
                INTERNAL_EPG_SEARCH_RESPONSE = INTERNAL_EPG_SEARCH(BASE_URL, APIC_COOKIE, CONSUMER_EPG, HEADERS)
                if int(INTERNAL_EPG_SEARCH_RESPONSE['totalCount']) == 1:
                    pass
                else:
                    DISPLAY_LIST.append(CONSUMER_EPG)
                    ERROR = True
                    if args.v:
                        print(colour.RED + 'Error 20 - ' + CONSUMER_EPG + ' does not exist or more than one search result retunred'  + colour.END)
        else:
            pass


    for rules in RULE_LIST:
        if rules['PROVIDER_L3OUT'] == 'INTERNAL':
            if rules['PROVIDER_EPG'] != 'BLANK':
                PROVIDER_EPG = rules['PROVIDER_EPG']
                # Search for Provider EPG
                INTERNAL_EPG_SEARCH_RESPONSE = INTERNAL_EPG_SEARCH(BASE_URL, APIC_COOKIE, PROVIDER_EPG, HEADERS)
                if int(INTERNAL_EPG_SEARCH_RESPONSE['totalCount']) == 1:
                    #print(PROVIDER_EPG + ' Already created.')
                    pass
                else:
                    DISPLAY_LIST.append(PROVIDER_EPG)
                    ERROR = True
                    if args.v:
                        print(colour.RED + 'Error 21 - ' + PROVIDER_EPG + ' does not exist or more than one search result retunred'  + colour.END)
        else:
            pass

    DISPLAY_SET = set(DISPLAY_LIST)
    for epgs in DISPLAY_SET:
        print(colour.RED + 'EPG "' + epgs + '" needs creating.' + colour.END)
    DISPLAY_LIST = []

    time.sleep(1)
    print(colour.BOLD + '\nChecking if External EPGs are created' + colour.END)
    print(colour.BOLD + '-----------------------------\n' + colour.END)

    # Search to validate external EPG's are created
    for rules in RULE_LIST:
        if rules['CONSUMER_L3OUT'] == 'INTERNAL':
            pass
        else:
			if rules['CONSUMER_EPG'] != 'BLANK':
				CONSUMER_L3OUT = rules['CONSUMER_L3OUT']
				CONSUMER_EPG = rules['CONSUMER_EPG']
				EXTERNAL_EPG_SEARCH_RESPONSE = EXTERNAL_EPG_SEARCH(BASE_URL, APIC_COOKIE, CONSUMER_L3OUT, CONSUMER_EPG, HEADERS)
				if int(EXTERNAL_EPG_SEARCH_RESPONSE['totalCount']) == 1:
					EPG_NAME = EXTERNAL_EPG_SEARCH_RESPONSE['imdata'][0]['l3extInstP']['attributes']['dn'].split('/')[3][6:]
					L3OUT_NAME = EXTERNAL_EPG_SEARCH_RESPONSE['imdata'][0]['l3extInstP']['attributes']['dn'].split('/')[2][4:]
					TENANT_NAME = EXTERNAL_EPG_SEARCH_RESPONSE['imdata'][0]['l3extInstP']['attributes']['dn'].split('/')[1][3:]
					if L3OUT_NAME == rules['CONSUMER_L3OUT']:
						pass
					else:
						print(colour.RED + 'EPG and L3OUT missmatch with ' + L3OUT_NAME + ' and ' + EPG_NAME + ' dont match value: ' + rules['CONSUMER_L3OUT'] + colour.END)

				else:
					DISPLAY_LIST.append(CONSUMER_EPG)
					ERROR = True
					if args.v:
						print(colour.RED + 'Error 22 - ' + CONSUMER_EPG + ' does not exist or more than one search result retunred'  + colour.END)

    for rules in RULE_LIST:
        PROVIDER_EPG = rules['PROVIDER_EPG']
        if rules['PROVIDER_L3OUT'] == 'INTERNAL':
            pass
        else:
			if rules['PROVIDER_EPG'] != 'BLANK':
				PROVIDER_EPG = rules['PROVIDER_EPG']
				PROVIDER_L3OUT = rules['PROVIDER_L3OUT']
				EXTERNAL_EPG_SEARCH_RESPONSE = EXTERNAL_EPG_SEARCH(BASE_URL, APIC_COOKIE, PROVIDER_L3OUT, PROVIDER_EPG, HEADERS)
				if int(EXTERNAL_EPG_SEARCH_RESPONSE['totalCount']) == 1:
					EPG_NAME = EXTERNAL_EPG_SEARCH_RESPONSE['imdata'][0]['l3extInstP']['attributes']['dn'].split('/')[3][6:]
					L3OUT_NAME = EXTERNAL_EPG_SEARCH_RESPONSE['imdata'][0]['l3extInstP']['attributes']['dn'].split('/')[2][4:]
					TENANT_NAME = EXTERNAL_EPG_SEARCH_RESPONSE['imdata'][0]['l3extInstP']['attributes']['dn'].split('/')[1][3:]
					if L3OUT_NAME == rules['PROVIDER_L3OUT']:
						pass
					else:
						print(colour.RED + 'EPG and L3OUT missmatch with ' + L3OUT_NAME + ' and ' + EPG_NAME + ' dont match value: ' + rules['PROVIDER_L3OUT'] + colour.END)

				else:
					DISPLAY_LIST.append(PROVIDER_EPG)
					ERROR = True
					if args.v:
						print(colour.RED + 'Error 22 - ' + PROVIDER_EPG + ' does not exist or more than one search result retunred'  + colour.END)
 
    DISPLAY_SET = set(DISPLAY_LIST)
    for epgs in DISPLAY_SET:
        print(colour.RED + 'EPG "' + epgs + '" needs creating.' + colour.END)

    # Exit script if errors.
    if ERROR:
        print(colour.RED + '\nPlease fix errors and retry script.\n' + colour.END)
        ERRORS()


    # End of pre checks
    print('\nPre Checks completed.')
    print('continue to provisioning?\n')
    USER_CONFIRM = raw_input('Y/N ').upper()
    print USER_CONFIRM
    if USER_CONFIRM != 'Y':
        exit('\nExiting without provisioning.')
    else:
        pass

    #--------------------------------------------------------------------------#
    # Begin Configuration
    #--------------------------------------------------------------------------#

    print(colour.BOLD + '\n\nStarting contract provisioning.\n' + colour.END)
    print(colour.BOLD + '-----------------------------' + colour.END)

    if len(FILTER_SET) > 0:
        print(colour.BOLD + '\nCreating Filters.' + colour.END)
        print(colour.BOLD + '-----------------------------' + colour.END)

        FILTER_CREATE(FILTER_SET, BASE_URL, APIC_COOKIE, HEADERS)
    else:
        pass
    if len(CONTRACT_SET) > 0:
        print(colour.BOLD + '\nCreating Contract & Subjects.' + colour.END)
        print(colour.BOLD + '-----------------------------' + colour.END)

        CONTRACT_CREATE(CONTRACT_SET, BASE_URL, APIC_COOKIE, HEADERS)
    else:
        pass
    # Add filters to subjects
    for rules in RULE_LIST:
        # Use the contract search to locate subject
        CONTRACT_NAME = rules['NAME']
        CONTRACT_SEARCH_RESPONSE = CONTRACT_SEARCH(BASE_URL, APIC_COOKIE, CONTRACT_NAME, HEADERS)
        # Validate that a contract can be located
        if int(CONTRACT_SEARCH_RESPONSE['totalCount']) == 1:
            TENANT = CONTRACT_SEARCH_RESPONSE['imdata'][0]['vzBrCP']['attributes']['dn'].split('/')[1][3:]
            CONTRACT_SUBJECT = CONTRACT_SEARCH_RESPONSE['imdata'][0]['vzBrCP']['attributes']['dn'].split('/')[2][4:].split('_')[0] + '_SBJ'
            SUBJECT_SEARCH_RESPONSE = SUBJECT_SEARCH(BASE_URL, APIC_COOKIE, CONTRACT_NAME, TENANT, CONTRACT_SUBJECT, HEADERS)

            # Add all filters for a subject to a list to be used for comparison.
            SUBJECT_FILTERS = []
            for filters in SUBJECT_SEARCH_RESPONSE['imdata']:
                SUBJECT_FILTERS.append(filters['vzRsSubjFiltAtt']['attributes']['tnVzFilterName'])

            # compare list of filters to those already in subject

            FILTER_COMPARE = LIST_COMPARE(rules['SERVICE'], SUBJECT_FILTERS)
            if len(FILTER_COMPARE[0]) ==  0:
                pass

            elif len(FILTER_COMPARE[0]) > 0:
                for FILTERS in FILTER_COMPARE[0]:
                    FILTER_ATTACH(BASE_URL, APIC_COOKIE, CONTRACT_NAME, CONTRACT_SUBJECT, FILTERS, HEADERS)

            else:
                exit(colour.RED + 'Error adding Filters to subject!' + colour.END)
        else:
            pass

    time.sleep(1)
    print(colour.BOLD + '\nConsuming & Providing Contracts.' + colour.END)
    print(colour.BOLD + '-----------------------------' + colour.END)


    for rules in RULE_LIST:
        LINE = rules['LINE']
        CONTRACT_NAME = rules['NAME']
        # Consuming contract
        EPG_NAME = rules['CONSUMER_EPG']
        print(colour.BOLD + '\nDeploying Contracts for Line: ' + str(LINE) + colour.END)
        print(colour.BOLD + '-----------------------------' + colour.END)

        if EPG_NAME != 'BLANK':
            if rules['CONSUMER_L3OUT'] == 'INTERNAL':
                INTERNL_EPG_CONTRACT_CONSUME(BASE_URL, EPG_NAME, CONTRACT_NAME, APIC_COOKIE, HEADERS)
            else:
                L3OUT_NAME = rules['CONSUMER_L3OUT']
                EXTERNAL_EPG_CONTRACT_CONSUME(L3OUT_NAME, EPG_NAME, CONTRACT_NAME, BASE_URL, APIC_COOKIE, HEADERS, args)

        # Providing contract
        EPG_NAME = rules['PROVIDER_EPG']
        if EPG_NAME != 'BLANK':
            if rules['PROVIDER_L3OUT'] == 'INTERNAL':
                INTERNL_EPG_CONTRACT_PROVIDE(BASE_URL, EPG_NAME, CONTRACT_NAME, APIC_COOKIE, HEADERS)
            else:
                L3OUT_NAME = rules['PROVIDER_L3OUT']
                EXTERNAL_EPG_CONTRACT_PROVIDE(L3OUT_NAME, EPG_NAME, CONTRACT_NAME, BASE_URL, APIC_COOKIE, HEADERS, args)


if __name__ == "__main__":
    main()
