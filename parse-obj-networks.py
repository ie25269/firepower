import sys, json, pprint
from ciscoconfparse import CiscoConfParse
from ipaddress import IPv4Network
# 
# 8/11/22 - Currently supports only host, range, and subnet network objects
#
# DESCRIPTION:
#   Parse object network groups from ASA config and output json data into separate files for import to FMC.
# INPUT:
#   ASA config file
# OUTPUT: 
#   Json data for converted objects, separated into multiple files by FMC object type.
#   FileNames:  fpHosts.json, fpNetworks.json, fpRanges.json  
#
#   *** FMC requires separate imports for each different object type. See FMC api-explorer for more detail ***
#
# USAGE: 
# python3 <scriptName> <inputFileName>
#
# From Firepower FMC 6.2.8 API Explorer
#  POST /fmc_config/v1/domain/DomainUUID/object/networks?bulk=true   ( Bulk POST operation on network objects. )
#  POST /fmc_config/v1/domain/domainUUID/object/hosts?bulk=true      ( Bulk POST operation on Host objects )
#  POST /fmc_config/v1/domain/domainUUID/object/ranges?bulk=true     ( Bulk POST on range objects )
#
#

try:
    confFile = str(sys.argv[1])
    parseSyntax = 'asa'
except:
    print(f'\nERROR: invalid argument.')
    print(f'USAGE: python <sript-name> <config-file-name>\n\n')
    sys.exit(1)

parse = CiscoConfParse(confFile, syntax=parseSyntax)

print('-----------------------')
x = 1
fpListHosts = []
fpListNetworks = []
fpListRanges = []

#for obj in parse.find_objects('^object network')[0:3]:
for obj in parse.find_objects('^object network'):
    objFP = {}
    origText = str(obj.text)
    objName = origText.replace("object network ","")
    objDesc = ""
    objOverridable = "false"
    for c in obj.children:
        curLine = str.split(c.text)
        fword = str.lower(curLine[0])
        if fword == "host":
            objType = "Host"
            objVal = str(curLine[1])
        if fword == "subnet":
            objType = "Network"
            mask = str(curLine[2].strip())
            netString = "0.0.0.0/" + mask 
            cidrMask = str(IPv4Network(netString).prefixlen)
            objVal = str(curLine[1]) + "/" + cidrMask
        if fword == "range":
            objType = "Range"
            objVal = curLine[1] + "-" + curLine[2]
        if fword == "description":
            lineText = str(c.text).strip()
            objDesc = lineText.replace("description ","")
    objFP['name'] = objName
    objFP['value'] = objVal
    objFP['overridable'] = objOverridable
    objFP['description'] = objDesc
    objFP['type'] = objType
    #append parsed object dict to corresponding FP list for bulk import
    if objType == "Host":
        fpListHosts.append(objFP)
    if objType == "Network":
        fpListNetworks.append(objFP)
    if objType == "Range":
        fpListRanges.append(objFP)
    #print("Parsed object #{0} - {1}".format(str(x),objName))
    x += 1

numHosts = str(len(fpListHosts))
numNetworks = str(len(fpListNetworks))
numRanges = str(len(fpListRanges))
print(f'Parsing Complete. Parsed {x} objects.')
print(f" {numHosts:<10} host objects\n {numNetworks:<10} network objects\n {numRanges:<10} range objects")
print(f'-----------------------')
# write data to json files
with open('fpHosts.json', 'w') as fout:
    json.dump(fpListHosts, fout, indent=4)
with open('fpNetworks.json', 'w') as fout:
    json.dump(fpListNetworks, fout, indent=4)
with open('fpRanges.json', 'w') as fout:
    json.dump(fpListRanges, fout, indent=4)
print(f' fpHosts.json    json file for converted HOST objects ')
print(f' fpNetworks.json json file for converted NETWORK objects ')
print(f' fpRanges.json   json file for converted RANGE objects ')
print(f'-----------------------')
