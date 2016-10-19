#!/usr/bin/env python

import os,sys, re
import datetime
from dateutil.relativedelta import relativedelta
from optparse import OptionParser
import urllib,json
import datetime


import urllib2, httplib
class HTTPSClientAuthHandler(urllib2.HTTPSHandler):
        def __init__(self, key, cert):
                urllib2.HTTPSHandler.__init__(self)
                self.key = key
                self.cert = cert
        def https_open(self, req):
#Rather than pass in a reference to a connection class, we pass in
# a reference to a function which, for all intents and purposes,
# will behave as a constructor
                return self.do_open(self.getConnection, req)
        def getConnection(self, host, timeout=300):
                return httplib.HTTPSConnection(host, key_file=self.key, cert_file=self.cert)

def DBS3DatasetFiles(dataset, debug, summary):
        url="https://cmsweb.cern.ch/dbs/prod/global/DBSWriter/files?dataset="+str(dataset)
        if debug == True : print url
        opener = urllib2.build_opener(HTTPSClientAuthHandler('/tmp/x509up_u71360', '/tmp/x509up_u71360') )
        result = opener.open(url)
        result2 = result.read()
        result3 = json.loads(result2)

        dataset_summary = {}
        total_files = 0
	for file_name in result3:
		total_files = total_files + 1
        	lfn = file_name['logical_file_name']
        	if summary == False: print lfn
                file_type=lfn.split('/',3)[2]
                if file_type in dataset_summary.keys():
                        dataset_summary[file_type] = dataset_summary[file_type] + 1
                else:
                        dataset_summary[file_type] = 1  
	
	if summary == True:
		print 'dataset:',dataset
		for directory in dataset_summary:
		        print directory,':',dataset_summary[directory],':', dataset_summary[directory] * 100 / total_files,'%'
		print 'Total files in the dataset: ', total_files 	 

usage  = "Usage: %prog dataset"
parser = OptionParser(usage=usage)
parser.add_option("-v", "--verbose", action="store_true", default=False, dest="verbose", help="verbose output")
parser.add_option("-d", "--dataset", action="store", type="string", default="None", dest="dataset", help="Dataset name")
parser.add_option("-s", "--summary", action="store_true", default=False, dest="summary", help="Summary of total files of the dataset")
(opts, args) = parser.parse_args()

if (opts.dataset == None ):
    parser.error("Define dataset")

dataset = opts.dataset
debug = opts.verbose
summary = opts.summary

result = DBS3DatasetFiles(dataset,debug,summary)
