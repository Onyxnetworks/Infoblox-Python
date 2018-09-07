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
    #EXCEL_NAME = raw_input("Enter LTM workbook path and name: ")


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