#!/usr/bin/env python

import sys,getopt,urllib

try:
    import json
except ImportError:
    import simplejson as json

def help():
    print "instance (optional)    : PhEDEx instance prod/debug/dev (default prod)"
    print "option   (optional)    : return results with given option (e.g. 'subscribed:n' or 'custodial:y'"
    print "dataset, block, or lfn : name"
    print "checkReplica.py --option custodial:y --lfn /store/data/Run2011A/Photon/AOD/16Jan2012-v1/0001/42474CCE-A843-E111-82EE-002590200B68.root"
    print "\tThis will return only custodial locations of the given lfn"


dataset = None
block = None
lfn = None
option=None
sites=[]
instance='prod'
try:
    opts, args = getopt.getopt(sys.argv[1:], "", ["lfn=","dataset=", "block=", "instance=","option=","help"])
except getopt.GetoptError:
    print  >> sys.stderr, 'Failed to parse options'
    sys.exit(2)

# check command line parameter
for opt, arg in opts :
    if opt == "--dataset" :
        dataset = arg
    elif opt == "--block" :
        block = arg
    elif opt == "--lfn" :
        lfn = arg
    elif opt == "--option" :
        option = arg
    elif opt == "--instance" :
        instance = arg
    elif opt == "--help":
        help()
        sys.exit(0)
        
if dataset == None and block == None and lfn == None:
    print  >> sys.stderr, 'Please specify dataset with --dataset or block with --block or lfn with --lfn'
    sys.exit(2)

def checkOption(replica):
    try:
        if option:
            keyval = option.split(':')
            if replica[keyval[0]] != keyval[1]:
                return False
        return True
    except:
        print >> sys.stderr, 'check your option parameter: ', option

def addToResult(replica):
    if not checkOption(replica):
        return
    site = str(replica['node'])
    if site not in sites:
        sites.append(site)

try:
    if dataset:
        url='https://cmsweb.cern.ch/phedex/datasvc/json/' + instance + '/blockreplicas?dataset=' + dataset 
    elif block:
        url='https://cmsweb.cern.ch/phedex/datasvc/json/' + instance + '/blockreplicas?block=' + block.replace('#','%23',1)
    else:
        url='https://cmsweb.cern.ch/phedex/datasvc/json/' + instance + '/filereplicas?lfn=' + lfn

    result = json.load(urllib.urlopen(url))

    for b in result['phedex']['block']:
        if lfn == None:
            name = b['name']
            for replica in b['replica']:
                addToResult(replica)
        else:
            for file in b['file']:
                name = file['name']
                for replica in file['replica']:
                    addToResult(replica)

    if lfn:
        print 'lfn:', lfn, 'sites:', ','.join(sites)
    elif block:
        print 'block:', block, 'sites:', ','.join(sites)
    else:
        print 'dataset:', dataset, 'sites:', ','.join(sites)

except:
    print >> sys.stderr, 'Failed to get info for:',dataset,block,lfn
        

