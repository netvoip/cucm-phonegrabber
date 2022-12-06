### Introduction
Retrieves registered phones list from CUCM, connects to each by web interface and parses its serial number. The main advantage is that it can work with any phone model with web access enabled. Relatively fast, processing 1000 phones takes 15-30 sec.

Currently tested phone models:
```
Cisco 3905, Cisco 6921, Cisco 6961, Cisco 7811, Cisco 7821, Cisco 7861, Cisco 8841, Cisco 8861
```
If your phone is not listed, slight code changes might be required.

### Setup
On client computer you need to have Python interpreter v3.4+. Install required modules by `pip install -r requirements.txt` for console script only or `pip install -r requirements_flask.txt` for using console and web interface.  

`vars.conf` file should contain: 
- IP address or hostname of UCM server with "Cisco AXL Web Service" service running, 
- Username and password of user with "Standard AXL API access" role assigned, 
- Path to RIS WSDL schema on local computer, which can be downloaded from  
`https://cucm:8443/realtimeservice2/services/RISService70?wsdl`

### Usage
Starting from 9 version, CUCM AXL response is limited to ~1000 items. If you have more than 1000 active devices, you need to split your request into smaller ones grouped by directory number, name or IP (only one parameter per request) and model.  
`python get_phones_sn.py -num 1*` - phones with number starting from 1  
`python get_phones_sn.py -name SEP*` - all hardware phones  
`python get_phones_sn.py -model 621` - internal Cisco model number is used, see [RisPort70 API Reference](https://developer.cisco.com/docs/sxml/#risport70-api-reference)  
`python get_phones_sn.py -ip 192.168.* -max 10` - phones in 192.168.0.0/16 network, limit to 10 items  

Results are printed in csv format so it can be easily converted to xls for further processing.

### Web GUI
Here is simple user interface based on Flask. Run local server by command `python flask_start.py`
