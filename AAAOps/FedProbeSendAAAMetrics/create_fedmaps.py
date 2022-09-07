try: import xml.etree.ElementTree as ET
except ImportError: from elementtree import ElementTree as ET
try: import json
except ImportError: import simplejson as json

import sys
#import urllib2, httplib, sys
#import httplib, sys

try : import urllib
except : import urllib2

try:
    # For Python 3.0 and later
    import urllib.request
except ImportError:
    # Fall back to Python 2's urllib2
    import urllib2

# from XRDFED-kibana-probe.py
import xml.dom.minidom 
import subprocess
import os
import sys
import signal
import re
import time
#import Lemon.XMLAPI
import socket
import atexit
import threading
import tempfile
import socket
#import path
#import os.path
from os import path
import numpy as np

# global vars: sites, output
#              cmsTopology : from vofeed,
#              sites       : from vofeed and updated as we proceed
#              output      : {"prod" : [...], "trans" : [...], "nowhere" : [...]}

THEPATH='/opt/TransferTeam/AAAOps/FedProbeSendAAAMetrics/'
#VOFEED='http://dashb-cms-vo-feed.cern.ch/dashboard/request.py/cmssitemapbdii'
VOFEED='https://cmssst.web.cern.ch/cmssst/vofeed/vofeed.xml'
LOCKFILE=THEPATH+'create_fedmaps.lock'
timeout_sec = 10 * 60

output = {"prod" : [], "trans" : [], "nowhere" : []}
sites = {}
xrdmapc_output_prod = ''
xrdmapc_output_prod_2 = ''
xrdmapc_output_tran = ''
gRedirectors=['cms-xrd-global01.cern.ch', 'cms-xrd-global02.cern.ch']
tRedirectors=['cms-xrd-transit.cern.ch']
topRedirectors = [gRedirectors[0],gRedirectors[1],]+tRedirectors

if not path.exists(THEPATH+'mapHostSitenames.py') : 
   with open(THEPATH+'mapHostSitenames.py','w') as data : data.write('HostSitenames = {}')

if not path.exists(THEPATH+'siteStoages.py') : 
   with open(THEPATH+'siteStoages.py','w') as data : data.write('SiteStorages = {}')

if not path.exists(THEPATH+'DNSARecords.py') : 
   with open(THEPATH+'DNSARecords.py','w') as data : data.write('DNSARecords = {}')

if not path.exists(THEPATH+'xrdVersions.py') : 
   with open(THEPATH+'xrdVersions.py','w') as data : data.write('XrdVersions = {}')

from mapHostSitenames import HostSitenames
from siteStoages import SiteStorages 
from DNSARecords import DNSARecords
from xrdVersions import XrdVersions

class Alarm(Exception):
    pass

def alarm_handler(signum, frame):
    print ("ERROR: caught overall timeout after "+str(timeout_sec)+"s\n")
    clear_lock()
    sys.exit(2)
    raise Alarm

def clear_lock():
    try:
        os.unlink(LOCKFILE)      
    except (Exception,e) :
        print ("could not remove lockfile:"+str(e))

def xrd_info(redirector,what):
    theargs = [redirector, "query", "config", what]
    if 'version' in what or 'role' in what : command = 'xrdfs'
    else :
       command = 'xrdmapc'
       theargs = [ '--list', 'all', redirector ]
    config_out = "unknown"
    count = 0
    count_limit = 3
    timelimit = 2
    if 'xrdmapc' in command :
       timelimit = 180
       count_limit = 1
    while (count < count_limit):
       (errtext,out,err,elapsed) = run_xrd_commands(command, theargs, timelimit) #"xrdfs",
                                                      #[redirector,
                                                      # "query","config", # 1:kXR_QStats
                                                      # what])         # a_ll stats
    
       if 'xrdmapc' in command :
          if out :
             errtext = err
             config_out = out
             break
       if err:
          #errtext = ''
          #config_out = 'error'
          config_out = err.replace(b'\n',b'').decode()
       else:
          #config_out=out
          #if 'xrdmapc' in command :
          #   break
          #else : 
          config_out = out.replace(b'\n',b'').decode()
          #   # to check if count matters config_out=config_out+'+'+str(count)
          if out.replace(b'\n',b'') : break
          time.sleep(1)
       count += 1
    #print ( 'DEBUG count = ',count,' config_out ',config_out, ' redirector ',redirector)
    if not 'xrdmapc' in command :
       if not config_out : config_out = 'timeout'
       if 'Auth failed' in config_out : config_out = 'Auth failed'
    return (errtext,config_out,out)

def run_xrd_commands(cmd,args,timelimit):
    dev_null = open('/dev/null', 'r')
    errtxt = ''
    elapsed = -1.0
    #xrd_args = [ 'perl','-e',"alarm 180; exec @ARGV", cmd,   # one-line wrapper that *actually* kills the command
    #             "-DIConnectTimeout","30",
    #             "-DITransactionTimeout","60",
    #             "-DIRequestTimeout","60" ] + args    
    xrd_args = [ 'perl','-e',"alarm "+str(timelimit)+" ; exec @ARGV", cmd,   # one-line wrapper that *actually* kills the command
    #xrd_args = [ 'perl','-e',"alarm 30 ; exec @ARGV", cmd,   # one-line wrapper that *actually* kills the command
                 ] + args    
    #if 'xrdmapc' in cmd :
    #    xrd_args = [ cmd, ] + args    
    try:
        start = time.time()
        proc = subprocess.Popen(xrd_args,
                                stdin=dev_null,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        (out, err) = proc.communicate()
        ret = proc.returncode
        elapsed = (time.time() - start)
        #print ( ' out ',out )
        #if 'xrdmapc' in cmd : return ('',out,err,elapsed)
        err_redir_index = err.rfind(b'Received redirection to')
        err_index3010 = err.rfind(b'(error code: 3010')  # (permission denied) may be sort-of-OK - we are talking to final storage already - UK
        err_index3005 = err.rfind(b'(error code: 3005')  # (no user mapping) - INFN
        if err_redir_index >= 0 and (err_index3010 >= 0 or err_index3005 >= 0):
            errtxt = ''
        else:    
            if(ret > 0):
               errtxt = "client-side error - exit code "+str(ret)+"\n"
            err_index = err.rfind(b'Last server error')
            if err_index >= 0:
               err_end_index=err.find(b"\n",err_index)
               errtxt = errtxt + err[err_index:err_end_index]
    except (Exception,e) :
        errtext = errtxt + "Exception: "+str(e)
        out = 'Try did not work :O'
        print(out)
    dev_null.close()
    
    return (errtxt,out,err,elapsed)


def getDataFromURL(url, header = {}):
    try:
       # For Python 3.0 and later
       request = urllib.request.Request(url, headers=header)
       urlObj = urllib.request.urlopen(request)
       data    = urlObj.read()
    except ImportError:
       request = urllib2.Request(url, headers=header)
       urlObj  = urllib2.urlopen(request)
       data    = urlObj.read()
    return data

# Hard-coded one
def getGlobalRedirectors():
    
    siteName='T0_CH_CERN'
    #gRedirectors=['cms-xrd-global01.cern.ch', 'cms-xrd-global02.cern.ch']
    #tRedirectors=['cms-xrd-transit.cern.ch']
    ret = {}
    #ret[siteName] = {}
    ret['sites'] = []
    ret['hosts'] = []
    ret['flavors'] = []
    ret['endpoints'] = []
    ret['name']  = []
    ret['contact']  = []
    ret['xrootd_version']  = []
    ret['xrootd_role']  = []
    ret['xrootd_servers'] = []
    ret['xrootd_storage'] = []
    if SiteStorages[ siteName ] : xrootd_storage = SiteStorages[ siteName ]
    else : 
       xrootd_storage = getStorageFromStorageJson ( siteName )
       updateSiteStorage ( siteName , xrootd_storage )
    ret['federation'] = []

    # Production
    for gRedir in gRedirectors:
        ret['sites'].append(siteName)
        ret['hosts'].append(gRedir)
        ret['flavors'].append('XROOTD')
        ret['endpoints'].append(gRedir+':1094')
        ret['name'].append('CERN-PROD')
        ret['contact'].append(siteName)
        #(err_info,xrootd_version,dump_info) = xrd_info(gRedir+':1094',"version")
        #(err_info,xrootd_role,dump_info) = xrd_info(gRedir+':1094',"role")
        ret['xrootd_version'].append('')
        ret['xrootd_role'].append('')
        ret['xrootd_servers'].append('_^_')
        ret['xrootd_storage'].append(xrootd_storage)
        ret['federation'].append('prod')

    # Transitional
    for tRedir in tRedirectors:
        ret['sites'].append(siteName)
        ret['hosts'].append(tRedir)
        ret['flavors'].append('XROOTD')
        ret['endpoints'].append(tRedir+':1094')
        ret['name'].append('CERN-PROD')
        ret['contact'].append(siteName)
        #(err_info,xrootd_version,dump_info) = xrd_info(gRedir+':1094',"version")
        #(err_info,xrootd_role,dump_info) = xrd_info(gRedir+':1094',"role")
        ret['xrootd_version'].append('')
        ret['xrootd_role'].append('')
        ret['xrootd_servers'].append('_^_')
        ret['xrootd_storage'].append(xrootd_storage)
        ret['federation'].append('trans')
    return ret

def getSites():
    XML   = getDataFromURL(VOFEED)
    XML   = ET.fromstring(XML)
    #sites = XML.findall('atp_site')
    sites = XML.findall('.//atp_site')
    ret   = {}
    for site in sites:

        groups   = site.findall('.//group')
        siteName = None
        for i in groups:
            if i.attrib['type'] == 'CMS_Site':
                siteName = groups[1].attrib['name']
                break
        if not siteName: 
            continue
        services = site.findall('.//service')
        ret[siteName] = {}
        ret[siteName]['sites'] = []
        ret[siteName]['hosts'] = []
        ret[siteName]['flavors'] = []
        ret[siteName]['endpoints'] = []
        ret[siteName]['name']  = []
        ret[siteName]['contact']  = []
        ret[siteName]['xrootd_version']  = []
        ret[siteName]['xrootd_role']  = []
        ret[siteName]['xrootd_servers'] = []
        ret[siteName]['xrootd_storage'] = []
        ret[siteName]['federation'] = []
    #print ('DEBUG getSites() ret keys  ',ret.keys() )
    #print ('getSites() ret["T0_CH_CERN"] ',ret["T0_CH_CERN"])
    name = ''
    contact = ''
    for site in sites:
        groups   = site.findall('.//group')
        siteName = None
        for i in groups:
            if i.attrib['type'] == 'CMS_Site':
                siteName = groups[1].attrib['name']
                break
        if not siteName: 
            continue
        #print ('DEBUG getSites() site ',siteName)
        services = site.findall('.//service')
        #ret[siteName]['name'].append(site.attrib['name'])
        if site.attrib['name'] : name = site.attrib['name']
        contact = None
        try:
           #ret[siteName]['contact'].append(site.attrib['contact'])
           contact = site.attrib['contact']
        except:
           #ret[siteName]['contact'].append("")
           contact = siteName
        #if site.attrib['contact'] : contact = site.attrib['contact']

        #print ('DEBUG getSites() site contact ',)
        for service in services:
              flavor = service.attrib['flavour']
              try:
                 endpoint=service.attrib['endpoint']
              except:
                 endpoint=service.attrib['flavour']
            
              xrootd_version='__'
              xrootd_role='__'
              #if flavor in 'XROOTD':
              #  (err_info,xrootd_version,dump_info) = xrd_info(endpoint,"version")
              #  (err_info,xrootd_role,dump_info) = xrd_info(endpoint,"role")
              serviceName = service.attrib['hostname']
            
              #print ('DEBUG getSites() services siteName ',siteName)
              ret[siteName]['sites'].append(siteName)
              ret[siteName]['hosts'].append(serviceName)
              ret[siteName]['flavors'].append(flavor)
              ret[siteName]['endpoints'].append(endpoint)
              ret[siteName]['xrootd_version'].append(xrootd_version)
              ret[siteName]['xrootd_role'].append(xrootd_role)
              ret[siteName]['xrootd_servers'].append('_^_')
              #print ('DEBUG getSites() getStorageFromStorageJson siteName ',siteName)
              xrootd_storage = getStorageFromStorageJson ( siteName)
              #print ('DEBUG getSites() xrootd_storage ',xrootd_storage)
              #if siteName in SiteStorages : print (' found it ')
              #else : print ('not found ')
              if siteName in SiteStorages :
                 #print ( 'A ')
                 xrootd_storage = SiteStorages[ siteName ]
              else : 
                 #print ( 'B ')
                 xrootd_storage = getStorageFromStorageJson ( siteName )
                 updateSiteStorage ( siteName , xrootd_storage )
              #print ('DEBUG getSites() done sitestorage ')
              ret[siteName]['xrootd_storage'].append(xrootd_storage)
              ret[siteName]['name'].append(name)
              ret[siteName]['contact'].append(contact)
              ret[siteName]['federation'].append('nowhere')
              #print ('DEBUG getSites() done  ')
    return ret


def getStorageFromStorageJson ( site ):
    import os.path
    from os import path
    if not path.exists('/cvmfs/cms.cern.ch/SITECONF/'+site+'/storage.json') : return 'no_storage_json'
    with open('/cvmfs/cms.cern.ch/SITECONF/'+site+'/storage.json') as f: storage = f.read()
    try:
      storage = json.loads(str(storage))
    except:
      return 'storage_json_bad'
    xrootd_volume = 'info_missing'
    #print ('DEBUG getStorageFromStorageJson ( site ) before for vol in storage = ',storage)
    #for line in xrdmapc_output_prod.splitlines() :
    #    line = line.decode() # python3
    #for vol in storage :
    for index in range(len(storage)):
       vol=storage[index]
       volume = str(vol['volume']) # ' '.join([str(elem) for elem in str(vol['volume']).split('_')]) 
       #print ('DEBUG getStorageFromStorageJson ( site ) volume = ',volume)
       if 'FEDERATION' in volume.upper() : continue 
       #print ('DEBUG getStorageFromStorageJson ( site ) FEDERATION not in volume ',volume, ' vol protocols len ',len(vol['protocols']),' vol ',vol['protocols'])
       #for proto in vol['protocols'] :
       for index_proto in range(len(vol['protocols'])) :
           proto=vol['protocols'][index_proto]
           #print ( 'DEBUG getStorageFromStorageJson ( site ) storage index ', index_proto, ' volume ',volume, ' type ',type(proto) )
           #print ( 'DEBUG getStorageFromStorageJson ( site ) storage index ', index_proto, ' volume ',volume, proto['protocol'] )
           try :
             if 'XRootD' in str(proto['protocol']) : xrootd_volume = volume
           except :
             continue
           
    #print ('DEBUG getStorageFromStorageJson ( site ) after for vol in storage')
    if 'info_missing' in xrootd_volume :
     #for vol in storage :
     for index in range(len(storage)):
       vol=storage[index]
       volume = str(vol['volume']) # ' '.join([str(elem) for elem in str(vol['volume']).split('_')]) 
       if 'FEDERATION' in volume.upper() : continue 
       #for proto in vol['protocols'] :
       for index_proto in range(len(vol['protocols'])) :
           proto=vol['protocols'][index_proto]
           #print ( 'storage volume ',volume,proto['protocol'] )
           try : 
             if 'WebDAV' in str(proto['protocol']) : xrootd_volume = volume
           except :
             continue
    #print ('DEBUG getStorageFromStorageJson ( site ) site volume ', site, xrootd_volume )
    #                            3 (
    #print ( 'storage volume ', len(storage), (str(storage[0]['volume'])).split('_')[1:])
    #print ( 'storage volume ', len(storage), storage[1])
    #print ( 'storage volume ', len(storage), storage[2])
    return xrootd_volume

def getStorages():
    XML   = getDataFromURL(VOFEED)
    XML   = ET.fromstring(XML)
    #sites = XML.findall('atp_site')
    sites = XML.findall('.//atp_site')
    ret   = {}
    for site in sites:
        groups   = site.findall('.//group')
        siteName = None
        for i in groups:
            if i.attrib['type'] == 'CMS_Site':
                siteName = groups[1].attrib['name']
                break
        if not siteName: 
            continue
        #services = site.findall('.//service')
        ret[siteName] = {}
        ret[siteName]['sites'] = []
        ret[siteName]['hosts'] = []
        ret[siteName]['flavors'] = []
        ret[siteName]['endpoints'] = []
        ret[siteName]['name']  = []
        ret[siteName]['contact']  = []
        ret[siteName]['xrootd_version']  = []
        ret[siteName]['xrootd_role']  = []
        ret[siteName]['xrootd_servers'] = []
        ret[siteName]['xrootd_storage'] = []
    name = ''
    contact = ''
    storage_guessed = ''
    for site in sites:
        groups   = site.findall('.//group')
        siteName = None
        for i in groups:
            if i.attrib['type'] == 'CMS_Site':
                siteName = groups[1].attrib['name']
                break
        if not siteName: 
            continue
        se_resources = site.findall('.//se_resource')
        storage_guessed = 'NI'
        for i in se_resources :
            if i.attrib['id'] == 'RD3PCP':
              try :
               path = se_resources[1].attrib['path']
               #print (siteName, path )
               if 'HADOOP' in path.upper() : storage_guessed = 'hadoop'
               if 'DCACHE' in path.upper() : storage_guessed = 'dcache'
               if '/PNFS/' in path.upper() : storage_guessed = 'dcache'
               if 'CEPH' in path.upper() : storage_guessed = 'ceph'
               if 'LUSTRE' in path.upper() : storage_guessed = 'lustre'
               if 'STORM' in path.upper() : storage_guessed = 'posix'
               if 'GPFS' in path.upper() : storage_guessed = 'gpfs'
               if 'EOS' in path.upper() : storage_guessed = 'eos'
              except :
               storage_guessed = 'NI'
            if i.attrib['id'] == 'WRDEL3PCP' :
              try :
               path = se_resources[1].attrib['path']
               #print (siteName, path )
               if 'HADOOP' in path.upper() : storage_guessed = 'hadoop'
               if 'DCACHE' in path.upper() : storage_guessed = 'dcache'
               if '/PNFS/' in path.upper() : storage_guessed = 'dcache'
               if 'CEPH' in path.upper() : storage_guessed = 'ceph'
               if 'LUSTRE' in path.upper() : storage_guessed = 'lustre'
               if 'STORM' in path.upper() : storage_guessed = 'posix'
               if 'GPFS' in path.upper() : storage_guessed = 'gpfs'
               if 'EOS' in path.upper() : storage_guessed = 'eos'
              except :
               storage_guessed = 'NI'
 
        services = site.findall('.//service')
        #ret[siteName]['name'].append(site.attrib['name'])
        if site.attrib['name'] : name = site.attrib['name']
        try:
           #ret[siteName]['contact'].append(site.attrib['contact'])
           contact = site.attrib['contact']
        except:
           #ret[siteName]['contact'].append("")
           contact = siteName
        #if site.attrib['contact'] : contact = site.attrib['contact']

        for service in services:
              flavor = service.attrib['flavour']
              try:
                 endpoint=service.attrib['endpoint']
              except:
                 endpoint=service.attrib['flavour']
            
              xrootd_version='__'
              xrootd_role='__'
              #if flavor in 'XROOTD':
              #  (err_info,xrootd_version,dump_info) = xrd_info(endpoint,"version")
              #  (err_info,xrootd_role,dump_info) = xrd_info(endpoint,"role")
              serviceName = service.attrib['hostname']
              if 'XROOTD' in flavor :
                 #print ( siteName, serviceName )
                 if 'HADOOP' in serviceName.upper() : storage_guessed = 'hadoop'
                 if 'DCACHE' in serviceName.upper() : storage_guessed = 'dcache'
                 if '/PNFS/' in serviceName.upper() : storage_guessed = 'dcache'
                 if 'CEPH' in serviceName.upper() : 
                     storage_guessed = 'ceph'
                     #print (siteName, serviceName, 'ceph')
                 if 'LUSTRE' in serviceName.upper() : storage_guessed = 'lustre'
                 if 'STORM' in serviceName.upper() : storage_guessed = 'posix'
                 if 'GPFS' in serviceName.upper() : storage_guessed = 'gpfs'
                 if 'EOS' in serviceName.upper() : storage_guessed = 'eos'

              ret[siteName]['sites'].append(siteName)
              ret[siteName]['hosts'].append(serviceName)
              ret[siteName]['flavors'].append(flavor)
              ret[siteName]['endpoints'].append(endpoint)
              ret[siteName]['xrootd_version'].append(xrootd_version)
              ret[siteName]['xrootd_role'].append(xrootd_role)
              ret[siteName]['xrootd_servers'].append('_^_')
              ret[siteName]['xrootd_storage'].append( siteName+'+'+storage_guessed )
              #ret[siteName]['xrootd_storage_guessed'].append( storage_guessed )
              ret[siteName]['name'].append(name)
              ret[siteName]['contact'].append(contact)
    return ret


def parseHN(data):
    parsedHNs = []
    for line in data.split('\n'):
        if not len(line): continue
        if ':' in line: line = line[:line.find(':')]
        parsedHNs.append(line)
    return parsedHNs

def findDomain (h,idx) :
    h=h.split('.')[::-1]
    hlen=len(h)
    #if idx > hlen - 1 :
    #   return ''
    d=''
    j=0
    #for i in h[idx:] : 
    for i in h[:idx] : 
        if j == 0 : d = i
        else : d = d + '.' + i
        j = j + 1
    return d

def getIP(host_name):
    try:
        #host_name = socket.gethostname()
        host_ip = socket.gethostbyname(host_name)
        #print("Hostname :  ",host_name)
        #print("IP : ",host_ip)
        return host_ip
    except:
        return "Unable.to.get.an.IP"

def getIPReversed(host_name):
    try:
       ip=[ele for ele in reversed(getIP(host_name).split('.'))]
       ipr=''
       for p in ip :
          if ipr : ipr=ipr+"."+p
          else : ipr=ipr + p       
       return ipr
    except:
       return "Unable.to.get.a.Reverse.IP"

def findSitenameOld(h):
    mapHostSitename = []
    #print (' h ',h )
    ip=''
    jlen = len(h.split('.'))
    jd   = h.split('.')[-2:]
    jd.sort()
    if 'in2p3.fr' in h : 
       #print ("findSitenames getIP for ",h)
       ip=getIPReversed(h)
       #print ( getIP(h), ip )
       #print ("findSitenames getIP for ",h, " is ",ip)
       jlen = len(ip.split('.'))
       jd   = ip.split('.')[-2:]
       jd.sort()
    #print (' h ip jlen jd ',h,ip,jlen,jd)

    nmatch=0
    matched_site=''
    matched_domain=''
    for site in sites.keys() :
        sited = sites[site]['hosts'][0].split(".")[-2:]
        if 'in2p3.fr' in h : sited = getIPReversed ( sites[site]['hosts'][0] ).split(".")[-2:]
        for idx in range ( len ( sites[site]['hosts'] ) ):
           sited = sites[site]['hosts'][idx].split(".")[-2:]
           sited.sort()
           if 'in2p3.fr' in h : 
              sited = getIPReversed ( sites[site]['hosts'][idx] ).split(".")[-2:]
              sited.sort()
           #if site == 'T2_US_Vanderbilt' : 
           #print ( 'host ',sites[site]['hosts'][idx], ' jd ',jd, ' sited ',sited )
           if jd == sited : break
        #if site == 'T2_US_Vanderbilt' : print (site, ' length ',len(sites[site]['flavors']), ' jd ',jd, ' sited ',sited)
        if jd != sited : continue
        if not "XROOTD" in set(sites[site]['flavors']) : continue
        #socket.gethostbyname('sbgse1.in2p3.fr')
        for i in range(len(sites[site]['flavors'])) :
            for j in range(1, jlen):
                   adomain=findDomain(h,j)
                   bdomain=findDomain(sites[site]['hosts'][i],j)
                   if 'in2p3.fr' in h :
                      adomain=findDomain( ip , j)
                      bdomain=findDomain( getIPReversed ( sites[site]['hosts'][i] ), j)

                   #print ( " j ", j, " adomain ",adomain, " bdomain ",bdomain)
                   if adomain == bdomain :
                      #print ( " returns j ", j, " adomain ",adomain, " bdomain ",bdomain)
                      #len(adomain.split('.'))
                      #if jlen - j > nmatch :
                      if len(adomain.split('.')) > nmatch :      
                         matched_site=sites[site]['sites'][i]
                         nmatch = len(adomain.split('.')) # jlen - j
                         matched_domain=findDomain(adomain,nmatch)
        #if jd == sited : print (h, site)
        #if mapHostSitename : mapHostSitename[h] = []
        #print ( "appending site ",site)
        mapHostSitename.append ( site )
        #mapHostSitename.append ( "m="+matched_site )
        #mapHostSitename.append ( matched_site )
    #if len( mapHostSitename ) > 1 and len ( matched_domain.split(".") ) < 3 :
    #       print ( h, matched_site, mapHostSitename)
    return (matched_site, matched_domain)

def findSitename(h):
    global sites
    gredirs = getGlobalRedirectors()
    for idx in range ( len (gredirs['hosts']) ) :
        if h in gredirs['hosts'][idx] :
           return ( gredirs['sites'][idx], 'TOBEFIXED')

    mapHostSitename = []
    #print (' h ',h )
    ip=''
    jlen = len(h.split('.'))
    jd   = h.split('.')[-2:]
    jd.sort()
    if 'in2p3.fr' in h : 
       #print ("findSitenames getIP for ",h)
       ip=getIPReversed(h)
       #print ( getIP(h), ip )
       #print ("findSitenames getIP for ",h, " is ",ip)
       jlen = len(ip.split('.'))
       jd   = ip.split('.')[-2:]
       jd.sort()
    #print (' h ip jlen jd ',h,ip,jlen,jd)

    nmatch=0
    matched_site=''
    matched_domain=''
    for stype in [ 'xrootd','all' ] :
      for site in sites.keys() :
        sited = sites[site]['hosts'][0].split(".")[-2:]
        if 'in2p3.fr' in h : sited = getIPReversed ( sites[site]['hosts'][0] ).split(".")[-2:]
        for idx in range ( len ( sites[site]['hosts'] ) ):
           sited = sites[site]['hosts'][idx].split(".")[-2:]
           sited.sort()
           if 'in2p3.fr' in h : 
              sited = getIPReversed ( sites[site]['hosts'][idx] ).split(".")[-2:]
              sited.sort()
           #if site == 'T2_US_Vanderbilt' : 
           #print ( 'host ',sites[site]['hosts'][idx], ' jd ',jd, ' sited ',sited )
           if jd == sited : break
        #if site == 'T2_US_Vanderbilt' : print (site, ' length ',len(sites[site]['flavors']), ' jd ',jd, ' sited ',sited)
        if jd != sited : continue
        #print (" jd found ",jd )
        if stype == 'xrootd' :
           if not "XROOTD" in set(sites[site]['flavors']) : continue
        #socket.gethostbyname('sbgse1.in2p3.fr')
        for i in range(len(sites[site]['flavors'])) :
            for j in range(1, jlen):
                   adomain=findDomain(h,j)
                   bdomain=findDomain(sites[site]['hosts'][i],j)
                   if 'in2p3.fr' in h :
                      adomain=findDomain( ip , j)
                      bdomain=findDomain( getIPReversed ( sites[site]['hosts'][i] ), j)

                   #print ( " j ", j, " adomain ",adomain, " bdomain ",bdomain)
                   if adomain == bdomain :
                      #print ( " returns j ", j, " adomain ",adomain, " bdomain ",bdomain)
                      #len(adomain.split('.'))
                      #if jlen - j > nmatch :
                      if len(adomain.split('.')) > nmatch :      
                         matched_site=sites[site]['sites'][i]
                         nmatch = len(adomain.split('.')) # jlen - j
                         matched_domain=findDomain(adomain,nmatch)
        #if jd == sited : print (h, site)
        #if mapHostSitename : mapHostSitename[h] = []
        #print ( "appending site ",site)
        #mapHostSitename.append ( site )
        #mapHostSitename.append ( "m="+matched_site )
        #mapHostSitename.append ( matched_site )
      if matched_site : break

    #if len( mapHostSitename ) > 1 and len ( matched_domain.split(".") ) < 3 :
    #       print ( h, matched_site, mapHostSitename)
    return (matched_site, matched_domain)

def updateHostSitename ( h, site ) :
    #HostSitenames[h] = {}
    HostSitenames[h] = site
    with open(THEPATH+'mapHostSitenames.py','w') as data: 
      data.write('HostSitenames = ' + str(HostSitenames))

def updateSiteStorage ( site , storage ) :
    #SiteStorages[ site ] = {}
    SiteStorages[ site ] = storage
    with open(THEPATH+'siteStoages.py','w') as data: 
      data.write('SiteStorages = ' + str(SiteStorages))


def getRegionalRedirectors ():
    global xrdmapc_output_prod
    global xrdmapc_output_prod_2

    #Lines=[]
    #with open(THEPATH+'out/xrdmapc_all_0.txt') as f: Lines = f.readlines()
    regionalRedirectors = {}
    count = 0 
    #for line in set(Lines) :
    for line in xrdmapc_output_prod.splitlines() :
        if type (line) is not str : line = line.decode() # python3
        #print("Line{}: {}".format(count, line.split()))
        entries=line.split()
        #if 'Man' in entries[1] :
        if entries[1] == 'Man' :
           #print ( "found Man in ",entries[1] )
           if int (entries[0]) == 1 :
              endpoint = entries[2]
              host = endpoint.split(':')[0]
              if host in HostSitenames :
                 site=HostSitenames[host]
              else :
                 (site,domain) = findSitename(host)
                 updateHostSitename ( host, site ) 
              regionalRedirectors[site] = {}
              regionalRedirectors[site]['endpoint'] = endpoint
              regionalRedirectors[site]['host'] = host
              regionalRedirectors[site]['flavors'] = 'XROOTD'
              regionalRedirectors[site]['federation'] = 'prod'

        #count += 1
    #print ( regionalRedirectors )
    return regionalRedirectors 

def getRegionalRedirectorsFromFile ():
    Lines=[]
    with open(THEPATH+'out/xrdmapc_all_0.txt') as f: Lines = f.readlines()
    regionalRedirectors = {}
    #count = 0 
    for line in set(Lines) :
        #print("Line{}: {}".format(count, line.split()))
        entries=line.split()
        if entries[1] == 'Man' :
           if int (entries[0]) == 1 :
              endpoint = entries[2]
              host = endpoint.split(':')[0]
              if host in HostSitenames :
                 site=HostSitenames[host]
              else :
                 (site,domain) = findSitename(host)
                 updateHostSitename ( host, site ) 
              regionalRedirectors[site] = {}
              regionalRedirectors[site]['endpoint'] = endpoint
              regionalRedirectors[site]['host'] = host
              regionalRedirectors[site]['flavors'] = 'XROOTD'
              regionalRedirectors[site]['federation'] = 'prod'

        #count += 1
    #print ( regionalRedirectors )
    return regionalRedirectors


def getXrootdServers () :
    global xrdmapc_output_prod
    global xrdmapc_output_prod_2
    global sites
    #Lines=[]
    #print ("DEBUG sites ",len ( sites ))
    xrdServers = {}
    for site in sites :
        #print ( ' site ',site )
        xrdServers[site] = {}
        xrdServers[site]['endpoints'] = []
        xrdServers[site]['hosts'] = []
        xrdServers[site]['federation'] = []
        xrdServers[site]['flavors'] = []
    #return xrdServers
    count = 0 
    for line in xrdmapc_output_prod.splitlines() :
        print("Line{}: {}".format(count, line.split()))
        if type (line) is not str : line = line.decode()
        entries=line.split()
        #print ( entries )
        #if entries[0] == 'Srv' :
        idx = 0
        if entries[1] == 'Man' : idx = 2
        if entries[0] == 'Srv' : idx = 1
        if idx == 1 or idx == 2 :
           endpoint = entries[idx]
           host = endpoint.split(':')[0]
           if '[' in endpoint : continue
           #(site,domain) = findSitename(host)
           #from mapHostSitenames import HostSitenames
           if host in HostSitenames :
              site=HostSitenames[host]
           else :
              if 'localhost' in host : continue # give up
              (site,domain) = findSitename(host)
              updateHostSitename ( host, site )
           #print ( " host and site ",host, site ) 
           #print ( "DEBUG xrdServers[site]['endpoints'] ", xrdServers[site]['endpoints'] )
           #if '[::ffff:144.16.111.9]:11001' in endpoint :
           #   site = 'T2_IN_TIFR'
           #   xrdServers[site]['endpoints'].append('se01.indiacms.res.in:11001')
           #   xrdServers[site]['hosts'].append ( 'se01.indiacms.res.in' )
           #   xrdServers[site]['federation'].append ( 'prod' )
           #print ( endpoint, host, site )
           #if 'unl.edu' in endpoint : print ( endpoint, host , site, domain)
           # addhoc
           #if not site :
           #   #if 'vanderbilt.edu' in host : site = 'T2_US_Vanderbilt'

           #xrdServers[site] = {}
           #print ( " site ",site)
           #if site == 'T2_US_Nebraska' : print ( 'T2_US_Nebraska ', endpoint )
           #if '[::ffff:144.16.111.9]:11001' in endpoint :
           #    xrdServers[site]['endpoints'].append('se01.indiacms.res.in:11001')
           #else :
           #if 'localhost' in site:
           #   print (" site has localhost")
           #   xrdServers[site]={} #'endpoints':'','hosts':'','flavors':'','federation':''}
           #   xrdServers[site]['endpoints']=['localhost']
           #   xrdServers[site]['hosts']=[host]
           #   xrdServers[site]['flavors']=['XROOTD']
           #   xrdServers[site]['federation']=['prod']
           #else:
           if not endpoint in xrdServers[site]['endpoints'] :
              xrdServers[site]['endpoints'].append ( endpoint )
              xrdServers[site]['hosts'].append ( host  )
              xrdServers[site]['flavors'].append ( 'XROOTD' )
              xrdServers[site]['federation'].append ( 'prod' )
           #print("Line{}: {}".format(count, line.split()), ' idx = ',idx, endpoint,site,xrdServers[site]['federation'])

        #count += 1
    #print ("Returning xrdServers")
    return xrdServers

def getXrootdServersFromFile () :
    global sites
    Lines=[]
    with open(THEPATH+'out/xrdmapc_all_0.txt') as f: Lines = f.readlines()
    print ("DEBUG sites ",len ( sites ))
    xrdServers = {}
    for site in sites :
        #print ( ' site ',site )
        xrdServers[site] = {}
        xrdServers[site]['endpoints'] = []
        xrdServers[site]['hosts'] = []
        xrdServers[site]['federation'] = []
        xrdServers[site]['flavors'] = []
    #return xrdServers
    count = 0 
    for line in Lines :
        #print("Line{}: {}".format(count, line.split()))
        entries=line.split()
        #print ( entries )
        #if entries[0] == 'Srv' :
        idx = 0
        if entries[1] == 'Man' : idx = 2
        if entries[0] == 'Srv' : idx = 1
        if idx == 1 or idx == 2 :
           endpoint = entries[idx]
           host = endpoint.split(':')[0]
           if '[' in endpoint : continue
           #(site,domain) = findSitename(host)
           #from mapHostSitenames import HostSitenames
           if host in HostSitenames :
              site=HostSitenames[host]
           else :
              (site,domain) = findSitename(host)
              updateHostSitename ( host, site )
           #print ( host, site ) 
           #print ( xrdServers[site]['endpoints'] )
           #if '[::ffff:144.16.111.9]:11001' in endpoint :
           #   site = 'T2_IN_TIFR'
           #   xrdServers[site]['endpoints'].append('se01.indiacms.res.in:11001')
           #   xrdServers[site]['hosts'].append ( 'se01.indiacms.res.in' )
           #   xrdServers[site]['federation'].append ( 'prod' )
           #print ( endpoint, host, site )
           #if 'unl.edu' in endpoint : print ( endpoint, host , site, domain)
           # addhoc
           #if not site :
           #   #if 'vanderbilt.edu' in host : site = 'T2_US_Vanderbilt'

           #xrdServers[site] = {}
           #print ( " site ",site)
           #if site == 'T2_US_Nebraska' : print ( 'T2_US_Nebraska ', endpoint )
           #if '[::ffff:144.16.111.9]:11001' in endpoint :
           #    xrdServers[site]['endpoints'].append('se01.indiacms.res.in:11001')
           #else :
           if not endpoint in xrdServers[site]['endpoints'] :
              xrdServers[site]['endpoints'].append ( endpoint )
              xrdServers[site]['hosts'].append ( host  )
              xrdServers[site]['flavors'].append ( 'XROOTD' )
              xrdServers[site]['federation'].append ( 'prod' )
           #print("Line{}: {}".format(count, line.split()), ' idx = ',idx, endpoint,site,xrdServers[site]['federation'])

        #count += 1
    return xrdServers

def getTransitionalXrootds () :
    global sites
    global xrdmapc_output_tran
    #Lines=[]
    #with open(THEPATH+'out/xrdmapc_trans_3.txt') as f: Lines = f.readlines()
    xrdServers = {}
    #print ("DEBUG sites ",sites.keys())
    for site in sites :
        #print ( ' site ',site )
        xrdServers[site] = {}
        xrdServers[site]['endpoints'] = []
        xrdServers[site]['hosts'] = []
        xrdServers[site]['federation'] = []
        xrdServers[site]['flavors'] = []
    #return xrdServers
    #count = 0 
    for line in xrdmapc_output_tran.splitlines() :
        if type (line) is not str : line = line.decode()
        #print("Line{}: {}".format(count, line.split()))
        entries=line.split()
        #print ( entries 
        idx = 0
        if entries[1] == 'Man' : idx = 2
        if entries[0] == 'Srv' : idx = 1
        if idx == 1 or idx == 2 :
           endpoint = entries[idx]
           host = endpoint.split(':')[0]
           #(site,domain) = findSitename(host)
           #from mapHostSitenames import HostSitenames
           if '[' in endpoint: continue

           if host in HostSitenames :
              #print (' if host = ',host, ' HostSitenames ',HostSitenames )
              site=HostSitenames[host]
              if not site :
                 (site,domain) = findSitename(host)
                 updateHostSitename ( host, site ) 
           else :
              #print (' else host = ',host )
              (site,domain) = findSitename(host)
              updateHostSitename ( host, site ) 
              #print (' else host = ',host, ' site ',site )
           if not endpoint in xrdServers[site]['endpoints'] :
              xrdServers[site]['endpoints'].append ( endpoint )
              xrdServers[site]['hosts'].append ( host  )
              xrdServers[site]['flavors'].append ( 'XROOTD' )
              xrdServers[site]['federation'].append ( 'trans' )
              #print (' endpoint ',endpoint )
 
        #count += 1
    return xrdServers

def getXrootdsFromTransFile () :
    global sites
    Lines=[]
    with open(THEPATH+'out/xrdmapc_trans_3.txt') as f: Lines = f.readlines()
    xrdServers = {}
    #print ("DEBUG sites ",sites.keys())
    for site in sites :
        #print ( ' site ',site )
        xrdServers[site] = {}
        xrdServers[site]['endpoints'] = []
        xrdServers[site]['hosts'] = []
        xrdServers[site]['federation'] = []
        xrdServers[site]['flavors'] = []
    #return xrdServers
    #count = 0 
    for line in Lines :
        #print("Line{}: {}".format(count, line.split()))
        entries=line.split()
        #print ( entries 
        idx = 0
        if entries[1] == 'Man' : idx = 2
        if entries[0] == 'Srv' : idx = 1
        if idx == 1 or idx == 2 :
           endpoint = entries[idx]
           host = endpoint.split(':')[0]
           #(site,domain) = findSitename(host)
           #from mapHostSitenames import HostSitenames
           if '[' in endpoint: continue

           if host in HostSitenames :
              #print (' if host = ',host, ' HostSitenames ',HostSitenames )
              site=HostSitenames[host]
              if not site :
                 (site,domain) = findSitename(host)
                 updateHostSitename ( host, site ) 
           else :
              #print (' else host = ',host )
              (site,domain) = findSitename(host)
              updateHostSitename ( host, site ) 
              #print (' else host = ',host, ' site ',site )
           if not endpoint in xrdServers[site]['endpoints'] :
              xrdServers[site]['endpoints'].append ( endpoint )
              xrdServers[site]['hosts'].append ( host  )
              xrdServers[site]['flavors'].append ( 'XROOTD' )
              xrdServers[site]['federation'].append ( 'trans' )
              #print (' endpoint ',endpoint )
 
        #count += 1
    return xrdServers

def queryXrdmapc (redirector) :
    global sites
    global xrdmapc_output_prod
    global xrdmapc_output_prod_2
    global xrdmapc_output_tran
    if 'trans' in redirector :
        (err_info,xrdmapc_output_tran,dump_info) = xrd_info(redirector,'')
        with open(THEPATH+'out/xrdmapc_tran.txt','w' ) as f:
           for line in xrdmapc_output_tran.splitlines() :
               #f.write(str(line.decode()))
               if type (line) is str :
                  #print ( "1 str "+line )
                  f.write(line)
               else :
                  #print ( "1 no str "+str(line.decode()) )
                  f.write(str(line.decode()))
               f.write('\n')
    elif 'global02' in redirector :
        (err_info,xrdmapc_output_prod_2,dump_info) = xrd_info(redirector,'')
        with open(THEPATH+'out/xrdmapc_prod_2.txt','w' ) as f: 
           for line in xrdmapc_output_prod_2.splitlines() :
               if type (line) is str :
                  #print ( "2 str "+line )
                  f.write(line)
               else :
                  #print ( "2 no str "+str(line.decode()) )
                  f.write(str(line.decode()))
               f.write('\n')
    else :
        (err_info,xrdmapc_output_prod,dump_info) = xrd_info(redirector,'')
        with open(THEPATH+'out/xrdmapc_prod_1.txt','w' ) as f:
           for line in xrdmapc_output_prod.splitlines() :
               #f.write(str(line.decode()))
               if type (line) is str :
                  #print ( "3 str "+line )
                  f.write(line)
               else :
                  #print ( "3 no str "+str(line.decode()) )
                  f.write(str(line.decode()))
               f.write('\n')


def updateXrdInfo (thesite) :
    global sites
    xrdInfo = sites[thesite]
    xrd_idxes = findXROOTDIdxes ( xrdInfo )
    #print ( thesite, sites[thesite] )
    for idx in range(len(xrd_idxes)) :
       endpoint = sites[thesite]['endpoints'][xrd_idxes[idx]]
       (err_info,xrootd_version,dump_info) = xrd_info(endpoint,"version")
       #xrdInfo['xrootd_version'][xrd_idxes[idx]] = xrootd_version
       sites[thesite]['xrootd_version'][xrd_idxes[idx]] = xrootd_version
       (err_info,xrootd_role,dump_info) = xrd_info(endpoint,"role")
       #xrdInfo['xrootd_role'][xrd_idxes[idx]] = xrootd_role
       sites[thesite]['xrootd_role'][xrd_idxes[idx]] = xrootd_role
       #print ("DEBUG updateXrdInfo ",thesite, sites[thesite]['endpoints'], " xrootd_role ",xrootd_role, " xrootd_version ",xrootd_version)
       if not 'timeout' in xrootd_role and not 'FATAL' in xrootd_role :
          if not 'timeout' in xrootd_version and not 'FATAL' in xrootd_version :
           updatexrdVersions ( endpoint, xrootd_role, xrootd_version )
           #if not xrootd_version in XrdVersions[endpoint]['xrootd_version'] or not xrootd_role in XrdVersions[endpoint]['xrootd_role'] : 
           #    updatexrdVersions ( endpoint, xrootd_role, xrootd_version )
       from xrdVersions import XrdVersions
       if endpoint in XrdVersions : 
          if 'timeout' in xrootd_role or 'FATAL' in xrootd_role :
              #print ( "( endpont )",endpoint )
              xrootd_role = XrdVersions[endpoint]['Role']
              #sites[thesite]['xrootd_role'][xrd_idxes[idx]] = '['+xrootd_role+']'
              #if 'timeout' in xrootd_version or 'FATAL' in xrootd_version : sites[thesite]['xrootd_version'][xrd_idxes[idx]] = '['+XrdVersions[endpoint]['Version']+']'
              sites[thesite]['xrootd_role'][xrd_idxes[idx]] = xrootd_role
          if 'timeout' in xrootd_version or 'FATAL' in xrootd_version : sites[thesite]['xrootd_version'][xrd_idxes[idx]] = XrdVersions[endpoint]['Version']


#def updateFederation (thesite) :
#    xrdInfo = sites[thesite]
#    xrd_idxes = findXROOTDIdxes ( xrdInfo )
#    #print ( thesite, sites[thesite] )
#    for idx in range(len(xrd_idxes)) :
#       endpoint = sites[thesite]['endpoints'][xrd_idxes[idx]]
#       (err_info,xrootd_version,dump_info) = xrd_info(endpoint,"version")
#       #xrdInfo['xrootd_version'][xrd_idxes[idx]] = xrootd_version
#       sites[thesite]['federation'][xrd_idxes[idx]] = xrootd_version
#       (err_info,xrootd_role,dump_info) = xrd_info(endpoint,"role")
#       #xrdInfo['xrootd_role'][xrd_idxes[idx]] = xrootd_role
#       sites[thesite]['xrootd_role'][xrd_idxes[idx]] = xrootd_role

def updateContactInfo () :
    global sites
    for site in sites :
        xrdInfo = sites[site]
        xrd_idxes = findXROOTDIdxes ( xrdInfo )
        contact = ''
        for contact in sites[site]['contact'] : 
            if '@' in contact : break
        for idx in range(len(xrd_idxes)) :
            #sites[site]['contact'][xrd_idxes[idx]] = contact
            sites[site]['contact'][xrd_idxes[idx]] = contact.replace('@cern.ch','')

def findXROOTDIdxes (thesite) :
    idxes=[]
    i=0
    for flavor in thesite['flavors'] :
        if flavor == 'XROOTD' : idxes.append(i)
        i += 1
    if len(idxes) == 0 :
       i=0
       for flavor in thesite['flavors'] :
           if flavor == 'WEBDAV' : idxes.append(i)
           i += 1

    return idxes
def runqueryXrdmapc () :
    signal.signal(signal.SIGALRM, alarm_handler)
    try:
        threads = list()
        for redirector in topRedirectors: 
            if 1 == 0 :
               queryXrdmapc (redirector+':1094')
            else :
               t = threading.Thread(target=queryXrdmapc, args=(redirector+':1094',))
               threads.append(t)
               t.start()
        print ("Start joining threads ")
        for xrd, thread in enumerate(threads):
            #print ("Before joining thread ", site)
            thread.join()
        print ("All threads done ")
    except Alarm:
        print ("ERROR: caught overall timeout after "+str(timeout_sec)+"s\n")
        #clear_lock()
        #sys.exit(2)
    signal.alarm(0)

def runThreadedupdateXrdInfo () :

    signal.signal(signal.SIGALRM, alarm_handler)
    try:
        threads = list()
        for site in sites: 
            if 1 == 0 :
               updateXrdInfo (site)
            else :
               t = threading.Thread(target=updateXrdInfo, args=(site,))
               threads.append(t)
               t.start()
        print ("Start joining threads ")
        for site, thread in enumerate(threads):
            #print ("Before joining thread ", site)
            thread.join()
        print ("All threads done ")
    except Alarm:
        print ("ERROR: caught overall timeout after "+str(timeout_sec)+"s\n")
        #clear_lock()
        #sys.exit(2)
    signal.alarm(0)


#with open(THEPATH+'exceptions.json') as f: exc = f.read()
#exc = json.loads(exc)

#def exception(name):
#    ret = None
#    for i in exc.keys():
#	if i == name : return exc[i]['VOname']
#    return ret


#def siteName2CMSSiteName(dom):
#    ret = None
#    for cmsSite in sites.keys():
#        ret = exception(dom)
#	if ret :
#	    ret = str(ret)
#	    return ret   
#	if sites[cmsSite]['hosts'][0].find(dom) != -1:
#            return cmsSite
#    return ret

def jsonSorting(item):
    if isinstance(item, dict):
        return sorted((key, jsonSorting(values)) for key, values in item.items())
    if isinstance(item, list):
        return sorted(jsonSorting(x) for x in item)
    else:
        return item

def getAllSiteRedirectors () :
   global sites
   try :
      print ( 'DEBUG Doing getSites' )
      sites = getSites()

      print ( 'DEBUG Doing gRedirs ')
      gredirs = getGlobalRedirectors()

      print ( 'DEBUG Doing rRedirs ')
      #regionalRedirectors = getRegionalRedirectorsFromFile()
      regionalRedirectors = getRegionalRedirectors ()
      #print ( 'DEBUG regionalRedirectors ', regionalRedirectors ) 
      print ( 'DEBUG Doing xrdServers ')
      #xrdProdServers = getXrootdServersFromFile()
      xrdProdServers = getXrootdServers()
      #print ( 'DEBUG xrdProdServers ', xrdProdServers )
      print ( 'DEBUG Doing xrd from trans redirector ')
      #xrdTranServers = getXrootdsFromTransFile()
      xrdTranServers = getTransitionalXrootds()
      #print ( 'DEBUG xrdTranServers ', xrdTranServers)
      for site in sites.keys():
        #print ( 'DEBUG Doing site g ',site )
        if 'T0_CH_CERN' in site :
          for sitekey in sites[site].keys() :
               for siteval in gredirs[sitekey] :
                  sites[site][sitekey].append(siteval)
        #print ( 'Doing site r ',site )
        #if 'cmsxrootd-site3.fnal.gov:1094' in sites[site]['endpoints'] :
        #print ( ' before regional ', site, ' has it in ', sites[site]['endpoints'] ) 
        if site in regionalRedirectors : #.has_key(site):
          for sitekey in sites[site].keys() :

              #print (" site RR ",site, " sitekey ",sitekey, sites[site][sitekey])

              if 'sites' in sitekey : sites[site][sitekey].append( site )
              elif 'hosts' in sitekey : sites[site][sitekey].append( regionalRedirectors[site]['host'] )
              elif 'flavors' in sitekey : sites[site][sitekey].append( 'XROOTD' )
              elif 'endpoints' in sitekey : sites[site][sitekey].append( regionalRedirectors[site]['endpoint'] )
              elif 'name' in sitekey : sites[site][sitekey].append( 'RR_service_from_'+site )
              elif 'xrootd_version' in sitekey :
                   #(err_info,xrootd_version,dump_info) = xrd_info(regionalRedirectors[site]['endpoint'],"version")
                   sites[site][sitekey].append( '' )
              elif 'xrootd_role' in sitekey :
                   #(err_info,xrootd_role,dump_info) = xrd_info(regionalRedirectors[site]['endpoint'],"role")
                   sites[site][sitekey].append( '' )
              elif 'xrootd_servers' in sitekey : sites[site][sitekey].append( 'RR' )
              elif 'xrootd_storage' in sitekey : 
                   if SiteStorages[ site ] : xrootd_storage = SiteStorages[ site ]
                   else : 
                      xrootd_storage = getStorageFromStorageJson ( site )
                      updateSiteStorage ( site , xrootd_storage )

                   sites[site][sitekey].append( xrootd_storage )
              elif 'federation' in sitekey : sites[site][sitekey].append( 'prod' )
              else :
                   sites[site][sitekey].append( 'RR' )
        #if 'cmsxrootd-site3.fnal.gov:1094' in sites[site]['endpoints'] :
        #   print ( ' after regional ', site, ' has it in ', sites[site]['endpoints'] ) 
        ic = 0
        for xrdServers in [ xrdProdServers, xrdTranServers ] :
          #ic = ic + 1 #print ( 'Doing xrdServers ',xrdServers ) #site x ',site, ' endpoints count ', xrdServers[site]['endpoints']  )
          if site in xrdServers : #.has_key(site):
            #print (' xrdServers has key ic site ',ic,site, xrdServers[site])
            for idx in range ( len ( xrdServers[site]['endpoints'] ) ) :
              if xrdServers[site]['endpoints'][idx] in sites[site]['endpoints'] : 
                  #xrdInfo = sites[site]
                  #if xrdServers[site]['endpoints'][idx] == 'cmsxrootd-site1.fnal.gov:1094' : print ( site, "will update  sites[site]['endpoints'] for ",xrdServers[site]['endpoints'][idx], xrdInfo ) #updateFederation (site) #
                  #xrd_idxes = findXROOTDIdxes ( xrdInfo )
                  for xrd_idx in range(len( sites[site]['endpoints'] )) :
                       #if xrdServers[site]['endpoints'][idx] == 'cmsxrootd-site1.fnal.gov:1094' : #updateFederation (site) #
                       #     print ( site, "will update  sites[site]['endpoints'] for ",xrdServers[site]['endpoints'][idx], ' vs ',sites[site]['endpoints'][xrd_idx])
                       if xrdServers[site]['endpoints'][idx] in sites[site]['endpoints'][xrd_idx] :
                         #if xrdServers[site]['endpoints'][idx] == 'cmsxrootd-site1.fnal.gov:1094' : #updateFederation (site) #
                         #   print ( site, "will update  sites[site]['endpoints'] for ",xrdServers[site]['endpoints'][idx])
                         #sites[site]['endpoints'][xrd_idx] =  xrdServers[site]['endpoints'][idx]
                         #sites[site]['hosts'][xrd_idx] =  xrdServers[site]['hosts'][idx]
                         #sites[site]['flavors'][xrd_idx] =  xrdServers[site]['flavors'][idx]
                         sites[site]['federation'][xrd_idx] =  xrdServers[site]['federation'][idx]
                  #print ( 'skipping site idx ',site,idx,xrdServers[site]['endpoints'][idx],sites[site]['endpoints'])
                  continue
              #for sitekey in sites[site].keys() :
              #for sitekey in sites[site].keys() :
              #print ( 'Doing site x site ',site, ' n endpoints ',len ( xrdServers[site]['endpoints'] ), ' endpoint ',xrdServers[site]['endpoints'][idx])
              #for idx in range ( len ( xrdServers[site]['endpoints'] ) ) :
              #if not 'sites' in sitekey : continue
              #print ( 'Doing site x ',site )
              #print ( 'Doing site x site ',site, ' n endpoints ',len ( xrdServers[site]['endpoints'] ), ' idx ', idx, ' endpoint ',xrdServers[site]['endpoints'][idx])

              sites[site]['sites'].append( site )
              sites[site]['hosts'].append( xrdServers[site]['hosts'][idx] )
              sites[site]['flavors'].append( 'XROOTD' )
              sites[site]['endpoints'].append( xrdServers[site]['endpoints'][idx] )
              sites[site]['name'].append( 'Xrootd_Servers_from_'+site )
              sites[site]['xrootd_version'].append( 'unknown' )
              sites[site]['xrootd_role'].append( 'server' )
              sites[site]['xrootd_servers'].append( xrdServers[site]['hosts'][idx] )
              xrootd_storage = 'uninitialized'
              if SiteStorages[ site ] : xrootd_storage = SiteStorages[ site ]
              else : 
                  xrootd_storage = getStorageFromStorageJson ( site )
                  updateSiteStorage ( site , xrootd_storage )

              sites[site]['xrootd_storage'].append( xrootd_storage )
              sites[site]['contact'].append( site )
              sites[site]['federation'].append( xrdServers[site]['federation'][idx] )

              #print ( 'Doing site x ',site, sites[site])
        updateContactInfo()
      return sites
   except Exception as e :
      err={}
      err["error"] = str(e)
      #print (json.dumps(err))
      print ( err )
      sys.exit(1)

#for site in sites :
#    idxes = findXROOTDIdxes (sites[site])
#    #print ( ' site ', site, ' fed ',sites [ site ]['federation'], ' endpoint ',sites [ site ]['endpoints'] )
#    for idx in idxes :
#       if sites [ site ]['flavors'][idx] == 'XROOTD' :
#        print ( ' site ', site, 'idx ',idx, ' fed ',sites [ site ]['federation'][idx], ' endpoint ',sites [ site ]['endpoints'][idx] )
##    if 'T2_US_Florida' in site :
##        for key in sites [site] :
##            print ( len (sites[site][key]), key, sites[site][key] )

#sys.exit(0)

# Checks if a hostname is an alias or not
def getDNSARecords ( h ):
    import dns.resolver
    #import socket
    if h in DNSARecords : #.has_key (h) :
       if DNSARecords[h]['Alias'] == True :
         return ( DNSARecords[h]['Alias'], DNSARecords[h]['A'] )

    isAlias = False
    aRecords = []
    try :
      result = dns.resolver.query(h, 'A')
      for ipval in result:
        ip = ipval.to_text()
        (host, alias, ipl) = socket.gethostbyaddr(ip)
        aRecords.append (host)
      if len(aRecords) > 1 : 
        isAlias = True
      #print ("Updating DNS Records for h = ", h)
      updateDNSARecords ( h, isAlias, aRecords )
      return (isAlias, aRecords)
    except Exception as e :
      print ("Exception h ",h, " ",e)
      return (isAlias, aRecords)
      
def updateDNSARecords ( h, isAlias, aRecords ) :
    #if not DNSARecords.has_key (h) : 
    DNSARecords[ h ] = {'Alias' : isAlias, 'A' : aRecords }
    with open(THEPATH+'DNSARecords.py','w') as data:
       #print ( 'DNSARecords = ' + str(DNSARecords) )
       data.write('DNSARecords = ' + str(DNSARecords))

def updatexrdVersions ( endpoint, role, version ) :
    #if not DNSARecords.has_key (h) : 
    XrdVersions[ endpoint ] = {'Role' : role, 'Version' : version }
    with open(THEPATH+'xrdVersions.py','w') as data:
       data.write('XrdVersions = ' + str(XrdVersions))

class MyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, bytes):
            return str(obj, encoding='utf-8');
        return json.JSONEncoder.default(self, obj)

if __name__ == "__main__":
    # run xrdmapc against the global redirector and the transitional redirector
    runqueryXrdmapc ()

    # get all redirectors from the hardwired way or the vofeed or the xrdmapc output
    sites = getAllSiteRedirectors ()

    # fill xrootd version and xrootd role in a threaded way
    runThreadedupdateXrdInfo ()

    #
    #if 1 == 0 :
    for site in sites :
        idxes = findXROOTDIdxes (sites[site])
        for idx in idxes :
            xrdv = sites [ site ]['xrootd_version'][idx]
            endpoint = sites [ site ]['endpoints'][idx]
            xrdr = sites [ site ]['xrootd_role'][idx]
            if 'timeout' in xrdv :
               #(err_info,xrootd_version,dump_info) = xrd_info(endpoint,"version")
               #(err_info,xrootd_role,dump_info) = xrd_info(endpoint,"role")
               #sites [ site ]['xrootd_version'][idx] = xrootd_version
               print ( site, endpoint,xrdv) # " version new ",xrootd_version)
            if 'timeout' in xrdr :
               #(err_info,xrootd_version,dump_info) = xrd_info(endpoint,"version")
               #(err_info,xrootd_role,dump_info) = xrd_info(endpoint,"role")
               #sites [ site ]['xrootd_role'][idx] = xrootd_role
               print ( site, endpoint,xrdr) # " role new ",xrootd_role)
    #


    federations={}
    for site in sites :
        idxes = findXROOTDIdxes (sites[site])
        for idx in idxes :
            # Update if the host is an alias and the federation is nowhere
            if ( 'T0_' in site or 'T1_' in site or 'T2_' in site ) and sites [ site ]['federation'][idx] == 'nowhere' :
              #print ( 'Doing getDNSRecords ', sites [ site ]['hosts'][idx] )
              (isAlias, A) = getDNSARecords ( sites [ site ]['hosts'][idx] )
              if isAlias :
                 aFound = True
                 shost = ''
                 for ar in A :
                     #print ( ' ar ',ar, ' hosts ', sites [ site ]['hosts'] )
                     if not ar in sites [ site ]['hosts'] : aFound = False
                     shost = ar
                     
                 if len (A) > 1 : 
                    if shost in sites [ site ]['hosts'] :
                       sites [ site ]['federation'][idx] = sites [ site ] ['federation'][sites [ site ]['hosts'].index ( shost )]
                    else :
                       print ( ' len(A) ', sites [site]['hosts'] )
                    
              #print ( ' site ', site, 'idx ',idx, ' fed ',sites [ site ]['federation'][idx], ' endpoint ',sites [ site ]['endpoints'][idx] , isAlias , aFound )
            #print ( ' site ', site, 'idx ',idx, ' fed ',sites [ site ]['federation'][idx], ' endpoint ',sites [ site ]['endpoints'][idx] )
            #output[sites[site]['federation'][idx]].append(sites[site])
            federations[sites[site]['federation'][idx]] = {}
    for federation in federations :
        for site in sites :
            idxes = findXROOTDIdxes (sites[site])
            for idx in idxes :
                if sites[site]['federation'][idx] in federation :
                   thesite = {}
                   thesite['sites'] = sites[site]['sites'][idx]
                   thesite['hosts'] = sites[site]['hosts'][idx]
                   thesite['flavors'] = sites[site]['flavors'][idx]
                   thesite['endpoints'] = sites[site]['endpoints'][idx]
                   thesite['name']  = sites[site]['name'][idx]
                   thesite['contact']  = sites[site]['contact'][idx]
                   thesite['xrootd_version']  = sites[site]['xrootd_version'][idx]
                   thesite['xrootd_role']  = sites[site]['xrootd_role'][idx]
                   thesite['xrootd_servers'] = sites[site]['xrootd_servers'][idx]
                   thesite['xrootd_storage'] = sites[site]['xrootd_storage'][idx]
                   thesite['federation'] = sites[site]['federation'][idx]
                   output[federation].append(thesite)
    #for federation in federations :
    #    for thesite in output[federation] :
    #        print (  federation, thesite )
    with open(THEPATH+'out/federations.json', 'w') as f:
        #f.write(json.dumps(output, indent = 1))
        f.write(json.dumps(output,cls=MyEncoder,indent=1))
    print ("Check ",THEPATH+'out/federations.json')
exit()
