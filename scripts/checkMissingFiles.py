#!/usr/bin/env python

import json
from os import system
from sys import argv,exit
from re import sub
from time import time

tmpdir = '/tmp/'

verbose=False
threshold = 86400*7*2

dsList = open(argv[1])
datasets = list(dsList)

for iA in xrange(1,len(argv)):
  if 'verbose' in argv[iA]:
    verbose = ('rue' in argv[iA].split('=')[-1])
  if 'threshold' in argv[iA]: 
    threshold = float(argv[iA].split('=')[-1])*86400

class TMDBFile():
  def __init__(self,n):
    self.name = n
    self.missing = []
    self.basis = []
    self.eta = []
    self.complete = []

for ds in datasets:
  bad = {}
  if verbose: print 'investigating',ds
  cmd = 'wget --no-check-certificate -O '+tmpdir+'missingfiles.json "https://cmsweb.cern.ch/phedex/datasvc/json/prod/missingfiles?block='+ds+'%23*" > /dev/null 2>/dev/null'
  system(cmd)
  with open(tmpdir+'missingfiles.json') as jsonFile:
    missingBlocks = json.load(jsonFile)['phedex']['block']
  for block in missingBlocks:
    for missingFile in block['file']:
      if len(missingFile['missing'])>0:
        try:
          f = bad[missingFile['name']]
        except KeyError:
          f = TMDBFile(missingFile['name'])
          bad[missingFile['name']] = f
        for m in missingFile['missing']:
          f.missing.append(m['node_name'])

  cmd = 'wget --no-check-certificate -O '+tmpdir+'data.json "https://cmsweb.cern.ch/phedex/datasvc/json/prod/data?dataset='+ds+'" > /dev/null 2>/dev/null'
  system(cmd)
  file2block = {}
  with open(tmpdir+'data.json') as jsonFile:
    blocks = json.load(jsonFile)['phedex']['dbs'][0]['dataset'][0]['block']
    for b in blocks:
      for f in b['file']:
        file2block[f['lfn']] = b['name']

  cmd = 'wget --no-check-certificate -O '+tmpdir+'ba.json "https://cmsweb.cern.ch/phedex/datasvc/json/prod/blockarrive?dataset='+ds+'" > /dev/null 2>/dev/null'
  system(cmd)
  blockArrives = {}
  with open(tmpdir+'ba.json') as jsonFile:
    blocks = json.load(jsonFile)['phedex']['block']
    for b in blocks:
      blockArrives[b['name']] = {}
      for d in b['destination']:
        blockArrives[b['name']][d['name']] = {'basis':d['basis'], 'eta':d['time_arrive']}

  for lfn,f in bad.iteritems():
    block = file2block[lfn]
    blockArrive = blockArrives[block]
    



bad = []
for block in missingBlocks:
  for missingFile in block['file']:
    nSites = len(missingFile['missing'])
    name = missingFile['name']
    f = TMDBFile(name)
    for m in missingFile['missing']:
      f.missing.append(m['node_name'])
    bad.append(f)

print 'found %i missing files'%len(bad)

for b in bad:
  cmd = 'wget --no-check-certificate -O /tmp/snarayan/data.json "https://cmsweb.cern.ch/phedex/datasvc/json/prod/data?file='+b.name+'" > /dev/null 2>/dev/null'
  system(cmd)
  with open('/tmp/snarayan/data.json') as jsonFile:
    block = json.load(jsonFile)['phedex']['dbs'][0]['dataset'][0]['block'][0]['name']
  cmd = 'wget --no-check-certificate -O /tmp/snarayan/sub.json "https://cmsweb.cern.ch/phedex/datasvc/json/prod/subscriptions?block='+sub('#','%23',block)+'" > /dev/null 2>/dev/null'
  system(cmd)
  with open('/tmp/snarayan/sub.json') as jsonFile:
    ds = json.load(jsonFile)['phedex']['dataset'][0]
    for s in ds['subscription']:
      b.subscribed.append(s['node'])
    for s in ds['block'][0]['subscription']:
      b.subscribed.append(s['node'])

if verbose:
  for b in bad:
    print b.name
    print '\t',b.missing
    print '\t',b.subscribed

#print lfn
for b in bad:
#  print '%2i  :  %s'%(b[0],b[1])
  found=False
  for s in b.subscribed:
    found = (s not in b.missing)
    if found:
      break
  if not found:
    print b.name
