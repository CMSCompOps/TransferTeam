#!/usr/bin/env python

import os
import sys
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
import stomp
from uuid import uuid4
from urllib.request import urlopen
import time

print("stomp version", stomp.__version__)


class OptionParser():
    def __init__(self):
        "User based option parser"
        self.parser = argparse.ArgumentParser()
        msg = "Send aaa subscription json file via StompAMQ to a broker, provide broker credentials in JSON file"
        self.parser.add_argument("--amq", action="store",
                                 dest="amq", default="", help=msg, required=True)


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
    url = 'http://vocms039.cern.ch/aaa-fedinfo/federations.json'
    result = json.load(urlopen(url))
    fed_data = createFlattenJson(result)
    f = open("fed.json", "r")
    for x in f:
        data = json.loads(x)
        yield data

def createFlattenJson(json_file):
    '''
    flattens the federation.json file
    '''
    for k,v in json_file.items():
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
            my_json = ('{"siteName" : "%s", "state" : "%s", "statusCode" : %s, "stateName" : "%s"}' %(site, k, statusCode, stateName))
            with open("fed.json","a") as f:
                f.write("%s\n" %my_json)

if __name__ == "__main__":
    optmgr = OptionParser()
    opts = optmgr.parser.parse_args()
    payload = parseFederationJson()
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
        if creds and StompAMQ:
            amq = StompAMQ(username, password, producer, topic, key=None,
                           cert=None, validation_schema=None, host_and_ports=[(host, port)])
            eod = False
            wait_seconds = 10
            while not eod: 
                messages = []
                for d in payload:
                    notif,_,_ = amq.make_notification(d, "aaa_federations_document", dataSubfield=None)
                    messages.append(notif)
                if messages:
                    print(messages)
                    amq.send(messages)
                    time.sleep(wait_seconds)
                else:
                    eod = True
