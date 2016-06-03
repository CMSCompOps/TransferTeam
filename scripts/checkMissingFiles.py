#!/usr/bin/env python

import json
from os import system
from sys import argv,exit
from re import sub

verbose=True

lfn = argv[1]

class TMDBFile():
  def __init__(self,n):
    self.name = n
    self.missing = []
    self.subscribed = []

if verbose: print 'investigating',lfn

try:
  site = argv[2]
  cmd = 'wget --no-check-certificate -O /tmp/snarayan/missingfiles.json "https://cmsweb.cern.ch/phedex/datasvc/json/prod/missingfiles?block='+lfn+'%23*&node='+site+'" > /dev/null 2>/dev/null'
except IndexError:
  cmd = 'wget --no-check-certificate -O /tmp/snarayan/missingfiles.json "https://cmsweb.cern.ch/phedex/datasvc/json/prod/missingfiles?block='+lfn+'%23*" > /dev/null 2>/dev/null'
system(cmd)

with open('/tmp/snarayan/missingfiles.json') as jsonFile:
  missingBlocks = json.load(jsonFile)['phedex']['block']

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
