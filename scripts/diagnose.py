#!/usr/bin/env python

import json
from os import system
from sys import argv,exit
from re import sub
from time import time

tmpdir = '/tmp/'

basis = {
 -6 : 'at least one file has no source replica remaining',
 -5 : 'no path from source to destination',
 -4 : 'automatically suspended by router for too many failures',
 -3 : 'no active download link to the destination',
 -2 : 'manually suspended',
 -1 : 'block is still open',
  0 : 'all files in the block are currently routed',
  1 : 'not yet routed because the destination queue is full',
  2 : 'at least one file is waiting for rerouting',
}

verbose=False
debug=False
threshold = 86400*7*2

dsList = open(argv[1])
datasets = list(dsList)

for iA in xrange(2,len(argv)):
  if 'verbose' in argv[iA]:
    verbose = ('rue' in argv[iA].split('=')[-1])
  if 'debug' in argv[iA]:
    debug = ('rue' in argv[iA].split('=')[-1])
  if 'threshold' in argv[iA]: 
    threshold = float(argv[iA].split('=')[-1])*86400

class Site():
  def __init__(self):
    self.bases = {}
    for iB in xrange(-6,3): 
      self.bases[iB]=0
    self.averageETA = 0
    self.counter = 0

class TMDBDataset():
  def __init__(self,n):
    self.name = n
    self.blocks = {}
  def __str__(self):
    sites = {}
    for block,obj in self.blocks.iteritems():
      sb = obj.getStatus()
      for site in sb:
        if site not in sites:
          sites[site] = Site()
        for iB in xrange(-6,3):
          sites[site].bases[iB] += sb[site].bases[iB]
        sites[site].counter += sb[site].counter
        if sites[site].averageETA!=None and sb[site].averageETA!=None:
          sites[site].averageETA += sb[site].averageETA*sb[site].counter
        else:
          sites[site].averageETA=None
    for site in sites:
      if sites[site].averageETA!=None:
        sites[site].averageETA /= sites[site].counter
    s = self.name + ' is waiting on %i sites\n'%len(sites)
    for sitename,site in sites.iteritems():
      s += '\t' + sitename + ': '
      if site.averageETA!=None:
        s += 'ETA=%.3g days\n'%((site.averageETA-time())/86400.)
      else:
        s += 'ETA=unknown\n'
      for iB in xrange(-6,3):
        if site.bases[iB]>0:
          s += '\t\t%4i stuck in %2i (%s)\n'%(site.bases[iB],iB,basis[iB])
    return s

class TMDBBlock():
  def __init__(self,n):
    self.name = n
    self.files = {}
  def getStatus(self):
    sites = {}
    for lfn,obj in self.files.iteritems():
      for site,info in obj.missing.iteritems():
        if site not in sites:
          sites[site] = Site()
        sites[site].bases[info[0]] += 1
        sites[site].counter += 1
        if sites[site].averageETA!=None and type(info[1])==type(1.):
          sites[site].averageETA += info[1]
        else:
          sites[site].averageETA = None
    for site in sites:
      if sites[site].averageETA!=None:
        sites[site].averageETA /= sites[site].counter
    return sites

class TMDBFile():
  def __init__(self,n):
    self.name = n
    self.missing = {}
    self.complete = []

stuckLFNs = []

for dsRaw in datasets:
  ds = dsRaw.strip()
  dsInstance = TMDBDataset(ds)
  bad = {}
  if debug: print 'investigating',ds
  cmd = 'wget --no-check-certificate -O '+tmpdir+'missingfiles.json "https://cmsweb.cern.ch/phedex/datasvc/json/prod/missingfiles?block='+ds+'%23*" > /dev/null 2>/dev/null'
  if debug: print cmd
  system(cmd)
  with open(tmpdir+'missingfiles.json') as jsonFile:
    missingBlocks = json.load(jsonFile)['phedex']['block']
  for block in missingBlocks:
    for missingFile in block['file']:
      if len(missingFile['missing'])>0:
        stuckLFNs.append(missingFile['name'])
        try:
          f = bad[missingFile['name']]
        except KeyError:
          f = TMDBFile(missingFile['name'])
          bad[missingFile['name']] = f
        for m in missingFile['missing']:
          f.missing[m['node_name']] = None

  cmd = 'wget --no-check-certificate -O '+tmpdir+'data.json "https://cmsweb.cern.ch/phedex/datasvc/json/prod/data?dataset='+ds+'" > /dev/null 2>/dev/null'
  if debug: print cmd
  system(cmd)
  file2block = {}
  with open(tmpdir+'data.json') as jsonFile:
    blocks = json.load(jsonFile)['phedex']['dbs'][0]['dataset'][0]['block']
    for b in blocks:
      block_ = TMDBBlock(b['name'])
      for f in b['file']:
        file2block[f['lfn']] = b['name']

  cmd = 'wget --no-check-certificate -O '+tmpdir+'ba.json "https://cmsweb.cern.ch/phedex/datasvc/json/prod/blockarrive?dataset='+ds+'" > /dev/null 2>/dev/null'
  if debug: print cmd
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
    if block not in dsInstance.blocks:
      dsInstance.blocks[block] = TMDBBlock(block)
    dsInstance.blocks[block].files[lfn] = f
    blockArrive = blockArrives[block]
    for s in f.missing:
      f.missing[s] = (blockArrive[sub('Buffer','MSS',s)]['basis'],blockArrive[sub('Buffer','MSS',s)]['eta'])

  print dsInstance

if verbose:
  for lfn in stuckLFNs:
    print lfn