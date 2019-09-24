#!/usr/bin/env python
import sys
import os
import json
import urllib2

## This tools uses Phedex API blockarrive
## USAGE: python find_missing_datasets.py 

def get_missing_data():
    url='https://cmsweb.cern.ch/phedex/datasvc/json/prod/nodes'
    result = url_reading(url)
    sites = get_node_name(result)
    for site in sites:
        get_block_with_no_source_replica(site)

def get_node_name(result):
    sites_list = [];
    for node in result['phedex']['node']:
        if "T1" in node['name'] or "T2" in node['name']:
            sites_list.append(node['name'])
    return sites_list

def get_block_with_no_source_replica(site):
    url='https://cmsweb.cern.ch/phedex/datasvc/json/prod/blockarrive?&basis=-6&to_node=' + site
    result = url_reading(url)
    with open('missing_data.txt', 'a+') as f:
        f.write("%s\r\n" %site)
        for block in result['phedex']['block']:
            f.write("%s\r\n" %block['dataset'])

def url_reading(url):
    jstr = urllib2.urlopen(url).read()
    jstr = jstr.replace("\n", " ")
    result = json.loads(jstr)
    return result

def init():
    get_missing_data()

init()
