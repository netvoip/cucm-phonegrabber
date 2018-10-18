#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct 15 18:45:48 2018
"""

import configparser
import argparse
from suds.client import Client
from datetime import datetime

Timestart = datetime.now()
Print = True
Search = []
vars = configparser.ConfigParser()
vars.read('vars.conf')
axluser = vars['cucm']['axluser']
axlpassword = vars['cucm']['axlpassword']
cucmip = vars['cucm']['ip']
riswsdl = vars['cucm']['riswsdl']


def cucm_rt_phones(model = 255, name = '', num = '', ip = '', max = 1000, Print = True):
    Out = []
    i = 0
    # Define request
    client = Client(riswsdl,
                    location='https://{}:8443/realtimeservice2/services/RISService70?wsdl'.format(cucmip),
                    username = axluser, password = axlpassword)
    stateInfo = None
    criteria = client.factory.create('CmSelectionCriteria')
    item = client.factory.create('SelectItem')
    criteria.MaxReturnedDevices = max
    criteria.DeviceClass = 'Phone'
    criteria.Model = model
    criteria.Status = 'Registered'
    if name != '':
        criteria.SelectBy = 'Name'
        item.Item = name
        criteria.SelectItems.item.append(item)
    elif num != '':
        criteria.SelectBy = 'DirNumber'
        item.Item = num
        criteria.SelectItems.item.append(item)
    elif ip != '':
        criteria.SelectBy = 'IPV4Address'
        item.Item = ip
        criteria.SelectItems.item.append(item)
    else:
        criteria.SelectBy = 'Name'
    criteria.Protocol = 'Any'
    criteria.DownloadStatus = 'Any'
    result = client.service.selectCmDevice(stateInfo, criteria)

    # Compose resulting list of dicts
    for node in result['SelectCmDeviceResult']['CmNodes']['item']:
        if node['CmDevices'] != None:
            for device in node['CmDevices']['item']:
                OutIp = device['IPAddress'][0][0]['IP']
                OutModel = modelname(device['Model'])
                OutDesc = device['Description']
                OutNum = device['DirNumber'].replace('-Registered', '')
                Out.append({'ip': OutIp, 'model': OutModel, 'desc': OutDesc, 'num': OutNum})
                if Print: print(str(list(Out[i].values())))
                i += 1
    return(Out)

def modelname(modelnum=0):
    # Return model name from number
    if modelnum == 336: return('Third-party SIP Device')
    elif modelnum == 503: return('Cisco Jabber')
    elif modelnum == 592: return('Cisco 3905')
    elif modelnum == 36213: return('Cisco 7811')
    elif modelnum == 621: return('Cisco 7821')
    elif modelnum == 623: return('Cisco 7861')
    elif modelnum == 683: return('Cisco 8841')
    elif modelnum == 685: return('Cisco 8861')
    elif modelnum == 495: return('Cisco 6921')
    elif modelnum == 497: return('Cisco 6961')
    else:
        print('Undefined model name: {}'.format(modelnum))
        return(modelnum)

if __name__ == "__main__":
    # Parsing arguments
    parser = argparse.ArgumentParser(description='Returns active phone list')
    parser.add_argument('-num', action="store", dest="num", default='')
    parser.add_argument('-name', action="store", dest="name", default='')
    parser.add_argument('-ip', action="store", dest="ip", default='')
    parser.add_argument('-max', action="store", dest="max", default=1500)
    parser.add_argument('-model', action="store", dest="model", default=255)
    parser.add_argument('-noprint', action="store_false", dest="noprint", default=True)
    args = parser.parse_args()
    Out = cucm_rt_phones(model = args.model, name = args.name, num = args.num, ip = args.ip, max = args.max, Print = args.noprint)
    print('\nTotal time: {}'.format(datetime.now() - Timestart))