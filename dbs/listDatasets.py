#!/usr/bin/env python
import sys,getopt
#DBS-3 imports
from dbs.apis.dbsClient import *

try:
    opts, args = getopt.getopt(sys.argv[1:], "", ["status="])
except getopt.GetoptError:
    sys.exit(2)

url="https://cmsweb.cern.ch/dbs/prod/global/DBSReader"
dbs3api = DbsApi(url=url)
status='*'

for opt, arg in opts :
    if opt == "--status" :
        status = arg

try:
    if status == None:
        dsInfos = dbs3api.listDatasets()
        for ds in dsInfos:
            print ds['dataset']
    else:
        dsInfos = dbs3api.listDatasets(dataset_access_type=status, detail='1')
        for ds in dsInfos:
            print ds['dataset'], ds['dataset_access_type']
except:
    print >> sys.stderr, 'error'

