#!/usr/bin/env python

import sys,os,getopt,urllib,httplib,time

try:
    import json
except ImportError:
    import simplejson as json

def to_TB(val):
    return "%.3f TB" % (val / float(1000 ** 4))

node = None
datasetRegex='/*/*/*'

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
        datasetRegex = arg

if node == None:
    print  >> sys.stderr, 'Please specify a node name with --node'
    sys.exit(2)
    
# Constant variables
urlPhedex = 'https://cmsweb.cern.ch/phedex/datasvc/json/prod/'

samples={}
 
#try:
url = urlPhedex + 'blockreplicas?create_since=0&show_dataset=y&dataset=%s&node=%s' % (datasetRegex,node)
result = json.load(urllib.urlopen(url))
totalSize = 0
for dataset in result['phedex']['dataset']:
    datasetName = str(dataset['name'])
    dataTier = datasetName.split('/')[3]

    datasetSize = 0
    for block in dataset['block']:
        datasetSize += int(block['bytes'])

    if dataTier in samples:
        samples[dataTier]['datasetlist'].append({'name':datasetName,'size':datasetSize})
        samples[dataTier]['size'] += datasetSize
    else:
        samples[dataTier] = {'datasetlist':[{'name':datasetName, 'size':int(datasetSize)}],'size':int(datasetSize)}

    totalSize += datasetSize

for key in samples:
    print key, to_TB(samples[key]['size'])
    for dataset in samples[key]['datasetlist']:
        print dataset['name'],to_TB(dataset['size'])
    print "############################################"

print 'totalsize:', to_TB(totalSize)

#except Exception as e:
#    print >> sys.stderr, 'error:',e
