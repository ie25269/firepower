import requests, sys, os
from requests.auth import HTTPBasicAuth
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import base64, json, pprint
# INFO
#   Get ServerVersion from FMC 
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

def objDetails(url,authHeaders):
    res = fmc.get(url, headers=authHeaders, verify=False)
    content = res.content
    data = json.loads(content)
    res = {}
    res['name'] = data['name']
    res['desc'] = data['description']
    res['value'] = data['value']
    return res


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

# SET URL & GET data
#url = 'https://{0}/api/fmc_config/v1/domain/{1}/object/hosts'.format(fmcHost,domUUID)
url = 'https://{0}/api/fmc_config/v1/domain/{1}/object/networkaddresses'.format(fmcHost,domUUID)
#url = 'https://{0}/api/fmc_config/v1/domain/{1}/object/networks'.format(fmcHost,domUUID)
#url = 'https://{0}/api/fmc_config/v1/domain/{1}/object/networkgroups'.format(fmcHost,domUUID)
#url = 'https://{0}/api/fmc_config/v1/domain/{1}/object/ranges'.format(fmcHost,domUUID)


# CREATE result dictionary for adding data
result = {}

# Request Data
res = fmc.get(url, headers=authHeaders, verify=False)
content = res.content
data = json.loads(content)
statcode = res.status_code

#Check paging results
if 'paging' in data:
    pages = data['paging']['pages']
    numResults = data['paging']['count']

#Append name & type to results dict
subdata = data['items']
for obj in subdata:
    name = obj['name']
    dtype = obj['type']
    objLink = obj['links']['self']
    objValue = objDetails(objLink,authHeaders)
    value = objValue['value']
    desc = objValue['desc']
    resultString = name + "    " + desc
    result[value] = resultString


# CHECK PAGING and Request Remaining Data...
if 'next' in data['paging']:
    nextLinks = data['paging']['next']
    nextLen = len(nextLinks)
    for url in nextLinks:
        res = fmc.get(url, headers=authHeaders, verify=False)
        content = res.content
        data = json.loads(content)
        #Append name & type to results dict
        subdata = data['items']
        for obj in subdata:
            name = obj['name']
            dtype = obj['type']
            objLink = obj['links']['self']
            objValue = objDetails(objLink,authHeaders)
            value = objValue['value']
            desc = objValue['desc']
            resultString = name + "    " + desc
            result[value] = resultString





print(f'--------------------\n')
#Print results dict 
count = len(result)
for k,v in result.items():
    print(f'{k:<40}: {v}')
print(f'\n--------------------')
print(f'StatusCode: {statcode}')
print(f'Result Keys: {count:<6} NumResults: {numResults}')
print(f'{url}\n\n')
