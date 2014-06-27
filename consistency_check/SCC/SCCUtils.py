#!/usr/bin/env python
import sys,getopt,urllib,os
try:
    import json
except ImportError:
    import simplejson as json

from dbs.apis.dbsClient import *

try:
    opts, args = getopt.getopt(sys.argv[1:], "", ["node=","list=","output="])
except getopt.GetoptError:
    sys.exit(2)

def logger(msg, isError=False):
    if isError:
        print>> outfile, "Node: %s file: %s dataset: None err: %s" % (node, lfn, msg.replace(' ', '_'))
    else:
        if dataset:
            print>> outfile, "Node: %s file: %s dataset: %s msg: %s" % (node, lfn, dataset[0]['dataset'], msg)
        else:
            print>> outfile, "Node: %s file: %s dataset: None msg: %s" % (node, lfn, msg)


node = None
list = None
output = None
flushCount=0

# check command line parameter
for opt, arg in opts :
    if opt == "--list":
        list = arg
    if opt == "--node":
        node = arg
    if opt == "--output":
        output = arg

# check required parameter
if node == None and list == None:
    print >> sys.stderr, 'Please specify either node name with --node or lfn list with --list'
    sys.exit(2)

# return se name from node name
if list == None:
    url='https://cmsweb.cern.ch/phedex/datasvc/json/prod/nodes?node=' + node
    result = json.load(urllib.urlopen(url))
    try:
        res = result['phedex']['node'][0]
        print str(res['se'])
    except Exception, e:
        print >> sys.stderr, "Failed to find SE name for the node: ", node
        
else:
    outfile = open(output, 'w')
    with open(list) as infile:
        for line in infile:
            flushCount+=1
            if flushCount % 100 == 0:
                os.fsync(outfile)

            lfn = line.strip()
            try:
                url="https://cmsweb.cern.ch/dbs/prod/global/DBSReader"
                dbs3api = DbsApi(url=url)

                dataset = dbs3api.listDatasets(logical_file_name=lfn, detail=1, dataset_access_type='*')
                if not dataset:
                    logger('file_not_in_dbs')
                else:
                    status = dataset[0]['dataset_access_type'].upper()
                    if status == "PRODUCTION":
                        logger('dataset_production')
                    else:
                        lfnInfo = dbs3api.listFiles(logical_file_name=lfn, detail='1')
                        if not lfnInfo:
                            logger('file_not_have_info')
                        else:
                            dataset_status='dataset_'+status.lower()
                            if lfnInfo[0]['is_file_valid'] == 0:
                                logger(dataset_status + '_file_invalid')
                            else:
                                logger(dataset_status + '_file_valid')

            except Exception, e:
                logger(str(e), True)
                print >> sys.stderr, str(e)
    outfile.close()
