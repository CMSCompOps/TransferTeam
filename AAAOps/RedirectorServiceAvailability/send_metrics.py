#python3

# For a file where each line is a json valid document
# send those documents to metrics.
# Original script for AAAops

import sys
import json
import requests
import traceback
import time
from datetime import datetime

html_dir = '/var/www/html/aaa-probe/'
probes_json='KIBANA_PROBES_GENERAL.json'

def update_dic_metrics(dic,metric_name,timestamp):
    dic.update({'producer':'cmsaaa'})
    dic.update({'type':metric_name})
    dic.update({'timestamp':timestamp})

    if dic.get('status')=='Available' and dic.get('version')!='':
        dic.update({'codeStatus':1})#Available
        
    if dic.get('status')=='Unavailable' or dic.get('status')=='Degraded':
        if dic.get('version')=='':
            dic.update({'codeStatus':0})#Unavailable
        else:
            dic.update({'codeStatus':2})#Degraded
    dic.update({'catCode':''})
    if dic.get('host')=='cms-xrd-global.cern.ch' or dic.get('host')=='cmsxrootd.fnal.gov' or dic.get('host')=='cms-xrd-transit.cern.ch':
        dic.update({'catCode':0})
   
    if dic.get('host')=='cms-xrd-global01.cern.ch' or dic.get('host')=='cms-xrd-global02.cern.ch':
        dic.update({'catCode':1})

    if dic.get('host')=='cmsxrootd2.fnal.gov' or dic.get('host')=='xrootd.unl.edu':
        dic.update({'catCode':2})
    
    #if dic.get('host')!='cms-xrd-global.cern.ch' or dic.get('host')!='cms-xrd-transit.cern.ch' or dic.get('host')!='cms-xrd-global01.cern.ch' or dic.get('host')!='cms-xrd-global02.cern.ch' or dic.get('host')!='cmsxrootd2.fnal.gov' or dic.get('host')!='xrootd.unl.edu':
        #dic.update({'catCode':3})

    if dic.get('host')=='vocms031.cern.ch' or dic.get('host')=='vocms032.cern.ch':
        dic.update({'catCode':4})

    if dic.get('catCode')=='':
        dic.update({'catCode':3})

    dic.update({'idb_fields':['codeStatus','status','Comment','version','service','host','xrdcp_below_time','xrdcp_above_time']})
    dic.update({'idb_tags':['status','host','codeStatus','catCode']})


def send(document):
    return requests.post('http://monit-metrics:10012/', data=json.dumps(document), headers={ "Content-Type": "application/json; charset=UTF-8"})

def send_and_check(document, should_fail=False):
    response = send(document)
    assert( (response.status_code in [200]) != should_fail), 'With document: {0}. Status code: {1}. Message: {2}'.format(document, response.status_code, response.text)

def openjson_send(path,filename,metric_name,timestamp):
    with open(path+filename) as jsonfile:
        for line in jsonfile:
            dic_line=(json.loads(line))
            update_dic_metrics(dic_line,metric_name,timestamp)
            send_and_check(dic_line)
            #print(dic_line)

def main():
    metric_name="infrastructure"
    now=datetime.now()
    timestamp=int(datetime.timestamp(now))*1000

    try:
        print("Opening and sending documents")
        openjson_send(html_dir,probes_json,metric_name,timestamp)
        print("Done")

    except Exception:
        print("Exception in checker procedure:")
        traceback.print_exc()
        sys.exit(2)
if __name__=="__main__":
    sys.exit(main())
