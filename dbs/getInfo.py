#!/usr/bin/env python
import sys,getopt, time
#DBS-3 imports
from dbs.apis.dbsClient import *

# usage: python ~/TransferTeam/dbs/getInfo.py --method files --return block_name,logical_file_name,check_sum,adler32,file_size --option logical_file_name:xxxx.root

try:
    opts, args = getopt.getopt(sys.argv[1:], "", ["method=","option=","return="])
except getopt.GetoptError:
    sys.exit(2)

method = None
option = None
attrs = None

# check command line parameter
for opt, arg in opts :
    if opt == "--method":
        method = arg.lower()
    elif opt == "--option":
        option = arg
    elif opt == "--return":
        attrs = arg

if method == None or attrs == None:
    print 'Please specify method with --method and attributes returned with --return'
    sys.exit(2)

UNIT = 1000 ** 4 #TB
def to_TB(amount):
    return "%.3f" % (amount / float(UNIT),)

url="https://cmsweb.cern.ch/dbs/prod/global/DBSReader"
dbs3api = DbsApi(url=url)

try:
    params = {}
    for op in option.split(','):
        key,val = option.split(':')
        params[key] = val

    params['detail']='1'

    if method == "files":
        infos = dbs3api.listFiles(**params)
    if method == "datasets":
        if "dataset_access_type" not in params:
            params['dataset_access_type=']="*"
        infos = dbs3api.listDatasets(**params)

    for info in infos:
        for attr in attrs.split(','):
            if "date" in attr:
                print time.strftime('%Y%m%d', time.gmtime(info[attr])),
            else:
                print info[attr],
        print
except Exception as e:
    print >> sys.stderr, e

