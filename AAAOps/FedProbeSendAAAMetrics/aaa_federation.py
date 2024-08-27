#!/usr/bin/env python
import re
import sys

#RHEL8 default is 7.0.0 __requires__ = 'stomp.py==4.1.21'
__requires__ = 'stomp.py==7.0.0'

from pkg_resources import load_entry_point
import stomp

import os
import subprocess
import urllib
import json
from datetime import datetime
import collections
import stomp
import argparse
from CMSMonitoring.StompAMQ import StompAMQ
import uuid
from itertools import islice
import hashlib
from uuid import uuid4
from urllib.request import urlopen
import time
#RHEL8
# CMSMonitoring modules
try:
    from CMSMonitoring.StompAMQ7 import StompAMQ7
except ImportError:
    print("ERROR: Could not import StompAMQ7")
    sys.exit(1)

print("stomp version", stomp.__version__)

FedProbeSendAAAMetrics = '/opt/TransferTeam/AAAOps/FedProbeSendAAAMetrics/'
FedProbeSendAAAMetrics = '/opt/TransferTeam/AAAOps/FedProbeSendAAAMetrics/'

class OptionParser():
    def __init__(self):
        "User based option parser"
        self.parser = argparse.ArgumentParser()
        msg = "Send aaa subscription json file via StompAMQ to a broker, provide broker credentials in JSON file"
        self.parser.add_argument("--amq", action="store",
                                 dest="amq", default="", help=msg, required=True)
        #self.parser.add_argument("--create_json_only", action="store",
        #                         dest="create_json_only", default="", help=msg, required=False)


class MyListener(stomp.ConnectionListener):
    def on_error(self, headers, message):
        print('received an error "%s"' % message)

    def on_message(self, headers, message):
        print('received a message "%s"' % message)


def credentials(fname=None):
    "Read credentials from MONIT_BROKER environment"
    if not fname:
        fname = os.environ.get('MONIT_BROKER', '')
    if not os.path.isfile(fname):
        raise Exception(
            "Unable to locate MONIT credentials, please setup MONIT_BROKER")
        return {}
    with open(fname, 'r') as istream:
        data = json.load(istream)
    return data

def parseFederationJson():
    '''
    modifies federation.json  with tags and
    Return json object to feed cern metris
    '''
    #url = 'http://vocms039.cern.ch/aaa-fedinfo/federations.json'
    #result = json.load(urlopen(url))
    #print ("open f")
    with open(FedProbeSendAAAMetrics+'out/federations.json') as f: url = f.read()
    #print ("url ",url)
    result = json.loads(url)

    if result['prod'] and result['trans']:
        fed_data = createFlattenJson(result)
        #print (opts.create_json_only)
        f = open(FedProbeSendAAAMetrics+"fed.json", "r")
        #if opts.create_json_only :
        #  print (" 2 ",opts.create_json_only)
        #  for x in f:
        #    data = json.loads(x)
        #else:
        for x in f:
          data = json.loads(x)
          #print ( data )
          yield data

def createFlattenJson(json_file):
    '''
    flattens the federation.json file
    '''
    #print ("createFlattenJson")
    for k,v in json_file.items():
        #print ( k, v.keys() )
        #for dic in v:
        #   print ( k, dic.keys() )
        #break
        if ("prod" in k):
            statusCode = 1
            stateName = "Production Federation"
        elif ("trans" in k):
            statusCode = 2
            stateName = "Transitional Federation"
        else:
            statusCode = 3
            stateName = "not at any federation"
        for site in v:
            #print ( k, site )       
            #my_json = ('{"siteName" : "%s", "state" : "%s", "statusCode" : %s, "stateName" : "%s"}' %(site, k, statusCode, stateName))
            #for isite in range(len(site['sites'])):
            #   if 'XROOTD' not in site['flavors'][isite] : continue
            #   #contact = site['contact'][0]
            #   ##print (site['sites'][isite], " contact len ",len(site['contact']))
            #   #if not contact : contact = site['contact'][(len(site['contact']) - 1)]
            #   #print (" s = ",site['sites'][isite], site['flavors'][isite], site['endpoints'][isite], site['federation'][isite]) #print (" site = ",site['sites'])
            my_json = ('{"siteName" : "%s", "state" : "%s", "statusCode" : %s, "stateName" : "%s", "flavor" : "%s", "endpoint" : "%s", "xrootd_version" : "%s", "xrootd_role" : "%s", "storage" : "%s", "contact" : "%s"}' %(site['sites'], k, statusCode, stateName, site['flavors'], site['endpoints'], site['xrootd_version'], site['xrootd_role'], site['xrootd_storage'], site['contact']))
            with open(FedProbeSendAAAMetrics+"fed.json","a") as f:
                f.write("%s\n" %my_json)

if __name__ == "__main__":
    #RHEL8
    ts = int(time.time()) * 1000
    #RHEL8
    optmgr = OptionParser()
    opts = optmgr.parser.parse_args()
    payload = parseFederationJson()
    #for ipay in payload:  #bockjoo comment this out when in production
    #    print (ipay)      #bockjoo comment this out when in production
    ##print ("Check "+FedProbeSendAAAMetrics+"fed.json")
    #sys.exit(0) # bockjoo to uncomment
    if opts.amq:
        creds = credentials(opts.amq)
        username = creds['username']
        password = creds['password']
        topic = creds['topic']
        host, port = creds['host_and_ports'].split(':')
        port = int(port)
        producer = creds['producer']
        topic = creds['topic']
        hosts = [(host, port)]
        #RHEL8
        doc_type = creds['type']
        #RHEL8 if creds and StompAMQ:
        #RHEL8     amq = StompAMQ(username, password, producer, topic, key=None,
        #RHEL8                   cert=None, validation_schema=None, host_and_ports=[(host, port)])
        if creds and StompAMQ7:
            amq = StompAMQ7(username, password, producer, topic, key=None,
                           cert=None, validation_schema=None, host_and_ports=[(host, port)])
            eod = False
            wait_seconds = 10
            while not eod: 
                messages = []
                for d in payload:
                    #RHEL8 notif,_,_ = amq.make_notification(d, "aaa_federations_document", dataSubfield=None)
                    notif,_,_ = amq.make_notification(payload=d, doc_type=doc_type,
                                                          producer=producer, ts=ts)
                    messages.append(notif)
                if messages:
                    print(messages)
                    amq.send(messages)
                    time.sleep(wait_seconds)
                else:
                    eod = True
