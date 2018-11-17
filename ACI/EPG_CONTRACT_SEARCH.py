import requests, json, time
from getpass import getpass

# Ignore SSL Errors
requests.packages.urllib3.disable_warnings()
 
def APIC_LOGIN(BASE_URL, APIC_USERNAME, APIC_PASSWORD ):
    # Log into APIC and generate a cookie for future requests
    headers = {'content-type': 'application/json'}
    login_url = BASE_URL + 'aaaLogin.json'
    auth = {"aaaUser" : {"attributes" : {"name" : APIC_USERNAME,"pwd" : APIC_PASSWORD}}}
    auth_payload = json.dumps(auth)
    try:
        post_response = requests.post(login_url, data=auth_payload, headers=headers, verify=False)
        # Take token from response to use for future authentications
        payload_response = json.loads(post_response.text)
        token = payload_response['imdata'][0]['aaaLogin']['attributes']['token']
        APIC_COOKIE = {}
        APIC_COOKIE['APIC-Cookie'] = token

    except:
        print('Unable to connect to APIC. Please check your credentials')
        exit()

    return APIC_COOKIE


def GET_PROVIDED_CONTRACTS(BASE_URL, APIC_COOKIE, ENDPOINT_CHILDREN, headers):
    for contracts in ENDPOINT_CHILDREN['imdata']:
        if contracts.keys() == [u'fvRsProv']:
            print('Contract: ' + contracts['fvRsProv']['attributes']['tnVzBrCPName'])
            CONTRACT_NAME = contracts['fvRsProv']['attributes']['tnVzBrCPName']
            TENANT = contracts['fvRsProv']['attributes']['tDn'].split('/')[1][3:]

            try:
                GET_URL = BASE_URL + 'node/mo/uni/tn-{0}/brc-{1}.json?query-target=children'.format(TENANT, CONTRACT_NAME)
                GET_RESPONSE = requests.get(GET_URL, cookies=APIC_COOKIE, headers=headers, verify=False)
                CONTRACTS = json.loads(GET_RESPONSE.text)
                return CONTRACTS

            except:
                print('Unable to connect to search Contracts')
                exit()


def GET_CONTRACT_SUBJECTS(BASE_URL, APIC_COOKIE, CONTRACT_DN, headers):
    try:
        TENANT = CONTRACT_DN.split('/')[1][3:]
        CONTRACT_NAME = CONTRACT_DN.split('/')[2][4:]
        GET_URL = BASE_URL + 'node/mo/uni/tn-{0}/brc-{1}.json?query-target=children'.format(TENANT, CONTRACT_NAME)
        GET_RESPONSE = requests.get(GET_URL, cookies=APIC_COOKIE, headers=headers, verify=False)
        CONTRACT_JSON = json.loads(GET_RESPONSE.text)
        return CONTRACT_JSON

    except:
        print('Unable to connect to search Contracts')
        exit()




def GET_CONTRACT_FILTERS(BASE_URL, APIC_COOKIE, CONTRACT_JSON, headers):
    PORT_LIST = []
    for subjects in CONTRACT_JSON['imdata']:
        if subjects.keys() == [u'vzSubj']:
            SUBJECT_NAME = subjects['vzSubj']['attributes']['name']
            TENANT = subjects['vzSubj']['attributes']['dn'].split('/')[1][3:]
            CONTRACT_NAME = subjects['vzSubj']['attributes']['dn'].split('/')[2][4:]
            try:
                GET_URL = BASE_URL + 'node/mo/uni/tn-{0}/brc-{1}/subj-{2}.json?query-target=children'.format(TENANT,CONTRACT_NAME,SUBJECT_NAME)
                GET_RESPONSE = requests.get(GET_URL, cookies=APIC_COOKIE, headers=headers, verify=False)
                SUBJECT_JSON = json.loads(GET_RESPONSE.text)

            except:
                print('Unable to connect to search for Contract Subjects')
                exit()

            for filters in SUBJECT_JSON['imdata']:
                if filters.keys() == [u'vzRsSubjFiltAtt']:
                    PORT_LIST.append(filters['vzRsSubjFiltAtt']['attributes']['tnVzFilterName'].encode())
    return PORT_LIST


def GET_VZ_ANY_CONTRACTS(BASE_URL, APIC_COOKIE, ENDPOINT_CHILDREN, headers):
    for contracts in ENDPOINT_CHILDREN['imdata']:
        if contracts.keys() == [u'fvRsBd']:
            BRIDGE_DOMAIN_NAME = contracts['fvRsBd']['attributes']['tDn'].split('/')[2][3:]
            BRIDGE_DOMAIN_TENANT = contracts['fvRsBd']['attributes']['tDn'].split('/')[1][3:]

            try:
                GET_URL = BASE_URL + 'node/mo/uni/tn-{0}/BD-{1}.json?query-target=children'.format(BRIDGE_DOMAIN_TENANT , BRIDGE_DOMAIN_NAME)
                GET_RESPONSE = requests.get(GET_URL, cookies=APIC_COOKIE, headers=headers, verify=False)
                BD_DETAILS = json.loads(GET_RESPONSE.text)

            except:
                print('Unable to connect to locate EPG Bridge Domain')
                exit()

            for vrf in BD_DETAILS['imdata']:
                if vrf.keys() == [u'fvRsCtx']:
                    VRF_NAME = vrf['fvRsCtx']['attributes']['tDn'].split('/')[2][4:]
                    VRF_TENANT = vrf['fvRsCtx']['attributes']['tDn'].split('/')[1][3:]
                    try:
                        GET_URL = BASE_URL + 'node/mo/uni/tn-{0}/ctx-{1}/any.json?query-target=children'.format(VRF_TENANT, VRF_NAME)
                        GET_RESPONSE = requests.get(GET_URL, cookies=APIC_COOKIE, headers=headers, verify=False)
                        VRF_DETAILS = json.loads(GET_RESPONSE.text)
                        return VRF_DETAILS

                    except:
                        print('Unable to connect to locate VRF level contracts.')
                        exit()

        if contracts.keys() == [u'l3extSubnet']:
            L3OUT_NAME = contracts['l3extSubnet']['attributes']['dn'].split('/')[2][4:]
            L3OUT_TENANT = contracts['l3extSubnet']['attributes']['dn'].split('/')[1][3:]

            try:
                GET_URL = BASE_URL + 'node/mo/uni/tn-{0}/out-{1}.json?query-target=children'.format(L3OUT_TENANT , L3OUT_NAME)
                GET_RESPONSE = requests.get(GET_URL, cookies=APIC_COOKIE, headers=headers, verify=False)
                L3OUT_DETAILS = json.loads(GET_RESPONSE.text)

            except:
                print('Unable to connect to locate L3OUT')
                exit()

            for vrf in L3OUT_DETAILS['imdata']:
                if vrf.keys() == [u'l3extRsEctx']:
                    VRF_NAME = vrf['l3extRsEctx']['attributes']['tDn'].split('/')[2][4:]
                    VRF_TENANT = vrf['l3extRsEctx']['attributes']['tDn'].split('/')[1][3:]
                    try:
                        GET_URL = BASE_URL + 'node/mo/uni/tn-{0}/ctx-{1}/any.json?query-target=children'.format(VRF_TENANT, VRF_NAME)
                        GET_RESPONSE = requests.get(GET_URL, cookies=APIC_COOKIE, headers=headers, verify=False)
                        VRF_DETAILS = json.loads(GET_RESPONSE.text)
                        return VRF_DETAILS

                    except:
                        print('Unable to connect to locate VRF level contracts.')
                        exit()

def GET_PROVIDER_DETAILS(BASE_URL, APIC_COOKIE, CONTRACT_JSON, headers):
    PROVIDER_LIST = []
    IP_LIST = []
    for subjects in CONTRACT_JSON['imdata']:
        # Add Provider EPG's dependinfg if they are external or internal
        if subjects.keys() == [u'vzRtProv']:
            if subjects['vzRtProv']['attributes']['tDn'].split('/')[3][:3] == 'epg':
                PROVIDER_LIST.append(subjects['vzRtProv']['attributes']['tDn'].split('/')[3][4:].encode())
                PROVIDER_EPG_NAME = subjects['vzRtProv']['attributes']['tDn'].split('/')[3][4:]
                PROVIDER_EPG_TENANT = subjects['vzRtProv']['attributes']['tDn'].split('/')[1][3:]
                PROVIDER_EPG_APP_PROF = subjects['vzRtProv']['attributes']['tDn'].split('/')[2][3:]
                try:
                    GET_URL = BASE_URL + 'node/mo/uni/tn-{0}/ap-{1}/epg-{2}.json?query-target=children'.format(
                        PROVIDER_EPG_TENANT, PROVIDER_EPG_APP_PROF, PROVIDER_EPG_NAME)
                    GET_RESPONSE = requests.get(GET_URL, cookies=APIC_COOKIE, headers=headers, verify=False)
                    PROVIDER_EPG_RESPONSE = json.loads(GET_RESPONSE.text)
                    # print(PROVIDER_EPG_RESPONSE)
                    for epgs in PROVIDER_EPG_RESPONSE['imdata']:
                        if epgs.keys() == [u'fvCEp']:
                            IP_LIST.append(epgs['fvCEp']['attributes']['ip'].encode())

                except:
                    print('Unable to connect to search for Provider EPGs')
                    exit()

            elif subjects['vzRtProv']['attributes']['tDn'].split('/')[3][:5] == 'instP':
                PROVIDER_LIST.append(subjects['vzRtProv']['attributes']['tDn'].split('/')[3][6:].encode())
                PROVIDER_EPG_NAME = subjects['vzRtProv']['attributes']['tDn'].split('/')[3][6:]
                PROVIDER_EPG_TENANT = subjects['vzRtProv']['attributes']['tDn'].split('/')[1][3:]
                PROVIDER_EPG_L3OUT = subjects['vzRtProv']['attributes']['tDn'].split('/')[2][4:]
                try:
                    GET_URL = BASE_URL + 'node/mo/uni/tn-{0}/out-{1}/instP-{2}.json?query-target=children'.format(
                        PROVIDER_EPG_TENANT, PROVIDER_EPG_L3OUT, PROVIDER_EPG_NAME)
                    GET_RESPONSE = requests.get(GET_URL, cookies=APIC_COOKIE, headers=headers, verify=False)
                    PROVIDER_EPG_RESPONSE = json.loads(GET_RESPONSE.text)
                    for epgs in PROVIDER_EPG_RESPONSE['imdata']:
                        if epgs.keys() == [u'l3extSubnet']:
                            SCOPE_LIST = epgs['l3extSubnet']['attributes']['scope'].split(',')
                            if 'import-security' in SCOPE_LIST:
                                IP_LIST.append(epgs['l3extSubnet']['attributes']['ip'].encode())

                except:
                    print('Unable to connect to search for Provider EPGs')
                    exit()

    return PROVIDER_LIST, IP_LIST


def GET_CONSUMER_DETAILS(BASE_URL, APIC_COOKIE, CONTRACT_JSON, headers):
    CONSUMER_LIST = []
    IP_LIST = []
    for subjects in CONTRACT_JSON['imdata']:
        # Add Consumer EPG's dependinfg if they are external or internal
        if subjects.keys() == [u'vzRtCons']:
            if subjects['vzRtCons']['attributes']['tDn'].split('/')[3][:3] == 'epg':
                CONSUMER_LIST.append(subjects['vzRtCons']['attributes']['tDn'].split('/')[3][4:].encode())
                CONSUMER_EPG_NAME = subjects['vzRtCons']['attributes']['tDn'].split('/')[3][4:]
                CONSUMER_EPG_TENANT = subjects['vzRtCons']['attributes']['tDn'].split('/')[1][3:]
                CONSUMER_EPG_APP_PROF = subjects['vzRtCons']['attributes']['tDn'].split('/')[2][3:]
                try:
                    GET_URL = BASE_URL + 'node/mo/uni/tn-{0}/ap-{1}/epg-{2}.json?query-target=children'.format(CONSUMER_EPG_TENANT, CONSUMER_EPG_APP_PROF, CONSUMER_EPG_NAME)
                    GET_RESPONSE = requests.get(GET_URL, cookies=APIC_COOKIE, headers=headers, verify=False)
                    CONSUMER_EPG_RESPONSE = json.loads(GET_RESPONSE.text)
                    # print(CONSUMER_EPG_RESPONSE)
                    for epgs in CONSUMER_EPG_RESPONSE['imdata']:
                        if epgs.keys() == [u'fvCEp']:
                            IP_LIST.append(epgs['fvCEp']['attributes']['ip'].encode())

                except:
                    print('Unable to connect to search for Consumer EPGs')
                    exit()

            elif subjects['vzRtCons']['attributes']['tDn'].split('/')[3][:5] == 'instP':
                CONSUMER_LIST.append(subjects['vzRtCons']['attributes']['tDn'].split('/')[3][6:].encode())
                CONSUMER_EPG_NAME = subjects['vzRtCons']['attributes']['tDn'].split('/')[3][6:]
                CONSUMER_EPG_TENANT = subjects['vzRtCons']['attributes']['tDn'].split('/')[1][3:]
                CONSUMER_EPG_L3OUT = subjects['vzRtCons']['attributes']['tDn'].split('/')[2][4:]
                try:
                    GET_URL = BASE_URL + 'node/mo/uni/tn-{0}/out-{1}/instP-{2}.json?query-target=children'.format(CONSUMER_EPG_TENANT, CONSUMER_EPG_L3OUT, CONSUMER_EPG_NAME)
                    GET_RESPONSE = requests.get(GET_URL, cookies=APIC_COOKIE, headers=headers, verify=False)
                    CONSUMER_EPG_RESPONSE = json.loads(GET_RESPONSE.text)
                    for epgs in CONSUMER_EPG_RESPONSE['imdata']:
                        if epgs.keys() == [u'l3extSubnet']:
                            SCOPE_LIST = epgs['l3extSubnet']['attributes']['scope'].split(',')
                            if 'import-security' in SCOPE_LIST:
                                IP_LIST.append(epgs['l3extSubnet']['attributes']['ip'].encode())

                except:
                    print('Unable to connect to search for Consumer EPGs')
                    exit()

    return CONSUMER_LIST, IP_LIST


def main():
    SANDBOX = 'https://sandboxapicdc.cisco.com/api/'
    LAB = ''
    DC1 = ''
    DC2 = ''
    DC = raw_input('DC: (DC1/DC2/LAB) ')
    APIC_USERNAME = raw_input('Username: ')
    APIC_PASSWORD = getpass()
    ENDPOINT_LOCATION = raw_input('Internal or External: ').upper()
    EPG_NAME = raw_input('EPG Name: ').upper()
    headers = {'content-type': 'application/json'}

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


    # Login to apic
    APIC_COOKIE = APIC_LOGIN(BASE_URL, APIC_USERNAME, APIC_PASSWORD)
    if APIC_COOKIE:
        print('\nSuccessfully generated authentication cookie\n')
    else:
        print('\nUnable to connect to APIC. Please check your credentials\n')
        time.sleep(1)

    # Search for External EPG's and display contract details
    if ENDPOINT_LOCATION == 'EXTERNAL':
        try:
            GET_URL	 = BASE_URL + 'node/class/l3extInstP.json?query-target-filter=and(eq(l3extInstP.name,"{0}"))'.format(EPG_NAME)
            GET_RESPONSE = requests.get(GET_URL, cookies=APIC_COOKIE, headers=headers, verify=False)
            EXTERNAL_ENDPOINTS = json.loads(GET_RESPONSE.text)
            TENANT = EXTERNAL_ENDPOINTS['imdata'][0]['l3extInstP']['attributes']['dn'].split('/')[1][3:]
            L3OUT = EXTERNAL_ENDPOINTS['imdata'][0]['l3extInstP']['attributes']['dn'].split('/')[2][4:]

        except:
            print('Unable to connect to search for EPG')
            exit()


        try:
            GET_URL = BASE_URL + 'node/mo/uni/tn-{0}/out-{1}/instP-{2}.json?query-target=children'.format(TENANT, L3OUT, EPG_NAME)
            GET_RESPONSE = requests.get(GET_URL, cookies=APIC_COOKIE, headers=headers, verify=False)
            ENDPOINT_CHILDREN = json.loads(GET_RESPONSE.text)

        except:
            print('Unable to connect to search for EPG Contracts')
            exit()

    # Search for Internal EPG's and display contract details
    elif ENDPOINT_LOCATION == 'INTERNAL':
        try:
            GET_URL = BASE_URL + 'node/class/fvAEPg.json?query-target-filter=and(eq(fvAEPg.name,"{0}"))'.format(EPG_NAME)
            GET_RESPONSE = requests.get(GET_URL, cookies=APIC_COOKIE, headers=headers, verify=False)
            INTERNAL_ENDPOINTS = json.loads(GET_RESPONSE.text)
            TENANT = INTERNAL_ENDPOINTS['imdata'][0]['fvAEPg']['attributes']['dn'].split('/')[1][3:]
            APP_PROF = INTERNAL_ENDPOINTS['imdata'][0]['fvAEPg']['attributes']['dn'].split('/')[2][3:]


        except:
            print('Unable to connect to search for EPG')
            exit()

        try:
            GET_URL = BASE_URL + 'node/mo/uni/tn-{0}/ap-{1}/epg-{2}.json?query-target=children'.format(TENANT, APP_PROF, EPG_NAME)
            GET_RESPONSE = requests.get(GET_URL, cookies=APIC_COOKIE, headers=headers, verify=False)
            ENDPOINT_CHILDREN = json.loads(GET_RESPONSE.text)

        except:
            print('Unable to connect to search for EPG Contracts')
            exit()

    else:
        print('Unknown EPG location selected. please chose from the following:')
        print('Internal | External')
        exit()

    print('\nConsumed VZ any Contracts:')
    print('-----------------------------')
    # Get VZ ant level contracts
    VRF_DETAILS = GET_VZ_ANY_CONTRACTS(BASE_URL, APIC_COOKIE, ENDPOINT_CHILDREN, headers)
    for vz_contracts in VRF_DETAILS['imdata']:
        if vz_contracts.keys() == [u'vzRsAnyToCons']:
            CONTRACT_NAME = vz_contracts['vzRsAnyToCons']['attributes']['tnVzBrCPName']
            CONTRACT_DN = vz_contracts['vzRsAnyToCons']['attributes']['tDn']
            CONTRACT_JSON = GET_CONTRACT_SUBJECTS(BASE_URL, APIC_COOKIE, CONTRACT_DN, headers)
            print('Contract: ' + CONTRACT_NAME)
            PROVIDER_LIST = GET_PROVIDER_DETAILS(BASE_URL, APIC_COOKIE, CONTRACT_JSON, headers)[0]
            print('Provided by: ' + str(PROVIDER_LIST))
            IP_LIST = GET_PROVIDER_DETAILS(BASE_URL, APIC_COOKIE, CONTRACT_JSON, headers)[1]
            if len(IP_LIST) == 0:
                print('No IPs found')
            else:
                print('Provider IPs: ' + str(IP_LIST))
            PORT_LIST = GET_CONTRACT_FILTERS(BASE_URL, APIC_COOKIE, CONTRACT_JSON, headers)
            print('Ports: ' + str(PORT_LIST) + '\n')
#
    print('\nConsumed Contracts:')
    print('-----------------------------')
    # Get Non VRF level contracts
    for contracts in ENDPOINT_CHILDREN['imdata']:
        if contracts.keys() == [u'fvRsCons']:
            print('Contract: ' + contracts['fvRsCons']['attributes']['tnVzBrCPName'])
            CONTRACT_NAME = contracts['fvRsCons']['attributes']['tnVzBrCPName']
            TENANT = contracts['fvRsCons']['attributes']['tDn'].split('/')[1][3:]
            PORT_LIST = []
            PROVIDER_LIST = []
            IP_LIST = []

            try:
                GET_URL = BASE_URL + 'node/mo/uni/tn-{0}/brc-{1}.json?query-target=children'.format(TENANT, CONTRACT_NAME)
                GET_RESPONSE = requests.get(GET_URL, cookies=APIC_COOKIE, headers=headers, verify=False)
                CONTRACTS = json.loads(GET_RESPONSE.text)

            except:
                print('Unable to connect to search Contracts')
                exit()

            for subjects in CONTRACTS['imdata']:
                if subjects.keys() == [u'vzSubj']:
                    SUBJECT_NAME = subjects['vzSubj']['attributes']['name']
                    TENANT = subjects['vzSubj']['attributes']['dn'].split('/')[1][3:]
                    try:
                        GET_URL = BASE_URL + 'node/mo/uni/tn-{0}/brc-{1}/subj-{2}.json?query-target=children'.format(TENANT, CONTRACT_NAME, SUBJECT_NAME)
                        GET_RESPONSE = requests.get(GET_URL, cookies=APIC_COOKIE, headers=headers, verify=False)
                        SUBJECT_JSON = json.loads(GET_RESPONSE.text)

                    except:
                        print('Unable to connect to search for Contract Subjects')
                        exit()

                    for filters in SUBJECT_JSON['imdata']:
                        if filters.keys() == [u'vzRsSubjFiltAtt']:
                            PORT_LIST.append(filters['vzRsSubjFiltAtt']['attributes']['tnVzFilterName'].encode())

                # Add Provider EPG's dependinfg if they are external or internal
                if subjects.keys() == [u'vzRtProv']:
                    if subjects['vzRtProv']['attributes']['tDn'].split('/')[3][:3] == 'epg':
                        PROVIDER_LIST.append(subjects['vzRtProv']['attributes']['tDn'].split('/')[3][4:].encode())
                        PROVIDER_EPG_NAME = subjects['vzRtProv']['attributes']['tDn'].split('/')[3][4:]
                        PROVIDER_EPG_TENANT = subjects['vzRtProv']['attributes']['tDn'].split('/')[1][3:]
                        PROVIDER_EPG_APP_PROF = subjects['vzRtProv']['attributes']['tDn'].split('/')[2][3:]
                        try:
                            GET_URL = BASE_URL + 'node/mo/uni/tn-{0}/ap-{1}/epg-{2}.json?query-target=children'.format(PROVIDER_EPG_TENANT, PROVIDER_EPG_APP_PROF, PROVIDER_EPG_NAME)
                            GET_RESPONSE = requests.get(GET_URL, cookies=APIC_COOKIE, headers=headers, verify=False)
                            PROVIDER_EPG_RESPONSE = json.loads(GET_RESPONSE.text)
                            # print(PROVIDER_EPG_RESPONSE)
                            for epgs in PROVIDER_EPG_RESPONSE['imdata']:
                                if epgs.keys() == [u'l3extSubnet']:
                                    SCOPE_LIST = epgs['l3extSubnet']['attributes']['scope'].split(',')
                                    if 'import-security' in SCOPE_LIST:
                                        IP_LIST.append(epgs['l3extSubnet']['attributes']['ip'].encode())

                        except:
                            print('Unable to connect to search for Consumer EPGs')
                            exit()

                    elif subjects['vzRtProv']['attributes']['tDn'].split('/')[3][:5] == 'instP':
                        PROVIDER_LIST.append(subjects['vzRtProv']['attributes']['tDn'].split('/')[3][6:].encode())
                        PROVIDER_EPG_NAME = subjects['vzRtProv']['attributes']['tDn'].split('/')[3][6:]
                        PROVIDER_EPG_TENANT = subjects['vzRtProv']['attributes']['tDn'].split('/')[1][3:]
                        PROVIDER_EPG_L3OUT = subjects['vzRtProv']['attributes']['tDn'].split('/')[2][4:]
                        try:
                            GET_URL = BASE_URL + 'node/mo/uni/tn-{0}/out-{1}/instP-{2}.json?query-target=children'.format(PROVIDER_EPG_TENANT, PROVIDER_EPG_L3OUT, PROVIDER_EPG_NAME)
                            GET_RESPONSE = requests.get(GET_URL, cookies=APIC_COOKIE, headers=headers, verify=False)
                            PROVIDER_EPG_RESPONSE = json.loads(GET_RESPONSE.text)
                            for epgs in PROVIDER_EPG_RESPONSE['imdata']:
                                if epgs.keys() == [u'l3extSubnet']:
                                    IP_LIST.append(epgs['l3extSubnet']['attributes']['ip'].encode())

                        except:
                            print('Unable to connect to search for Provider EPGs')
                            exit()

            print('Provided by: ' + str(PROVIDER_LIST))
            if len(IP_LIST) == 0:
                print('No IPs found')
            else:
                print(str(IP_LIST))
            print('Ports: ' + str(PORT_LIST) + '\n')


    print('\nProvided VZ any Contracts:')
    print('-----------------------------')
    VRF_DETAILS = GET_VZ_ANY_CONTRACTS(BASE_URL, APIC_COOKIE, ENDPOINT_CHILDREN, headers)
    for vz_contracts in VRF_DETAILS['imdata']:
        if vz_contracts.keys() == [u'vzRsAnyToProv']:
            CONTRACT_NAME = vz_contracts['vzRsAnyToProv']['attributes']['tnVzBrCPName']
            CONTRACT_DN = vz_contracts['vzRsAnyToProv']['attributes']['tDn']
            CONTRACT_JSON = GET_CONTRACT_SUBJECTS(BASE_URL, APIC_COOKIE, CONTRACT_DN, headers)
            print('Contract: ' + CONTRACT_NAME)
            PROVIDER_LIST = GET_CONSUMER_DETAILS(BASE_URL, APIC_COOKIE, CONTRACT_JSON, headers)[0]
            print('Consumed by: ' + str(PROVIDER_LIST))
            IP_LIST = GET_CONSUMER_DETAILS(BASE_URL, APIC_COOKIE, CONTRACT_JSON, headers)[1]
            if len(IP_LIST) == 0:
                print('No IPs found')
            else:
                print('Consumer IPs: ' + str(IP_LIST))
            PORT_LIST = GET_CONTRACT_FILTERS(BASE_URL, APIC_COOKIE, CONTRACT_JSON, headers)
            print('Ports: ' + str(PORT_LIST) + '\n')

    print('\nProvided Contracts:')
    print('-----------------------------')

    for contracts in ENDPOINT_CHILDREN['imdata']:
        if contracts.keys() == [u'fvRsProv']:
            print('Contract: ' + contracts['fvRsProv']['attributes']['tnVzBrCPName'])
            CONTRACT_NAME = contracts['fvRsProv']['attributes']['tnVzBrCPName']
            TENANT = contracts['fvRsProv']['attributes']['tDn'].split('/')[1][3:]
            PORT_LIST = []
            CONSUMER_LIST = []
            IP_LIST = []

            try:
                GET_URL = BASE_URL + 'node/mo/uni/tn-{0}/brc-{1}.json?query-target=children'.format(TENANT, CONTRACT_NAME)
                GET_RESPONSE = requests.get(GET_URL, cookies=APIC_COOKIE, headers=headers, verify=False)
                CONTRACTS = json.loads(GET_RESPONSE.text)

            except:
                print('Unable to connect to search Contracts')
                exit()

            for subjects in CONTRACTS['imdata']:
                if subjects.keys() == [u'vzSubj']:
                    SUBJECT_NAME = subjects['vzSubj']['attributes']['name']
                    TENANT = subjects['vzSubj']['attributes']['dn'].split('/')[1][3:]
                    try:
                        GET_URL = BASE_URL + 'node/mo/uni/tn-{0}/brc-{1}/subj-{2}.json?query-target=children'.format(TENANT, CONTRACT_NAME, SUBJECT_NAME)
                        GET_RESPONSE = requests.get(GET_URL, cookies=APIC_COOKIE, headers=headers, verify=False)
                        SUBJECT_JSON = json.loads(GET_RESPONSE.text)

                    except:
                        print('Unable to connect to search for Contract Subjects')
                        exit()

                    for filters in SUBJECT_JSON['imdata']:
                        if filters.keys() == [u'vzRsSubjFiltAtt']:
                            PORT_LIST.append(filters['vzRsSubjFiltAtt']['attributes']['tnVzFilterName'].encode())

                # Add consumer EPG's dependinfg if they are external or internal
                if subjects.keys() == [u'vzRtCons']:
                    if subjects['vzRtCons']['attributes']['tDn'].split('/')[3][:3] == 'epg':
                        CONSUMER_LIST.append(subjects['vzRtCons']['attributes']['tDn'].split('/')[3][4:].encode())
                        CONSUMER_EPG_NAME = subjects['vzRtCons']['attributes']['tDn'].split('/')[3][4:]
                        CONSUMER_EPG_TENANT = subjects['vzRtCons']['attributes']['tDn'].split('/')[1][3:]
                        CONSUMER_EPG_APP_PROF = subjects['vzRtCons']['attributes']['tDn'].split('/')[2][3:]
                        try:
                            GET_URL = BASE_URL + 'node/mo/uni/tn-{0}/ap-{1}/epg-{2}.json?query-target=children'.format(CONSUMER_EPG_TENANT, CONSUMER_EPG_APP_PROF, CONSUMER_EPG_NAME)
                            GET_RESPONSE = requests.get(GET_URL, cookies=APIC_COOKIE, headers=headers, verify=False)
                            CONSUMER_EPG_RESPONSE = json.loads(GET_RESPONSE.text)
                            # print(CONSUMER_EPG_RESPONSE)
                            for epgs in CONSUMER_EPG_RESPONSE['imdata']:
                                if epgs.keys() == [u'fvCEp']:
                                    IP_LIST.append(epgs['fvCEp']['attributes']['ip'].encode())

                        except:
                            print('Unable to connect to search for Consumer EPGs')
                            exit()

                    elif subjects['vzRtCons']['attributes']['tDn'].split('/')[3][:5] == 'instP':
                        CONSUMER_LIST.append(subjects['vzRtCons']['attributes']['tDn'].split('/')[3][6:].encode())
                        CONSUMER_EPG_NAME = subjects['vzRtCons']['attributes']['tDn'].split('/')[3][6:]
                        CONSUMER_EPG_TENANT = subjects['vzRtCons']['attributes']['tDn'].split('/')[1][3:]
                        CONSUMER_EPG_L3OUT = subjects['vzRtCons']['attributes']['tDn'].split('/')[2][4:]
                        try:
                            GET_URL = BASE_URL + 'node/mo/uni/tn-{0}/out-{1}/instP-{2}.json?query-target=children'.format(CONSUMER_EPG_TENANT, CONSUMER_EPG_L3OUT, CONSUMER_EPG_NAME)
                            GET_RESPONSE = requests.get(GET_URL, cookies=APIC_COOKIE, headers=headers, verify=False)
                            CONSUMER_EPG_RESPONSE = json.loads(GET_RESPONSE.text)
                            for epgs in CONSUMER_EPG_RESPONSE['imdata']:
                                if epgs.keys() == [u'l3extSubnet']:
                                    SCOPE_LIST = epgs['l3extSubnet']['attributes']['scope'].split(',')
                                    if 'import-security' in SCOPE_LIST:
                                        IP_LIST.append(epgs['l3extSubnet']['attributes']['ip'].encode())

                        except:
                            print('Unable to connect to search for Consumer EPGs')
                            exit()

            print('Consumed by: ' + str(CONSUMER_LIST))
            if len(IP_LIST) == 0:
                print('No IPs found')
            else:
                print(str(IP_LIST))
            print('Ports: ' + str(PORT_LIST) + '\n')



if __name__ == "__main__":
    main()