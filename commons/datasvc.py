#!/usr/bin/env python
import sys,getopt,urllib

try:
    import json
except ImportError:
    import simplejson as json

def help():
    print "instance (optional): PhEDEx instance prod/debug/dev (default prod)"
    print "service            : datasvc name (blockreplica, filereplica, etc.)"
    print "options (optional) : & seprated options (node=T2_CH_CERN&create_since=0)"
    print "path               : hierarchical path to attributes"
    print "Example usage:"
    print "datasvc.py --service filereplicas --options 'dataset=/TT_FullLept_noCorr_mass169_5_8TeV-mcatnlo/Summer12-START53_V7C-v1/GEN-SIM' --path /phedex/block:name/file:name,checksum,bytes"
    print "\tThis will return BlockName FileName FileCksum FileBytes one line each"


def parseResult(out, path, result, firstEntry=False):
    if path:
        first, rest = getKey(path[0]), path[1:]
        item, attr = first[0], first[1]

        subResults = result[item]
            
        if not isinstance(subResults, (list, set)):
            subResults = [subResults]

        for subResult in subResults:
            if attr:
                newOut = list(out);
                for key in attr.split(','):
                    newOut.append(str(subResult[key]).replace('\n',''))
                parseResult(newOut,rest,subResult)
            else:
                parseResult(out, rest, subResult) 
    else:
        print " ".join(out)

def getKey(key):
    if ':' in key:
        res = key.split(':')
    else:
        res = [key, None]
    return res

try:
    opts, args = getopt.getopt(sys.argv[1:], "", ["instance=","service=","options=","path=","help"])
except getopt.GetoptError:
    print  >> sys.stderr, 'Please specify data service with --service and path with --path'
    sys.exit(2)

service=None
options=None
path=None
instance="prod"
# check command line parameter
for opt, arg in opts :
    if opt == "--instance":
        instance = arg
    elif opt == "--service" :
        service = arg
    elif opt == "--options" :
        options = arg
    elif opt == "--path" :
        path = filter(None, arg.split('/'))
    elif opt == "--help":
        help()
        sys.exit(0)

if service == None or path == None:
    print  >> sys.stderr, 'Please specify data service with --service and path with --path'
    sys.exit(2)


result=None
output=[]
url='https://cmsweb.cern.ch/phedex/datasvc/json/' + instance + '/' + service
if options != None:
    url += '?' + options.replace('#','%23')

result = json.load(urllib.urlopen(url))
try:
    parseResult(output,path,result)
except:
    print >> sys.stderr, 'error'
