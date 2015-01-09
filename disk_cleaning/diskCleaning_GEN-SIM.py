#!/usr/bin/env python

import sys,os,getopt,urllib,httplib,time

try:
    import json
except ImportError:
    import simplejson as json

pileup = ["/MinBias_TuneZ2_7TeV-pythia6/Summer11Leg-START53_LV4-v1/GEN-SIM","/MinBias_TuneZ2_7TeV-pythia6/Summer11-START311_V2-v2/GEN-SIM","/MinBias_TuneZ2star_8TeV-pythia6/Summer12-START50_V13-v3/GEN-SIM","/MinBias_Tune4C_7TeV_pythia8/Summer12-LowPU2010-START42_V17B-v1/GEN-SIM","/MinBias_TuneA2MB_13TeV-pythia8/Fall13-POSTLS162_V1-v1/GEN-SIM","/MinBias_TuneZ2star_14TeV-pythia6/GEM2019Upg14-DES19_62_V8-v1/GEN-SIM","/MinBias_TuneZ2star_14TeV-pythia6/TTI2023Upg14-DES23_62_V1-v1/GEN-SIM","/MinBias_TuneZ2star_14TeV-pythia6/Muon2023Upg14-DES23_62_V1-v1/GEN-SIM","/MinBias_TuneA2MB_2p76TeV_pythia8/ppSpring2014-STARTHI53_V28_castor-v2/GEN-SIM","/GJet_Pt-20_doubleEMEnriched_TuneZ2_7TeV-pythia6/Summer11Leg-START53_LV4-v1/GEN-SIM","/QCD_Pt-1800_TuneZ2_7TeV_pythia6/Summer11Leg-START53_LV4-v1/GEN-SIM","/W4Jets_TuneZ2_7TeV-madgraph-tauola/Summer11Leg-START53_LV4-v1/GEN-SIM"]

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
urlWMstats = '/couchdb/wmstats/_design/WMStats/_view/'

statusOngoingWF = ["assigned","acquired","running","running-open","running-closed","assignment-approved"]
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
        if datasetName in pileup:
            if debugMode: print >> sys.stderr, 'skipping: it is set as pileup dataset in the script'
            continue

        # check if custodial replica exists
        url = urlPhedex + 'blockreplicas?create_since=0&dataset=' + datasetName
        subResult = json.load(urllib.urlopen(url))
        custReplicaExist = False
        datasetSizeAtSite = 0
        datasetSize = 0
        for block in subResult['phedex']['block']:
            datasetSize += long(block['bytes'])
            for replica in block['replica']:
                if replica['node'] == node:
                    datasetSizeAtSite += long(replica['bytes'])
                if replica['custodial'] == "y":
                    custReplicaExist = True

        if not custReplicaExist:
            if debugMode: print >> sys.stderr, 'skipping: no custodial replica exists'
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
            if debugMode: print >> sys.stderr, 'skipping: used by an ongoing WF'
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
