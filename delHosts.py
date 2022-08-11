import requests, sys, os
from requests.auth import HTTPBasicAuth
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import base64, json, pprint
# DESCRIPTION
#   Deletes Host objects from FMC. Returns status code and result text to stdout. 
# INPUT
#   This script looks for a file named "uuid-fpHosts.log"
#   A text file list of object Host UUID's to delete (one per line)
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
    inputFile = "uuid-fpHosts.log"
except:
    print(f'\nERROR: invalid argument.')
    print(f'USAGE: python <sript-name> <file-name>\n\n')
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

# CREATE list from inputFile
idList = []
with open(inputFile) as f:
    for line in f:
        idList.append(line.strip())

print(f'\n------------------\n')
try: 
    for uuid in idList:
        url = 'https://{0}/api/fmc_config/v1/domain/{1}/object/hosts/{2}'.format(fmcHost,domUUID,uuid)
        res = fmc.delete(url, headers=authHeaders, verify=False)
        statcode = res.status_code
        if statcode == 200:
            result = "DELETED Successfully"
        else:
            result = "Error during delete."
        print(f' {uuid:<40} {statcode:<8} {result}')

except:
    print(f' Error occurred during delete operation.')
print(f'\n------------------')
print(f'\n\n')
