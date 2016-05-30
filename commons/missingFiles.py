#!/usr/bin/env python

import os
import sys
import re
import urllib
import json
import time
from optparse import OptionParser


def init():
    usage = '%prog <options>'
    parser = OptionParser(usage=usage)

    parser.add_option(
        '-d', '--datatier', action='store', type='string', dest='datatier', help='Data Tier Name')

    parser.add_option(
        '-s', '--site', action='store', type='string', dest='site', help='Site Name')

    (opts, args) = parser.parse_args()

    if (opts.site == None):
        parser.error('Define site')

    data_tier = opts.datatier

    print 'site:' + opts.site
    if data_tier:
        print  'datatier:' + data_tier

    if data_tier == None:
        print '------------ DATA TIER: all_datasets'
        dataset_list = getDatasetsList('all_datasets')
    else:
        print '------------ DATA TIER:' + data_tier
        dataset_list = getDatasetsList('/'+ data_tier)

    missing_files = getMissingFiles(dataset_list, opts.site)
    getMissingFilesWithoutReplica(missing_files)


def getDatasetsList(data_tier):
    f = open('./StuckDatasets.txt')
    nl = sum(1 for _ in f)
    f = open('./StuckDatasets.txt')

    while nl > 0:
        nl = nl - 1
        d = f.readline()
        if 'AnalysisOps' in d:
            for i in range(5):
                d = f.readline()
            while '/' in d:
                if data_tier == 'all_datasets':
                    d2 = '/' + d.strip().split(' /')[1]
                    datasetsList.append(d2)
                else:
                    if data_tier in d[d.rindex('/'):]:
                        d2 = '/' + d.strip().split(' /')[1]
                        print 'dataset in []:' + d2
                        datasetsList.append(d2)
                d = f.readline()
    print 'datasets: ' + str(len(datasetsList))
    return datasetsList


def getMissingFiles(dataset_list, sitename):
    for i in range(len(dataset_list)):
        print 'investigating', dataset_list[i]
        url = 'https://cmsweb.cern.ch/phedex/datasvc/json/' + \
            instance.lower() + '/missingfiles?node=' + sitename + \
            '&block=' + str(dataset_list[i]) + '%23*'

        print url

        result = json.load(urllib.urlopen(url))

        for block in result['phedex']['block']:
            for missing_files in block['file']:
                if float(missing_files['time_create']) < (time.time() - 2592000):
                    lfnList.append(missing_files['name'].encode('utf-8'))
    return lfnList


def getMissingFilesWithoutReplica(missing_files):
    for i in range(len(missing_files)):
        print 'investigating', missing_files[i]
        url = 'https://cmsweb.cern.ch/phedex/datasvc/json/' + \
            instance.lower() + '/filereplicas?lfn='+str(missing_files[i])

        result = json.load(urllib.urlopen(url))
        lfn = result['phedex']['block'][0]['file'][0]['replica']
        if not lfn:
            files_wo_replica.append(
                result['phedex']['block'][0]['file'][0]['name'].encode('utf-8'))

    print '----------------------------\n--Missing files without a replica:'
    for f in files_wo_replica:
        print f
    return files_wo_replica

# mfl = missing files lis if t without replica, df = if equals to 0 exe global
# inv. command
def callFileInvalidationShellCommand(mfl, df):
    instance = 'dev'
    phdx_dir = '~/phedex/PHEDEX/'
    dbparam = ''  # tester's dbparam
    env = 'etc/profile.d/env.sh'
    utilities_script = 'Utilities/FileDeleteTMDB -db ~/phedex/info/DBParam:'
    user_id = ''  # tester's user_id
    cms_ver = 'CMSSW_7_1_4'
    cms_dir = '/afs/cern.ch/user/j/' + user_id + \
        '/home/cmssw/' + cms_ver + '/src'
    invalidation_cmd = './DBS3SetFileStatus.py --url=https://cmsweb.cern.ch/dbs/' + \
        instance.lower() + \
        '/global/DBSWriter --status=invalid --recursive=False'

    if df != 0:
        system('source ' + phdx_dir + env)
        for i in range(len(mfl)):
            # phedex global invalidation
            cmd = phdx_dir + utilities_script + \
                instance.lower().title() + '/' + dbparam + \
                ' -list lfn:' + mfl[i] + ' -invalidate'
            system(cmd)

            # db3 sl6 global invalidation
            cmd = 'cd ' + cms_dir
            system(cmd)
            system('cmsenv')
            cmd = 'voms-proxy-init -voms cms -cert usercert.pem -key userkey.pem'
            system(cmd)
            system(invalidation_cmd + ' --files=' + mfl[i])

datasetsList = []
lfnList = []
files_wo_replica = []
instance = 'prod'
init()