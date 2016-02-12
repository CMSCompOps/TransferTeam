#!/usr/bin/env python

import json
from os import system
from sys import argv,exit

lfn = argv[1]

cmd = 'wget --no-check-certificate -O /tmp/snarayan/missingfiles.json https://cmsweb.cern.ch/phedex/datasvc/json/prod/missingfiles?block='+lfn+'%23* > /dev/null 2>/dev/null'
system(cmd)

with open('/tmp/snarayan/missingfiles.json') as jsonFile:
  missingBlocks = json.load(jsonFile)['phedex']['block']

bad = []
for block in missingBlocks:
  for missingFile in block['file']:
    nSites = len(missingFile['missing'])
    name = missingFile['name']
    bad.append((nSites,name))

if len(bad)==1:
  print lfn
  for b in bad:
    print '%2i  :  %s'%(b[0],b[1])
