#!/usr/bin/venv python3
# -*- coding: utf-8 -*-

import configparser
import argparse
import os
from zeep import Client
from zeep.cache import SqliteCache
from zeep.transports import Transport
from zeep.exceptions import Fault
from zeep.plugins import HistoryPlugin
from requests import Session
from requests.auth import HTTPBasicAuth
from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning
from lxml import etree
from datetime import datetime

Timestart = datetime.now()
disable_warnings(InsecureRequestWarning)
Print = False
Search = []

vars = configparser.ConfigParser()
if (os.path.exists(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static', 'vars.conf'))):
    varfile = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static', 'vars.conf')
else:
    varfile = 'vars.conf'
vars.read(varfile)
axluser = vars['cucm']['axluser']
axlpassword = vars['cucm']['axlpassword']
cucmhost = vars['cucm']['ip']
riswsdl = 'https://{}:8443/realtimeservice2/services/RISService70?wsdl'.format(cucmhost)

def cucm_rt_phones(model = 255, name = '', num = '', ip = '', max = 1000, Print = True):
    StateInfo = ''
    if name != '':
        SelectBy = 'Name'
        SelectItems = {'item': name}
    elif num != '':
        SelectBy = 'DirNumber'
        SelectItems = {'item': num}
    elif ip != '':
        SelectBy = 'IPV4Address'
        SelectItems = {'item': ip}
    else:
        SelectBy = 'Name'
        SelectItems = {}
    CmSelectionCriteria = {
        'MaxReturnedDevices': max,
        'DeviceClass': 'Phone',
        'Model': '255',
        'Status': 'Registered',
        'SelectBy': SelectBy,
        'SelectItems': SelectItems
    }
    session = Session()
    session.verify = False
    session.auth = HTTPBasicAuth(axluser, axlpassword)
    transport = Transport(cache=SqliteCache(), session=session, timeout=5)
    history = HistoryPlugin()
    client = Client(wsdl=riswsdl, transport=transport, plugins=[history])

    def show_history():
        for item in [history.last_sent, history.last_received]:
            print(etree.tostring(item["envelope"], encoding="unicode", pretty_print=True))

    Out = []
    i = 0
    try:
        resp = client.service.selectCmDevice(CmSelectionCriteria=CmSelectionCriteria, StateInfo=StateInfo)
        result = resp['SelectCmDeviceResult']['CmNodes']['item']
        for node in result:
            if node['CmDevices'] != None:
                 for device in node['CmDevices']['item']:
                    OutIp = device['IPAddress']['item'][0]['IP']
                    OutModel = modelname(device['Model'])
                    OutDesc = device['Description']
                    OutNum = device['DirNumber'].replace('-Registered', '')
                    Out.append({'ip': OutIp, 'model': OutModel, 'desc': OutDesc, 'num': OutNum})
                    if Print: print(str(list(Out[i].values())))
                    i += 1
    except Fault:
        show_history()
        return []
    return Out

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
    elif modelnum == 307: return('Cisco 7911')
    elif modelnum == 115: return('Cisco 7941')
    elif modelnum == 434: return('Cisco 7942')
    elif modelnum == 435: return('Cisco 7945')
    elif modelnum == 365: return('Cisco 7921')
    elif modelnum == 484: return('Cisco 7925')
    elif modelnum == 431: return('Cisco 7937')
    elif modelnum == 30019: return('Cisco 7936 Conference')
    elif modelnum == 30007: return('Cisco 7912')
    elif modelnum == 36255: return('Cisco Spark')
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
    if Print: print('\nTotal time: {}'.format(datetime.now() - Timestart))