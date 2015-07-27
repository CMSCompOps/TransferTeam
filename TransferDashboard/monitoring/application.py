from flask import Flask, render_template, url_for, request, redirect, flash, jsonify
from flask import session as login_session
import random, string, os

import httplib2
import json
from flask import make_response
import requests

import time

app = Flask(__name__)
app.secret_key = 'cvAETf4adFASD4VDS4FB2fas'

@app.route('/')
def main():
    jsonData = json.load(open(os.path.join('static', 'data', 'transfers.json'), 'r'))
    jsonSites = jsonData['transfers']
    timeCreateTransfer = time.strftime('%Y/%m/%d', time.gmtime(jsonData['time_create']))
    sites = [{'name': site, 'count': len(jsonSites[site])} for site in jsonSites.keys()]
    
    jsonData  = json.load(open(os.path.join('static', 'data', 'errors.json'), 'r'))
    jsonErrors = jsonData['errors']
    timeCreateError = time.strftime('%Y/%m/%d', time.gmtime(jsonData['time_create']))
    errors = [{'name': error, 'count': len(jsonErrors[error])} for error in jsonErrors.keys()]
    
    return render_template('dashboard.html', sites=sites, transfer_time_create=timeCreateTransfer, errors=errors, error_time_create=timeCreateError)

@app.route('/transfer/<string:site_name>')
def transfer(site_name):
    json_data = json.load(open(os.path.join('static', 'data', 'transfers.json'), 'r'))['transfers']
    reqInfo = {}
    for req in json_data[site_name]:
        reqInfo[req] = {'bytes':0, 'node_bytes':0, 'latest_replica':float("inf")}
        for ds in json_data[site_name][req]:
            reqInfo[req]['bytes'] = ds['bytes']
            reqInfo[req]['node_bytes'] = ds['node_bytes']
            reqInfo[req]['latest_replica'] = min(float(ds['latest_replica']), reqInfo[req]['latest_replica'])
        reqInfo[req]['progress'] = (reqInfo[req]['node_bytes'] * 100.0) / reqInfo[req]['bytes']
    
    return render_template('transfer.html', site_name=site_name, site=json_data[site_name], reqInfo=reqInfo, LINK=LINK)

@app.route('/error/<string:error_name>')
def error(error_name):
    json_data = json.load(open(os.path.join('static', 'data', 'errors.json'), 'r'))['errors']
    return render_template('error.html', error_name=error_name, errors=json_data[error_name])


@app.context_processor
def my_utility_processor():

    def getTimeString(seconds):
        """Converts seconds to human-readable string"""
        seconds = long(float(seconds))
        seconds = abs(time.time() - seconds)
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)
     
        minutes = long(minutes)
        hours = long(hours)
        days = long(days)
        
        duration = []
        if days > 100:
            duration.append('>100 days')
        else:
            if days > 0:
                duration.append('%d day' % days + 's'*(days != 1))
            if hours > 0:
                duration.append('%d hour' % hours + 's'*(hours != 1))
            if minutes > 0:
                duration.append('%d minute' % minutes + 's'*(minutes != 1))
            #if seconds > 0:
            #    duration.append('%d second' % seconds + 's'*(seconds != 1))
        return ' '.join(duration)

    MB = 1000.0 ** 2
    GB = 1000.0 ** 3
    TB = 1000.0 ** 4
    def getSizeString(size, ext = True):
        """Converts size in bytes to human-readable string"""
        size = float(size)
        if size < GB:
            return ("%.3f MB" if ext else "%.3f") % (size/MB)
        elif size < 10*TB:
            return ("%.3f GB" if ext else "%.3f") % (size/GB)
        else:
            return ("%.3f TB" if ext else "%.3f") % (size/TB)
        
    return dict(getTimeString=getTimeString, getSizeString=getSizeString)

baseURL = 'https://cmsweb.cern.ch/phedex/'
baseWebPageURL = baseURL + 'prod/'
baseDatasvcURL = baseURL + 'datasvc/xml/prod/'
# handy links to use in the monitoring page to allow users easy navigation with actual PhEDEx pages
LINK = {
    'Routing': baseWebPageURL + 'Activity::Routing?showinvalid=on&tofilter=%s&blockfilter=%s',
    'Transfer': baseWebPageURL + 'Activity::TransferDetails?andor=and&tofilter=%s',
    'SubscriptionByDataset': baseWebPageURL + 'Data::Subscriptions#state=create_since=0&node=%s&filter=%s',
    'SubscriptionByRequest': baseWebPageURL + 'Data::Subscriptions#state=create_since=0&node=%s&request=%s',
    'QueuePlot': baseWebPageURL + 'Activity::QueuePlots?graph=request&no_mss=false&period=l24h&dest_filter=%s',
    'LinkByDestination': baseWebPageURL + 'Components::Links?to_filter=%s',
    'LinkBySourceDestination': baseWebPageURL + 'Components::Links?andor=and&to_filter=%s&from_filter=%s',
    'IncompleteBlockReplicas': baseDatasvcURL + 'blockreplicas?complete=n&dataset=%s',
    'FileReplicasByDataset': baseDatasvcURL + 'filereplicas?dataset=%s',
    'MissingFilesByDataset': baseDatasvcURL + 'missingfiles?block=%s%%23*&node=%s',
    'SuspendScript': 'https://github.com/dmwm/PHEDEX/blob/master/Utilities/RouterSuspend'
}

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=8080)
