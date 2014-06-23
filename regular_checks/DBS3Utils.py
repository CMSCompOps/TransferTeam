#!/usr/bin/env python
import sys,getopt,time
#DBS-3 imports
from dbs.apis.dbsClient import *

try:
    opts, args = getopt.getopt(sys.argv[1:], "", ["datasetValid","datasetProduction","datasetGEN","maxcdate="])
except getopt.GetoptError:
    print >> sys.stderr, 'getopt error'
    sys.exit(2)

type=-1
creation_date=int(time.time())

# check command line parameter
for opt, arg in opts :
    if opt == "--datasetValid":
        type = 1
    elif opt == "--datasetProduction":
        type = 2
    elif opt == "--datasetGEN":
        type = 3
    elif opt == "--maxcdate":
        creation_date = int(time.mktime(time.strptime(arg, "%Y%m%d")))


url='https://cmsweb.cern.ch/dbs/prod/global/DBSReader'
dbs3api = DbsApi(url=url)

try:
    if type == 1:
        datasets = dbs3api.listDatasets(dataset_access_type='VALID')
    elif type == 2:
        datasets = dbs3api.listDatasets(dataset_access_type='PRODUCTION', max_cdate=creation_date)
    elif type == 3:
        datasets = dbs3api.listDatasets(dataset_access_type='VALID', dataset='/*/*/GEN', max_cdate=creation_date)
    else:
        print >> sys.stderr, 'wrong parameter'

    for ds in datasets:
        print ds['dataset']
except Exception,e:
    print >> sys.stderr, 'error: ', e

