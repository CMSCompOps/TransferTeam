try: import xml.etree.ElementTree as ET
except ImportError: from elementtree import ElementTree as ET
try: import json
except ImportError: import simplejson as json
import urllib2, httplib, sys

# global vars: prod, trans : we create these text files, see run.py
#              cmsTopology : static text from dashboard team,
#              sites       : from BDII
#              output      : {"prod" : [...], "trans" : [...], "nowhere" : [...]}

output = {"prod" : [], "trans" : [], "nowhere" : []}

def getDataFromURL(url, header = {}):
    request = urllib2.Request(url, headers=header)
    urlObj  = urllib2.urlopen(request)
    data    = urlObj.read()
    return data

def getSites():
    XML   = getDataFromURL('http://dashb-cms-vo-feed.cern.ch/dashboard/request.py/cmssitemapbdii')
    XML   = ET.fromstring(XML)
    sites = XML.findall('atp_site')
    ret   = {}
    for site in sites:
        groups   = site.findall('group')
        siteName = None
        for i in groups:
            if i.attrib['type'] == 'CMS_Site':
                siteName = groups[1].attrib['name']
                break
        if not siteName: 
            continue
        services = site.findall('service')
        ret[siteName] = {}
        ret[siteName]['hosts'] = []
        ret[siteName]['name']  = site.attrib['name']
        for service in services:
            serviceName = service.attrib['hostname']
            ret[siteName]['hosts'].append(serviceName)
    return ret

def parseHN(data):
    parsedHNs = []
    for line in data.split('\n'):
        if not len(line): continue
        if ':' in line: line = line[:line.find(':')]
        parsedHNs.append(line)
    return parsedHNs

# try exception if we have a problem with URL.

try :
    sites = getSites()
except Exception as e :
    err={}
    err["error"] = str(e)
    print json.dumps(err)
    sys.exit(1)

#import expection dictionary
with open('/opt/TransferTeam/AAAOps/Federation/exceptions.json') as f: exc = f.read()
exc = json.loads(exc)

def exception(name):
    ret = None
    for i in exc.keys():
	if i == name : return exc[i]['VOname']
    return ret


def siteName2CMSSiteName(dom):
    ret = None
    for cmsSite in sites.keys():
        ret = exception(dom)
	if ret :
	    ret = str(ret)
	    return ret  
	if sites[cmsSite]['hosts'][0].find(dom) != -1:
            #print cmsSite
            return cmsSite
    return ret

if __name__ == "__main__":
    # get domains
    domains = {}
    with open('/opt/TransferTeam/AAAOps/Federation/in/prod_domain.txt') as f:  domains['prod']  = parseHN(f.read())
    with open('/opt/TransferTeam/AAAOps/Federation/in/trans_domain.txt') as f: domains['trans'] = parseHN(f.read())

    # find CMS site name of prod sites
    for federation in ['prod', 'trans']:
        for i in domains[federation]:
	    cmsSiteName = siteName2CMSSiteName(i)
	    if cmsSiteName and not cmsSiteName in output[federation]:
                output[federation].append(cmsSiteName)

    # special case for nowhere sites: if a site is not placed in both
    # federations, move it into "nowhere" array
    for cmsSite in sites.keys():
        if not cmsSite in output['prod'] and not cmsSite in output['trans']:
            output["nowhere"].append(cmsSite)
	if cmsSite == "T1_FR_CCIN2P3" and cmsSite in output['prod'] :
	    output["prod"].append("T2_FR_CCIN2P3")

    with open('/opt/TransferTeam/AAAOps/Federation/out/federations.json', 'w') as f:
        f.write(json.dumps(output, indent = 1))
exit()
