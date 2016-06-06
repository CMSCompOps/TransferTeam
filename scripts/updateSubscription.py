#!/usr/bin/env python

import os
import pycurl
import urllib
from optparse import OptionParser

def updateSubscription(block, node, priority):
    proxyfile='/tmp/x509up_u'+str(os.getuid())
    cadir='/etc/grid-security/certificates'

    c = pycurl.Curl()
    c.setopt(pycurl.CAINFO,proxyfile)
    c.setopt(pycurl.CAPATH,cadir)
    c.setopt(pycurl.SSLKEY,proxyfile)
    c.setopt(pycurl.SSLCERT,proxyfile)
    
    url='https://cmsweb.cern.ch/phedex/datasvc/perl/prod/updatesubscription?block=' + block.replace('#','%23',1) + '&node=' + node + '&suspend_until=' + priority
    if debug == True : print url 
 
    c.setopt(pycurl.URL, url)
    post_data = {'block': block , 'node': node , 'suspend_until': priority}

    postfields = urllib.urlencode(post_data)
    c.setopt(c.POSTFIELDS, postfields)
    c.perform()

usage  = "Usage: %prog --block <block> --node <node> --priority <low,normal,high>"
parser = OptionParser(usage=usage)
parser.add_option("-v", "--verbose", action="store_true", default=False, dest="verbose", help="verbose output")
parser.add_option("-b", "--block", action="store", type="string", default="None", dest="block", help="Block Name")
parser.add_option("-n", "--node", action="store", type="string", default="None", dest="node", help="Node Name")
parser.add_option("-p", "--priority", action="store", type="string", default="None", dest="priority", help="Priority")

(opts, args) = parser.parse_args()

if (opts.block == None or opts.node == None or opts.priority == None):
    parser.error("Define block, node and priority")

block = opts.block
node = opts.node
priority = opts.priority
debug = opts.verbose

result = updateSubscription(block, node, priority)
