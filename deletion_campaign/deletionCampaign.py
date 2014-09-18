#!/usr/bin/env python

import sys,os,getopt,urllib,httplib,time
try:
    import json
except ImportError:
    import simplejson as json
#DBS-3 imports
from dbs.apis.dbsClient import *

from sso_auth import Login

OUTPUT='/afs/cern.ch/user/m/mtaze/TransferTeam/deletion_campaign/out/'
# arguments
datasetRegexList=None

try:
    opts, args = getopt.getopt(sys.argv[1:], "", ["dataset="])
except getopt.GetoptError:
    print  >> sys.stderr, 'Failed to parse options!'
    sys.exit(2)

# check command line parameter
for opt, arg in opts :
    if opt == "--dataset":
        datasetRegexList = arg
        
if datasetRegexList == None:
    print  >> sys.stderr, 'Please specify dataset(regex) with --dataset option'
    sys.exit(2)
    
def to_GB(amount):
    return  "%.3f" % (amount / float(1000 ** 3))

url='https://cmsweb.cern.ch/dbs/prod/global/DBSReader'
dbs3api = DbsApi(url=url)
ssoLogin = Login()

try:
    # split comma separated dataset
    for datasetRegex in datasetRegexList.split(','):
        datasetList = dbs3api.listDatasets(dataset_access_type='VALID',detail=1,dataset=datasetRegex)
        for dataset in datasetList:
            if dataset['data_tier_name'].upper() == "RAW":
                continue
            dsName = dataset['dataset']
            dsCreationDate = time.strftime('%Y%m%d', time.gmtime(dataset['creation_date']))
            dsProcessedName = dataset['processed_ds_name']
            dsPopularity = []
            dsSize = dbs3api.listBlockSummaries(dataset=dsName)[0]['file_size']

            # remove version number
            if dsProcessedName[-3:-1] == '-v':
                dsProcessedName = dsProcessedName[:-3]
            dsProcessedName += ".txt"

            # if there is no popularity info for the dataset, it doesn't return a json object
            url = 'https://cms-popularity.cern.ch/popdb/popularity/getSingleDSstat?orderby=naccess&aggr=year&name=%s' % dsName
            try:
                result = json.loads(ssoLogin.getUrl(url))
                for popularity in result['data'][0]['data']:
                    dsPopularity.append('%s:%s' % (time.strftime('%Y', time.gmtime(popularity[0]/1000.0)), popularity[1]))
            except Exception as e:
                dsPopularity.append('NoRecord')

            with open(OUTPUT + dsProcessedName, 'a') as file:
                file.write("dataset: %s size(GB): %s creation_date: %s popularity: %s\n" % (dsName, to_GB(dsSize), dsCreationDate, ','.join(dsPopularity)))

            print "dataset: %s size(GB): %s creation_date: %s popularity: %s" % (dsName, to_GB(dsSize), dsCreationDate, ','.join(dsPopularity))

except Exception as e:
    print >> sys.stderr, 'error:',e
