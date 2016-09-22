import json
import urllib2,urllib, httplib, sys, re, os
import phedexClient as phd
import dbs3Client as dbs
from optparse import OptionParser

"""
    Basic script for transfer datasets. It creates a transfer request
    for the datasets and site specified
"""

test = False
priority = 'normal'
custodial = 'y'
url = 'cmsweb.cern.ch'

def submitTransferRequests(dataset_list, nodeName, chunk_size):
        
    transferRequests = []
    chunks = [dataset_list[x:x+chunk_size] for x in xrange(0, len(dataset_list), chunk_size)]
    for chunk in chunks:

        print "\nSite:", nodeName
        print "Datasets to subscribe:"
        print '\n'.join(chunk)

        if not test:
            r = phd.makeReplicaRequest(url, nodeName, chunk, "Transfer Team is subscribing datasets without custodial replica", priority, custodial)
            if ("phedex" in r and "request_created" in r["phedex"]):
                reqid = r["phedex"]["request_created"][0]["id"]
                transferRequests.append(reqid)
            else:
                print r
    return transferRequests

def main():
    usage = "usage: %prog [options]"
    parser = OptionParser(usage=usage)
    parser.add_option("-f","--file", dest="fileName", default=None, help="Input file with list of datasets to be transferred")
    parser.add_option("-n","--node", dest="nodeName", default=None, help="Node name to transfer the data")
    parser.add_option("-c","--chunk", dest="chunk", default=0, type=int,  help="Number of datasets per transfer request")
    (options, args) = parser.parse_args()

    if (options.fileName is None) or (options.nodeName is None) or (options.chunk == 0):
        parser.error("Provide node name to transfer the data to, file containing dataset list and number of datasets per transfer request")
        sys.exit(1)
   
    node = options.nodeName
    chunk = options.chunk
 
    with open(options.fileName) as f :
        datasets = f.read().splitlines()
        submittedReqs = submitTransferRequests(datasets,node,chunk)

        print '\n'.join(submittedReqs)

if __name__ == "__main__":
    main()
