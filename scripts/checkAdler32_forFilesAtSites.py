#!/usr/bin/env python
import os
import sys
import subprocess
import urllib
import json

## This tool will get all replicas register for a particular LFN and will return the CMS sites + PFN + checksum (of the corrupt file).
## USAGE: python checkAdler32ForFilesAtSites.py <LFN>

def init():
        f = str(sys.argv[1])
        get_cksum_from_catalog(f)
        get_file_replicas(f)
        get_cksum_from_replica(f)

def get_cksum_from_catalog(lfn):
        url = 'https://cmsweb.cern.ch/phedex/datasvc/json/prod/data?file=' + lfn
        result = json.load(urllib.urlopen(url))
        for p in result['phedex']['dbs']:
                for d in p['dataset']:
                        for b in d['block']:
                                for f in b['file']:
                                        adler32.append(str(f['checksum']).split(',')[0].split(':')[1])

def get_file_replicas(lfn):
        url = 'https://cmsweb.cern.ch/phedex/datasvc/json/prod/filereplicas?lfn=' + lfn
        result = json.load(urllib.urlopen(url))
        for b in result['phedex']['block']:
                for f in b['file']:
                        for r in f['replica']:
                                sites.append(r['node'])

def get_cksum_from_replica(lfn):
        print "-----------------------"
        print "FILE: " + lfn
        print "TMDB: " + adler32[0]
        print "Replicas: (" + str(len(sites)) + ") " + str(sites).replace("u'","").replace("'","").replace("[","").replace("]","")
        print "-----------------------"
        for s in range(len(sites)):
                url = 'https://cmsweb.cern.ch/phedex/datasvc/json/prod/lfn2pfn?protocol=srmv2&lfn=' + str(lfn) + '&node=' + str(sites[s])
                result = json.load(urllib.urlopen(url))
                for m in result['phedex']['mapping']:
                        pfn.append(m['pfn'])
                        cmd = "gfal-sum " + pfn[s] + " adler32"
                        result = subprocess.check_output(cmd, shell=True)
                        cksm = str(result).split('.root ')[1]
                        if str(adler32[0]).strip() != str(cksm).strip():
                                print "site: " + sites[s] + " - " + result

sites = []
adler32 = []
pfn = []
corrupted = []
init()