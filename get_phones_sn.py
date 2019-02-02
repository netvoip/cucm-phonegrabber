#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct 15 11:52:00 2018
"""

import requests
import re
import argparse
import ssl
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from get_active_phones import cucm_rt_phones

Timestart = datetime.now()
ssl._create_default_https_context = ssl._create_unverified_context
Printsum = True
To_file = False


def gethtml(url):
    # Downloads phone html page
    try:
        r = requests.get(url, timeout = 6)
        r.encoding = 'utf-8'
        Text = r.text
    except:
        return('No connect')
    return(Text)


def sn(ip, model, num, desc):
    # Returns dict with serial number
    Out = {'ip': ip, 'model': model, 'num': num, 'desc': desc}
    Address = SnRegex = Sn = ''
    if (model == 'Cisco 7811') or (model == 'Cisco 7861'):
        Address = 'http://{}/CGI/Java/Serviceability'.format(ip)
        SnRegex = '</TD><TD><B>([A-Z]{3}\w{8})</B></TD>'
    elif model == 'Cisco 3905':
        Address = 'http://{}/Device_Information.html'.format(ip)
        SnRegex = '<td><p><b>([A-Z]{3}\w{8})</b></p></td>'
    elif (model == 'Cisco 6961') or (model == 'Cisco 6921'):
        Address = 'http://{}'.format(ip)
        SnRegex = '</TD><TD><strong>([A-Z]{3}\w{8})</strong></TD>'
    else:
        Address = 'http://{}'.format(ip)
        SnRegex = '</TD><TD><B>([A-Z]{3}\w{8})</B></TD>'

    if (model == 'Cisco Jabber') or (model == 'Third-party SIP Device'):
        Sn = 'Not supported'
    else:
        Text = gethtml(Address)
        try:
            Sn = re.findall(SnRegex, Text)[0]
        except:
            Sn = 'Not found'
    Out['sn'] = Sn
    return(Out)


def getphonessn(num, name, ip, max = 30, model=255):
    Txt = Txttotal = ''
    Good = Notgood = Notsupported = 0
    # Get phones list of dicts
    Devices = []
    Devices = cucm_rt_phones(model = model, num = num, name = name, ip = ip, max = max, Print = False)
    Devices = sorted(Devices, key=lambda k: k['ip'])
    # Run sn extraction
    with ThreadPoolExecutor(max_workers=30) as executor:
        Result = executor.map(sn, (i['ip'] for i in Devices), (j['model'] for j in Devices),
            (k['num'] for k in Devices), (l['desc'] for l in Devices))
    Devices_ext = list(Result)
    # Make fragments of output text
    for device in Devices_ext:
        if device['sn'] == 'Not supported':
            Notsupported += 1
            continue
        elif device['sn'] == 'Not found':
            Notgood += 1
            Txttotal += '\n' + str(list(device.values()))
        else:
            Good += 1
            Txt += '\n{},{},{},{}'.format(device['model'], device['sn'], device['ip'], device['desc'])
    # Compose and print output text
    if Notgood > 0:
        Txttotal = "\n\nCould not get serial from:" + Txttotal
    Txttotal += '\n\nSuccessful {}, unsuccessful {}, unsupported {}. Total {}.'.format(Good, Notgood, Notsupported, len(Devices))
    Txt += Txttotal
    return(Txt)


if __name__ == '__main__':
    # Parsing arguments
    parser = argparse.ArgumentParser(description='Returns active phone list with serial numbers')
    parser.add_argument('-num', action="store", dest="num", default='')
    parser.add_argument('-name', action="store", dest="name", default='')
    parser.add_argument('-ip', action="store", dest="ip", default='')
    parser.add_argument('-max', action="store", dest="max", default=1500)
    parser.add_argument('-model', action="store", dest="model", default=255)
    parser.add_argument('-noprint', action="store_false", dest="noprint", default=True)
    args = parser.parse_args()
    Result = getphonessn(num = args.num, name = args.name, ip = args.ip, max = args.max, model = args.model)
    if args.noprint:
        print(Result)
    if Printsum: print('Total time: {}'.format(datetime.now() - Timestart))
    if To_file:
        with open('_serials.txt', 'w', encoding='utf-8') as output_file:
            output_file.write(Result)
        output_file.close()