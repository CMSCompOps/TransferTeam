#!/usr/bin/env python
import sys,getopt
import traceback
#DBS-3 imports
from dbs.apis.dbsClient import *

try:
    opts, args = getopt.getopt(sys.argv[1:], "", ["input=","lfn","dataset"])
except getopt.GetoptError:
    sys.exit(2)

inputFile = None
lfn = False
dataset = False
# check command line parameter
for opt, arg in opts :
    if opt == "--input" :
        inputFile = arg
    if opt == "--lfn":
        lfn = True
    if opt == "--dataset":
        dataset = True

if inputFile == None:
    print 'Please specify input file with --input'
    sys.exit(2)


def prnt(dataset, dsStatus, file, fileStatus):
    print dataset,dsStatus,file,fileStatus


url="https://cmsweb.cern.ch/dbs/prod/global/DBSReader"
dbs3api = DbsApi(url=url)

with open(inputFile) as file:
    for line in file:
        line = line.rstrip()
        try:
            if lfn:
                dsInfos = dbs3api.listDatasets(dataset_access_type='*', logical_file_name=line, detail='1')
                if not dsInfos:
                    prnt('NONE', 'NONE', line, 'NONE')
                else:
                    lfnInfos = dbs3api.listFiles(logical_file_name=line, detail='1')
                    if not lfnInfos:
                        prnt(dsInfos[0]['dataset'], dsInfos[0]['dataset_access_type'], line, 'NONE')
                    else:
                        prnt(dsInfos[0]['dataset'], dsInfos[0]['dataset_access_type'], line, lfnInfos[0]['is_file_valid'])
            else:
                dsInfos = dbs3api.listDatasets(dataset_access_type='*', dataset=line, detail='1')
                for ds in dsInfos:
                    print ds['dataset'], ds['dataset_access_type']

        except Exception, e:
            print >> sys.stderr, e
            if lfn:
                prnt('NONE', 'NONE', line, 'ERROR') 
            else:
                print line, 'ERROR'

