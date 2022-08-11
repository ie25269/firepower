import requests, sys, os
from requests.auth import HTTPBasicAuth
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import base64, json, pprint
#
# DESCRIPTION
#   Creates new Host objects in FMC (bulk post). 
# INPUT
#   json file - json data to create new Host objects in FMC.
# OUTPUT
#   uuid-fpHosts.log - Log file with uuid's for every object created 
# USAGE
#   python3 <scriptName> <jsonConfigFile> 
# ENABLE REST API ON FMC
#   System > Configuration > REST API Preferences > Enable REST API
# API EXPLORER
#   https://<FMC-HOSTNAME-OR-IP>:<HTTPS-PORT>/api/api-explorer
# TOKENS & DOMAIN-UUID
#   X-auth-access-token:	Required for REST API requests
#   X-auth-refresh-token:	Used to refresh auth-access token (requires BOTH tokens for refresh)
#   Domain-UUID:		Required for "MOST" requests, but not all.
#   Token Lifetime:		30 minutes
#   Generate Tokens & Domain UUID:
#     POST to https://<fmc>/api/fmc_platform/v1/auth/generatetoken with BasicAuthHeader
# REFERENCE
#   Firepower Management Center REST API Quick Start Guide, Version 6.2.0

try:
    confFile = str(sys.argv[1])
    logFile = "uuid-fpHosts.log"
except:
    print(f'\nERROR: invalid argument.')
    print(f'USAGE: python <sript-name> <config-file-name>\n\n')
    sys.exit(1)

# Look for ENV variables and use them for authentication.
env1 = "FPWR_USER"
env2 = "FPWR_PASS"
env3 = "FPWR_FMC"
if env1 in os.environ:
    username = os.environ.get(env1)
if env2 in os.environ:
    password = os.environ.get(env2)
if env3 in os.environ:
    fmcHost = os.environ.get(env3)

creds = str.encode(':'.join((username, password)))
encodedAuth = bytes.decode(base64.b64encode(creds))
preHeaders = {
    'authorization': " ".join(("Basic",encodedAuth)),
    }

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
fmc = requests.session()
fmc.auth = (username, password)
fmc.verify = False
fmc.disable_warnings = False
fmc.timeout = 5

# GET Tokens and Domain UUID
tokenURL = 'https://{0}/api/fmc_platform/v1/auth/generatetoken'.format(fmcHost)
res = fmc.post(tokenURL, headers=preHeaders, verify=False)
headers = res.headers
authToken = headers['X-auth-access-token']
authRefreshToken = headers['X-auth-refresh-token']
domUUID = headers['DOMAIN_UUID']
statcode = res.status_code

# NEW HEADERS with acquired Token and DomainUUID
authHeaders = {
    'accept': "application/json",
    'content-type': "application/json",
    'authorization': " ".join(("Basic",encodedAuth)),
    'cache-control': "no-cache",
    'X-auth-access-token': authToken,
    }

# PREP JSON DATA for POST
with open(confFile) as json_file:
    jsondata = json.load(json_file)
bodyReq = json.dumps(jsondata,indent=4)

#print(f'\n----jsondata----\n{jsondata}\n----bodyReq----\n{bodyReq}\n----\n\n')

# SET POST URL & POST data
url = 'https://{0}/api/fmc_config/v1/domain/{1}/object/hosts?bulk=true'.format(fmcHost,domUUID)
#url = 'https://{0}/api/fmc_config/v1/domain/{1}/object/networks?bulk=true'.format(fmcHost,domUUID)
#url = 'https://{0}/api/fmc_config/v1/domain/{1}/object/ranges?bulk=true'.format(fmcHost,domUUID)

res = fmc.post(url, headers=authHeaders, data=bodyReq, verify=False)
content = res.content
data = json.loads(content)
statcode = res.status_code

# CREATE list for deleting uuid's 
idList = []

# DISPLAY uuid & info for objects created
print(f'\nOBJECTS CREATED:\n-------------------\n')
sp=""
print(f'UUID{sp:<36} Type{sp:<11} Name{sp:<21} Value{sp:<25}')
try:
    subdata = data['items']
    #pprint.pprint(subdata,indent=2)
    for obj in subdata:
        objName = obj['name']
        objType = obj['type']
        objID = obj['id']
        objValue = obj['value']
        idList.append(objID)
        print(f'{objID:<40} {objType:<15} {objName:<25} {objValue:<30}')
except:
    print(f' Error reading returned data.')

try:
    with open(logFile, 'w') as f:
        for line in idList:
            f.write(line)
            f.write('\n')
except:
    print(f' Error writing to log file.')

print(f'\n--------------------')
print(f'STAT-CODE: {statcode}')
print(f'DOMAIN-UUID: {domUUID}')
print(f'CONFIG-FILE: {confFile}')
print(f'ID-LOG-FILE: {logFile}')
print(f'\n\n')
