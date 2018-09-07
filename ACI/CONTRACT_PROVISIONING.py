import openpyxl
import requests, json, time
import getpass
import signal
import os
import prettytable

# Ignore SSL Errors
requests.packages.urllib3.disable_warnings()


def OPEN_EXCEL():
    EXCEL_NAME = 'Python Contracts'
    #EXCEL_NAME = raw_input("Enter Contract workbook path and name: ")


    try:
        WB = openpyxl.load_workbook('{}.xlsx'.format(EXCEL_NAME), data_only=True)
        PY_WS = WB['Sheet1']


    except:
        print 'Unable to open {}, please check file name and path is correct'.format(EXCEL_NAME)
        exit()

    return PY_WS


# Function to read through Workbook and build contract information
def EXCEL_MUNGER(PY_WS):
    CONTRACT_LIST = []
    INDEX = 0
    # Loops through the rows in the worksheet to build contract information
    for row in PY_WS.iter_rows(min_row=2, max_col=8):
        DC_LOCATION = row[1].value.upper()
        CONTRACT_NAME = row[2].value.upper()
        CONSUMER_EPG = row[6].value.upper()
        PROVIDER_EPG = row[4].value.upper()
        SERVICE = row[3].value.upper()
        if row[7].value:
            CONSUMER_IP_LIST = row[7].value.split()
        else:
            pass
        if row[5].value:
            PROVIDER_IP_LIST = row[5].value.split()
        else:
            pass

        INDEX += 1
        CONTRACT_LIST.append({'Item': INDEX, 'DC': DC_LOCATION, 'NAME': CONTRACT_NAME, 'CONSUMER_EPG': CONSUMER_EPG, 'CONSUMER_IP': CONSUMER_IP_LIST, 'PROVIDER_EPG': PROVIDER_EPG, 'PROVIDER_IP': PROVIDER_IP_LIST, 'SERVICE': SERVICE })

    print CONTRACT_LIST[0]['PROVIDER_IP']
        #print(INDEX, DC_LOCATION, CONTRACT_NAME, CONSUMER_EPG, CONSUMER_IP, PROVIDER_EPG, PROVIDER_IP, SERVICE)
        # Loops through all the individual cells in that row
        #for cell in row:
        #    print(cell)


PY_WS = OPEN_EXCEL()
EXCEL_MUNGER(PY_WS)


FILTER SEARCH = /api/node/class/vzFilter.json?query-target-filter=and(eq(vzFilter.name,"{0}")).format(SERVICE)
CONTRACT SEARCH = /api/node/class/vzBrCP.xml?query-target-filter=and(eq(vzBrCP.name,"{0}")).format(CONTRACT_NAME)

FILTER_CREATE_URL = '/api/node/mo/uni/tn-common/flt-' + {0} + '.json'.format(SERVICE)
FILTER_CREATE_PAYLOAD = {"vzFilter": {"attributes": {"name": SERVICE,},"children": [{"vzEntry": {"attributes": {"name": SERVICE,"etherT": "ip",	"prot": SERVICE.split(-)[0].lower(),"dFromPort": SERVICE.split(-)[1],"dToPort": SERVICE.split(-)[1],},"children": []}}]}}
FILTER_CREATE_RESPONE = {"totalCount":"0","imdata":[]}

CONTRACT_CREATE_URL = '/api/node/mo/uni/tn-common/brc-' + {0}'.json'.format(CONTRACT_NAME)
CONTRACT_CREATE_PAYLOAD = {	"vzBrCP": {	"attributes": {	"name": CONTRACT_NAME.split(_)[0],"scope": "global",},"children": [{"vzSubj": {	"attributes": {	"name": CONTRACT_NAME.split(_)[0] + 'SBJ',},"children": [{"vzRsSubjFiltAtt": {"attributes": {"tnVzFilterName": SERVICE,	"directives": "none"},}}]}}]}}
CONTRACT_CREATE_RESPONSE = {"totalCount":"0","imdata":[]}

