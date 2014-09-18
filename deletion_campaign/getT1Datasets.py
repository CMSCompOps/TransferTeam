#!/usr/bin/env python

import sys,os,getopt,urllib,httplib,time
try:
    import json
except ImportError:
    import simplejson as json

# arguments
node = None
datasetRegexList=None

try:
    opts, args = getopt.getopt(sys.argv[1:], "", ["node=","dataset="])
except getopt.GetoptError:
    print  >> sys.stderr, 'Failed to parse options!'
    sys.exit(2)

# check command line parameter
for opt, arg in opts :
    if opt == "--node":
        node = arg
    elif opt == "--dataset":
        datasetRegexList = arg
        
if datasetRegexList == None:
    print  >> sys.stderr, 'Please specify dataset(regex) with --dataset option'
    sys.exit(2)
    
def to_GB(amount):
    return  "%.3f" % (amount / float(1000 ** 3))

try:
    # split comma separated dataset list into datasvc format
    datasetOption = ''
    for datasetRegex in datasetRegexList.split(','):
        datasetOption += '&dataset=%s' % datasetRegex

    if node == None:
        node = 'T1_*_Buffer&node=T1_*_MSS'

    # get all dataset at the specified node
    url = 'https://cmsweb.cern.ch/phedex/datasvc/json/prod/blockreplicas?create_since=0&show_dataset=y&node=%s%s' % (node,datasetOption)
    result = json.load(urllib.urlopen(url))
    totalSize = 0
    totalDataset=0
    for dataset in result['phedex']['dataset']:
        datasetName = str(dataset['name'])

        if datasetName.split('/')[2] == 'RAW':
            continue

        datasetSize = 0
        if 'bytes' in dataset:
            datasetSize = long(dataset['bytes'])
        else:
            for block in dataset['block']:
                datasetSize += block['bytes']
        
        print 'dataset: %s size(GB): %s' % (datasetName, to_GB(datasetSize))
        totalDataset += 1
        totalSize += datasetSize

    print 'total_dataset:',totalDataset,'total_size(GB): %s' % to_GB(totalSize)
except Exception as e:
    print >> sys.stderr, 'error:',e
