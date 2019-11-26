#!/usr/bin/env python

import os
import sys
import time
import subprocess
import urllib
import json
from datetime import datetime
import requests
import collections
import stomp
import argparse
from CMSMonitoring.StompAMQ import StompAMQ
import uuid
import hashlib
import stomp
from uuid import uuid4
import time


class OptionParser():
    def __init__(self):
        "User based option parser"
        self.parser = argparse.ArgumentParser()
        msg = "Send aaa subscription json file via StompAMQ to a broker, provide broker credentials in JSON file"
        self.parser.add_argument("--amq", action="store",
                                 dest="amq", default="", help=msg, required=True)
        msg = " provide data json file"
        self.parser.add_argument("--data", action="store",
                                 dest="subscription_data", default="", help=msg, required=True)


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


if __name__ == "__main__":
    optmgr = OptionParser()
    opts = optmgr.parser.parse_args()
    if opts.subscription_data:
        try:
            with open(opts.subscription_data, 'r') as f:
                payload = json.load(f)
        except IOError:
            print("File not accessible")

    if opts.amq:
        creds = credentials(opts.amq)
        username = creds['username']
        password = creds['password']
        topic = creds['topic']
        host, port = creds['host_and_ports'].split(':')
        port = int(port)
        ckey = os.path.join("/root/pradeep/send_aaa_matrics/", 'userkey.pem')
        cert = os.path.join("/root/pradeep/send_aaa_matrics/", 'usercert.pem')
        producer = creds['producer']
        topic = creds['topic']
        if creds and StompAMQ:
            amq = StompAMQ(username, password, producer, topic, key=ckey,
                           cert=cert, validation_schema=None, host_and_ports=[(host, port)])
            data = []
            for doc in payload:
                hid = int(uuid4())
                notification, _, _ = amq.make_notification(doc, hid)
                data.append(notification)
            results = amq.send(data)
            print("results", results)
