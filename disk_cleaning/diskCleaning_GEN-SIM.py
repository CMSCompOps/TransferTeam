#!/usr/bin/env python

import sys,os,getopt,urllib,httplib,time

try:
    import json
except ImportError:
    import simplejson as json


# get method to parse given url which requires certificate
def geturl(url, request, retries=2):
    conn  =  httplib.HTTPSConnection(url, cert_file = os.getenv('X509_USER_PROXY'),
                                            key_file = os.getenv('X509_USER_PROXY'))
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
try:
    opts, args = getopt.getopt(sys.argv[1:], "", ["node=","dataset="])
except getopt.GetoptError:
    print  >> sys.stderr, 'Failed to parse options!'
    sys.exit(2)

# check command line parameter
for opt, arg in opts :
    if opt == "--node":
        node = arg
    elif opt == "--dataset":
        datasetRegex = arg
        
if node == None:
    print  >> sys.stderr, 'Please specify a node name with --node'
    sys.exit(2)
    
# Constant variables
urlPhedex = 'https://cmsweb.cern.ch/phedex/datasvc/json/prod/'
urlCMSWeb = 'cmsweb.cern.ch'
urlWMstats = '/couchdb/wmstats/_design/WMStats/_view/'

statusOngoingWF = ["assigned","acquired","running","running-open","running-closed","assignment-approved"]
OUTPUTDATASET_LIMIT = 6 # in Months
datelimit = int(time.time()) - 6*30*24*60*60
 
try:
    url = urlPhedex + 'blockreplicas?create_since=0&show_dataset=y&dataset=%s&node=%s' % (datasetRegex,node)
    result = json.load(urllib.urlopen(url))
    totalSize = 0
    for dataset in result['phedex']['dataset']:
        datasetName = str(dataset['name'])
    
        # check if custodial replica exists
        url = urlPhedex + 'blockreplicas?create_since=0&custodial=y&dataset=' + datasetName
        subResult = json.load(urllib.urlopen(url))
        custReplicaExist = False
        datasetSize = 0
        for block in subResult['phedex']['block']:
            datasetSize += int(block['bytes'])
            if 'replica' in block:
                custReplicaExist = True
            else:
                custReplicaExist = False
    
        if not custReplicaExist:
            #print >> sys.stderr, 'no custodial location for '+ datasetName
            continue
    
        # check if it's input dataset of an ongoing WF
        url = urlWMstats + 'requestByInputDataset?include_docs=true&reduce=false&key="%s"' % datasetName
        rows = geturl(urlCMSWeb, url)['rows']
        isInputOfOngoingWF = False
        inputWFs = []
        for row in rows:
            inputWFs.append("%s %s %s" % (row['id'],row['doc']['request_status'][-1]['status'], time.strftime('%Y-%m-%d', time.gmtime(row['doc']['request_status'][-1]['update_time']))))
            if row['doc']['request_status'][-1]['status'] in statusOngoingWF:
                isInputOfOngoingWF = True
                break
        if isInputOfOngoingWF:
            continue
    
        
        # check if it's output dataset of a recently finished WF  
        url = urlWMstats + 'requestByOutputDataset?include_docs=true&reduce=false&key="%s"' % datasetName
        rows = geturl(urlCMSWeb, url)['rows']
        isOutputOfRecentWF = False
        outputWFs = []
        for row in rows:
            outputWFs.append("%s %s %s" % (row['id'],row['doc']['request_status'][-1]['status'], time.strftime('%Y-%m-%d', time.gmtime(row['doc']['request_status'][-1]['update_time']))))
            if int(row['doc']['request_status'][-1]['update_time']) > datelimit:
                isOutputOfRecentWF = True
                break
        if isOutputOfRecentWF:
            continue
        
        totalSize += datasetSize
        print 'dataset:',datasetName
        print '\tWFs(inputdataset):'
        for wf in inputWFs:
            print '\t\t'+wf
        print '\tWFs(outputdataset):'
        for wf in outputWFs:
            print '\t\t'+wf
        print
    print 'total_size:', "%.3f TB" % (totalSize / float(1000 ** 4))
except Exception as e:
    print >> sys.stderr, 'error:',e
