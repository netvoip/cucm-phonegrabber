#!/usr/bin/env python3

import requests
import re
import configparser
import argparse
import ssl

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
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

Timestart = datetime.now()
ssl._create_default_https_context = ssl._create_unverified_context
disable_warnings(InsecureRequestWarning)

vars = configparser.ConfigParser()
varfile = 'vars.conf'
vars.read(varfile)
axluser = vars['cucm']['axluser']
axlpassword = vars['cucm']['axlpassword']
cucmhost = vars['cucm']['ip']
riswsdl = 'https://{}:8443/realtimeservice2/services/RISService70?wsdl'.format(cucmhost)

# Get phones info from cucm
def cucm_rt_phones(model = 255, name = '', num = '', ip = '', max = 1000, Print = True):
    StateInfo = ''
    if name:
        SelectBy = 'Name'
        SelectItems = {'item': name}
    elif num:
        SelectBy = 'DirNumber'
        SelectItems = {'item': num}
    elif ip:
        SelectBy = 'IPV4Address'
        SelectItems = {'item': ip}
    else:
        SelectBy = 'Name'
        SelectItems = {}
    CmSelectionCriteria = {
        'MaxReturnedDevices': max,
        'DeviceClass': 'Phone',
        'Model': model,
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

    out = []
    try:
        resp = client.service.selectCmDevice(CmSelectionCriteria=CmSelectionCriteria, StateInfo=StateInfo)
        result = resp['SelectCmDeviceResult']['CmNodes']['item']
        for node in result:
            if node['CmDevices'] != None:
                 for device in node['CmDevices']['item']:
                    current = {}
                    current['ip'] = device['IPAddress']['item'][0]['IP']
                    current['model'] = modelname(device['Model'])
                    current['desc'] = device['Description']
                    current['num'] = device['DirNumber'].replace('-Registered', '')
                    out.append(current)
    except Fault:
        show_history()
        return []
    return out

# Internal model number to human readable
def modelname(modelnum=0):
    if modelnum == 336: return('Third-party SIP Device')
    elif modelnum == 503: return('Cisco Jabber')
    elif modelnum == 592: return('Cisco 3905')
    elif modelnum == 36213: return('Cisco 7811')
    elif modelnum == 621: return('Cisco 7821')
    elif modelnum == 623: return('Cisco 7861')
    elif modelnum == 683: return('Cisco 8841')
    elif modelnum == 684: return('Cisco 8851')
    elif modelnum == 685: return('Cisco 8861')
    elif modelnum == 495: return('Cisco 6921')
    elif modelnum == 497: return('Cisco 6961')
    elif modelnum == 622: return('Cisco 7841')
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
        return modelnum


# Download phone html page
def gethtml(url):
    try:
        r = requests.get(url, timeout = 6)
        r.encoding = 'utf-8'
        out = r.text
    except:
        return('No connect')
    return out


# Insert serial number into phone dict
def extract_sn(ip, model, num, desc):
    out = {'ip': ip, 'model': model, 'num': num, 'desc': desc}
    weburl = ''
    sn_regex = ''
    sn = ''
    if (model == 'Cisco 7811') or (model == 'Cisco 7861'):
        weburl = 'http://{}/CGI/Java/Serviceability'.format(ip)
        sn_regex = r'</TD><TD><B>([A-Z]{3}\w{8})</B></TD>'
    elif model == 'Cisco 3905':
        weburl = 'http://{}/Device_Information.html'.format(ip)
        sn_regex = r'<td><p><b>([A-Z]{3}\w{8})</b></p></td>'
    elif (model == 'Cisco 6961') or (model == 'Cisco 6921'):
        weburl = 'http://{}'.format(ip)
        sn_regex = r'</TD><TD><strong>([A-Z]{3}\w{8})</strong></TD>'
    else:
        weburl = 'http://{}'.format(ip)
        sn_regex = r'</TD><TD><B>([A-Z]{3}\w{8})</B></TD>'

    if (model == 'Cisco Jabber') or (model == 'Third-party SIP Device'):
        sn = 'Not supported'
    else:
        html = gethtml(weburl)
        try:
            sn = re.search(sn_regex, html)[1]
        except:
            sn = 'No SN found'
    out['sn'] = sn
    return(out)


def getphonessn(num, name, ip, max = 30, model=255):
    # Get phones as list of dicts
    devices = []
    devices = cucm_rt_phones(model = model, num = num, name = name, ip = ip, max = max, Print = False)
    devices = sorted(devices, key=lambda k: k['ip'])
    # Run sn extraction
    with ThreadPoolExecutor(max_workers=30) as executor:
        insert_sn = executor.map(extract_sn, (i['ip'] for i in devices), (j['model'] for j in devices),
            (k['num'] for k in devices), (l['desc'] for l in devices))
    devices_with_sn = list(insert_sn)

    # Generate output text
    out_text = ''
    summary = ''
    good = bad = unsup = 0
    for device in devices_with_sn:
        if device['sn'] == 'Not supported':
            unsup += 1
        elif device['sn'] == 'No SN found':
            bad += 1
            summary += str(list(device.values())) + '\n'
        else:
            good += 1
            out_text += '{},{},{},{}\n'.format(device['model'], device['sn'], device['ip'], device['desc'])
    if bad > 0:
        summary = "\nCould not get serials from:\n" + summary
    summary += '\nSuccessful {}, unsuccessful {}, unsupported {}. Total {}.'.format(good, bad, unsup, len(devices))
    out_text += summary
    return(out_text)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Returns active phone list with serial numbers')
    parser.add_argument('-num', action="store", dest="num", default='')
    parser.add_argument('-name', action="store", dest="name", default='')
    parser.add_argument('-ip', action="store", dest="ip", default='')
    parser.add_argument('-max', action="store", dest="max", default=1500)
    parser.add_argument('-model', action="store", dest="model", default=255)
    args = parser.parse_args()
    Result = getphonessn(num = args.num, name = args.name, ip = args.ip, max = args.max, model = args.model)
    print(Result)
    print('Total time: {}'.format(datetime.now() - Timestart))
