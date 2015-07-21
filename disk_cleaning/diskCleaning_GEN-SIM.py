#!/usr/bin/env python

import sys,os,getopt,urllib,httplib,time,re

try:
    import json
except ImportError:
    import simplejson as json

def to_TB(amount):
    return "%.3fTB" % (amount / float(1000 ** 4))

def to_GB(amount):
    return "%.3fGB" % (amount / float(1000 ** 3))

# get method to parse given url which requires certificate
def geturl(url, request, retries=2):
    proxy = os.getenv('X509_USER_PROXY')
    if not proxy:
        proxy = "/tmp/x509up_u%s" % os.geteuid()

    conn  =  httplib.HTTPSConnection(url, cert_file = proxy,
                                            key_file = proxy)
    r1=conn.request("GET",request)
    r2=conn.getresponse()
    request = json.loads(r2.read())
    #try until no exception
    while 'exception' in request and retries > 0:
        conn  =  httplib.HTTPSConnection(url, cert_file = os.getenv('X509_USER_PROXY'),
                                                key_file = os.getenv('X509_USER_PROXY'))
        r1=conn.request("GET",request)
        r2=conn.getresponse()
        request = json.loads(r2.read())
        retries-=1
    if 'exception' in request:
        raise Exception('Maximum queries to ReqMgr exceeded',str(request))
    return request


node = None
datasetRegex='/*/*/GEN-SIM'
monthLimit = 6 # in Months
debugMode = False
try:
    opts, args = getopt.getopt(sys.argv[1:], "", ["node=","dataset=","monthlimit=","debug"])
except getopt.GetoptError:
    print  >> sys.stderr, 'Failed to parse options!'
    sys.exit(2)

# check command line parameter
for opt, arg in opts :
    if opt == "--node":
        node = arg
    elif opt == "--dataset":
        datasetRegex = arg
    elif opt == "--monthlimit":
        monthLimit = int(arg)
    elif opt == "--debug":
        debugMode = True

if node == None:
    print  >> sys.stderr, 'Please specify a node name with --node'
    sys.exit(2)
    
# Constant variables
urlPhedex = 'https://cmsweb.cern.ch/phedex/datasvc/json/prod/'
urlCMSWeb = 'cmsweb.cern.ch'
urlWMstats = '/couchdb/reqmgr_workload_cache/_design/ReqMgr/_view/'

# added "completed" Status as asked by Andrew - there may be some workflows that require ACDC etc
StatusOngoingWF = ["assigned","acquired","running","running-open","running-closed","assignment-approved","completed"]
datelimit = int(time.time()) - monthLimit*30*24*60*60
 
url = urlPhedex + 'blockreplicas?create_since=0&show_dataset=y&dataset=%s&node=%s' % (datasetRegex,node)
result = json.load(urllib.urlopen(url))
totalSize = long(0)
totalSizeAtSite = long(0)
for dataset in result['phedex']['dataset']:
    try:
        datasetName = str(dataset['name'])

        if debugMode: print >> sys.stderr, 'checking: %s' % datasetName

        # skip pileup samples
        if re.match(r'/MinBias.*/.*/GEN-SIM',datasetName):
            if debugMode: print >> sys.stderr, 'skipping pileup dataset: %s' % datasetName
            continue

        # check if custodial replica exists
        url = urlPhedex + 'blockreplicas?create_since=0&dataset=' + datasetName
        subResult = json.load(urllib.urlopen(url))
        custReplicaExist = False
        custReplicaComplete = False
        datasetSizeAtSite = 0
        datasetSize = 0
        for block in subResult['phedex']['block']:
            datasetSize += long(block['bytes'])
            for replica in block['replica']:
                if replica['node'] == node:
                    datasetSizeAtSite += long(replica['bytes'])
                if replica['custodial'] == "y":
                    custReplicaExist = True
                    if replica['complete'] == "y":
                        custReplicaComplete = True

            # if one of the blocks not have custodial replica or has non complete custodial replica, skip the dataset
            if not custReplicaExist or not custReplicaComplete:
                break

        if not custReplicaExist:
            if debugMode: print >> sys.stderr, 'skipping: no custodial replica exists'
            continue

        if not custReplicaComplete:
            if debugMode: print >> sys.stderr, 'skipping: custodial replica is not complete'
            continue

        # check if it's input dataset of an ongoing WF
        url = urlWMstats + 'byinputdataset?include_docs=true&reduce=false&key="%s"' % datasetName
        rows = geturl(urlCMSWeb, url)['rows']
        isInputOfOngoingWF = False
        inputWFs = []
        for row in rows:
            inputWFs.append("%s %s %s" % (row['id'],row['doc']['RequestTransition'][-1]['Status'], time.strftime('%Y-%m-%d', time.gmtime(row['doc']['RequestTransition'][-1]['UpdateTime']))))
            if row['doc']['RequestTransition'][-1]['Status'] in StatusOngoingWF:
                isInputOfOngoingWF = True
                break
        if isInputOfOngoingWF:
            if debugMode: print >> sys.stderr, 'skipping: used by an ongoing WF'
            continue

        
        # check if it's output dataset of a recently finished WF  
        url = urlWMstats + 'byoutputdataset?include_docs=true&reduce=false&key="%s"' % datasetName
        rows = geturl(urlCMSWeb, url)['rows']
        isOutputOfRecentWF = False
        outputWFs = []
        for row in rows:
            outputWFs.append("%s %s %s" % (row['id'],row['doc']['RequestTransition'][-1]['Status'], time.strftime('%Y-%m-%d', time.gmtime(row['doc']['RequestTransition'][-1]['UpdateTime']))))
            if int(row['doc']['RequestTransition'][-1]['UpdateTime']) > datelimit:
                isOutputOfRecentWF = True
                break
        if isOutputOfRecentWF:
            if debugMode: print >> sys.stderr, 'skipping: recently produced'
            continue
        
        totalSizeAtSite += datasetSizeAtSite
        totalSize += datasetSize
        print 'dataset:',datasetName,'sizeAtSite:',to_GB(datasetSizeAtSite),'total_size:',to_GB(datasetSize)
        print '\tWFs(inputdataset):'
        for wf in inputWFs:
            print '\t\t'+wf
        print '\tWFs(outputdataset):'
        for wf in outputWFs:
            print '\t\t'+wf
        print
    except Exception as e:
        if debugMode: print >> sys.stderr, 'skipping: unexpected error (please also check whether you have a valid proxy) - %s' % e
        continue

print 'total_size_at_site:', to_TB(totalSizeAtSite),'total_size:', to_TB(totalSize)
