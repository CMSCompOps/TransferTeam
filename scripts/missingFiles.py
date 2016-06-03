#!/usr/bin/env python

import os, sys, re, urllib, json, time
from optparse import OptionParser

def getDatasetsList():
        f = open('./StuckDatasets.txt')
        nl = sum(1 for _ in f)
        f = open('./StuckDatasets.txt')

        while nl > 0:
                nl = nl - 1
                d = f.readline()
                if 'AnalysisOps' in d:
                        for i in range(5):d=f.readline()
                        while '/' in d:
                                d2 = '/' + d.strip().split(' /')[1]
                                datasetsList.append(d2)
                                d = f.readline()
        return datasetsList

def missingfiles(dataset_list, debug,sitename):
        for i in range(len(dataset_list)):
              if dataset_list[i].find('ST')>=0:
                continue
              print 'investigating',dataset_list[i]
              url="https://cmsweb.cern.ch/phedex/datasvc/json/"+ instance.lower() +"/missingfiles?node="+sitename+"&block="+str(dataset_list[i])+"%23*"
              if debug == True : print url
              print url
              result = json.load(urllib.urlopen(url))

              for block in  result ['phedex']['block']:
                        for missing_files in block['file']:
                                if float(missing_files['time_create']) < (time.time() - 2592000/2.):
                                        lfnList.append(missing_files['name'].encode("utf-8"))
	print '--Missing files list:'
        print lfnList
        return lfnList

def replica(missing_files, debug):
        for i in range(len(missing_files)):
              print 'investigating',missing_files[i]
              url="https://cmsweb.cern.ch/phedex/datasvc/json/"+ instance.lower() + "/filereplicas?lfn="+str(missing_files[i])
              if debug == True : print url

              result = json.load(urllib.urlopen(url))
              lfn = result ['phedex']['block'][0]['file'][0]['replica']
              if not lfn:
                        files_no_replica.append(result['phedex']['block'][0]['file'][0]['name'].encode("utf-8"))

	print '----------------------------\n--Missing files without a replica:'
        for f in files_no_replica:
          print f
        return files_no_replica

def callFileInvalidationShellCommand(mfl, df): #mfl = missing files list without replica, df = if equals to 0 exe global inv. command
	phdx_dir = '~/phedex/PHEDEX/'
	dbparam = '' # tester's dbparam
	env = 'etc/profile.d/env.sh'
	utilities_script = 'Utilities/FileDeleteTMDB -db ~/phedex/info/DBParam:'
	user_id = '' # tester's user_id
	cms_ver = 'CMSSW_7_1_4'
	cms_dir = '/afs/cern.ch/user/j/' + user_id + '/home/cmssw/' + cms_ver + '/src'
	invalidation_cmd = './DBS3SetFileStatus.py --url=https://cmsweb.cern.ch/dbs/'+ instance.lower() +'/global/DBSWriter --status=invalid --recursive=False'

	if df != 0:
		system('source ' + phdx_dir + env)
		for i in range (len(mfl)):
			# phedex global invalidation
			cmd = phdx_dir + utilities_script + instance.lower().title() + '/' + dbparam +' -list lfn:'+ mfl[i] + ' -invalidate'
			system(cmd)
	
			# db3 sl6 global invalidation		
			cmd = 'cd ' + cms_dir
			system(cmd)
			system('cmsenv')
			cmd = 'voms-proxy-init -voms cms -cert usercert.pem -key userkey.pem'
			system(cmd)
			system(invalidation_cmd + ' --files=' + mfl[i])

usage  = "Usage: %prog dataset"
parser = OptionParser(usage=usage)
parser.add_option("-v", "--verbose", action="store_true", default=False, dest="verbose", help="verbose output")
parser.add_option("-d", "--dataset", action="store", type="string", default="None", dest="dataset", help="Dataset Name")
parser.add_option("-s", "--site", action="store", type="string", dest="site", help="Site Name")
(opts, args) = parser.parse_args()

#if (opts.dataset == None ):
#    parser.error("Define dataset"
if (opts.site == None):
  parser.error("Define site")



dataset = opts.dataset
debug = opts.verbose
datasetsList = []
lfnList = []
files_no_replica = []
instance='prod'
dataset_list = getDatasetsList()
missing_files = missingfiles(dataset_list,debug,opts.site)
replica = replica(missing_files,debug)
