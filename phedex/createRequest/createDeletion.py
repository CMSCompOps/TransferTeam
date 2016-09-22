import json
import urllib2,urllib, httplib, sys, re, os
from xml.dom.minidom import getDOMImplementation
import phedexClient as phd
import dbs3Client as dbs
from optparse import OptionParser
"""
    Basic script for deleting datasets. It creates deletion requests
    for the all sites that have the sample
"""

test = False
url = 'cmsweb.cern.ch'

def prepareDeletionRequests(datasets):
    """
    make a single deletion request per bunch of datasets
    Filtering only the INVALID or DEPRECATED ones
    """
    
    size = 30

    #delete duplicates
    datasets = list(set(datasets))
    
    #group datasets by sites
    requests = {}
    for ds in datasets:
        try:
            t = dbs.getDatasetStatus(ds)
            #filter by status
            if t != 'INVALID' and t != 'DEPRECATED':
                continue
            sites = phd.getBlockReplicaSites(ds, onlycomplete=False)
            for s in sites:
                #ignore buffers
                if "Buffer" in s or "Export" in s:
                    continue
                if s not in requests:
                    requests[s] = []
                requests[s].append(ds)
        except Exception as e:
            print "error:",ds,e
    

    return requests

def submitDeletionRequests(requests):
    deletionRequests = []
    for site in sorted(requests.keys()):
        datasets = requests[site]
        print "site:", site
        print "datasets to delete:"
        print '\n'.join(datasets)
        if not test:
            r = phd.makeDeletionRequest(url, [site], datasets, "Deletion Campaign for INVALID data")
            if ("phedex" in r and "request_created" in r["phedex"]):
                reqid = r["phedex"]["request_created"][0]["id"]
                deletionRequests.append(reqid)
            else:
                print r
    return deletionRequests

def main():
    usage = "usage: %prog [options] workflow"
    parser = OptionParser(usage=usage)
    parser.add_option("-f","--file", dest="fileName", default=None,
                        help="Input file")
    (options, args) = parser.parse_args()

    if options.fileName is None:
        parser.error("Provide a file contains dataset list")
        sys.exit(1)
    
    with open(options.fileName) as f:
        datasets = f.read().splitlines()
        reqs = prepareDeletionRequests(datasets)
        submittedReqs = submitDeletionRequests(reqs)

        print '\n'.join(submittedReqs)

if __name__ == "__main__":
    main()
