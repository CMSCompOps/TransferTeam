from flask import Flask, render_template, url_for, request, redirect, flash, jsonify
from flask import session as login_session
from flask import make_response

import random
import string
import os
import json
import time
import re

app = Flask(__name__)
app.secret_key = 'cvAETf4adFASD4VDS4FB2fas'

@app.route('/')
def main():
    """Shows the dashboard"""
    jsonData = json.load(open(os.path.join('static', 'data', 'transfers.json'), 'r'))
    jsonSites = jsonData['transfers']
    timeCreateTransfer = time.strftime('%Y/%m/%d %H:%M', time.gmtime(jsonData['time_create']))
    sites = [{'name': site, 'count': len(jsonSites[site])} for site in jsonSites.keys()]
    
    jsonData  = json.load(open(os.path.join('static', 'data', 'errors.json'), 'r'))
    jsonErrors = jsonData['errors']
    timeCreateError = time.strftime('%Y/%m/%d %H:%M', time.gmtime(jsonData['time_create']))
    errors = [{'name': error, 'count': len(jsonErrors[error])} for error in jsonErrors.keys()]

    jsonData  = json.load(open(os.path.join('static', 'data', 'storages.json'), 'r'))
    jsonStorages = jsonData['storages']
    timeCreateStorage = time.strftime('%Y/%m/%d %H:%M', time.gmtime(jsonData['time_create']))
    storages = [{'name': storage} for storage in jsonStorages.keys()]
    
    return render_template('dashboard.html',
                           sites=sites, transfer_time_create=timeCreateTransfer,
                           errors=errors, error_time_create=timeCreateError,
                           storages=storages, storage_time_create=timeCreateStorage)

@app.route('/transfer/<string:site_name>')
def transfer(site_name):
    """Shows the ongoing transfers for the given site"""
    json_data = json.load(open(os.path.join('static', 'data', 'transfers.json'), 'r'))['transfers']
    reqInfo = {}
    for req in json_data[site_name]:
        reqInfo[req] = {'bytes':0, 'node_bytes':0, 'latest_replica':float("inf")}
        for ds in json_data[site_name][req]:
            reqInfo[req]['time_create'] = ds['time_create']
            reqInfo[req]['bytes'] += ds['bytes']
            reqInfo[req]['node_bytes'] += ds['node_bytes']
            reqInfo[req]['latest_replica'] = min(float(ds['latest_replica']), reqInfo[req]['latest_replica'])
        
        reqInfo[req]['progress'] = (reqInfo[req]['node_bytes'] * 100.0) / reqInfo[req]['bytes']
    
    return render_template('transfer.html', site_name=site_name, site=json_data[site_name], reqInfo=reqInfo, LINK=LINK)


@app.route('/storage/<string:storage_name>')
def storage(storage_name):
    """Shows the storage usage for the given site"""
    json_data = json.load(open(os.path.join('static', 'data', 'storages.json'), 'r'))['storages'][storage_name]
    size_by_type = {}
    size_by_tier = {}
    size_by_era = {}
    
    unknown_samples = []
    for ds in json_data:

        # get tier/era/type of the dataset
        dsInfo = getDatasetInfo(ds)
        type = dsInfo['type']
        tier = dsInfo['tier']
        era = dsInfo['era']

        # check each block in the dataset
        for block in json_data[ds]:
            bytes = int(block['node_bytes'])
            
            # check the custodiality
            if block['custodial'] == 'y':
                cust = 'custodial'
            else:
                cust = 'non-custodial'

            # sum the size of the block into the corresponding dictionary
            add(size_by_type, cust, type, bytes)
            add(size_by_tier, cust, tier, bytes)
            add(size_by_era, cust, era, bytes)

    # calculate the total size at the site
    if 'custodial' in size_by_type: 
        size_by_type['custodial']['total'] = sum(size_by_type['custodial'].itervalues())
    if 'non-custodial' in size_by_type:
        size_by_type['non-custodial']['total'] = sum(size_by_type['non-custodial'].itervalues())

    return render_template('storage.html',
                           storage_name=storage_name,size_by_type=size_by_type,
                           size_by_tier=size_by_tier, size_by_era=size_by_era,
                           unknown_samples=unknown_samples)


@app.route('/error/<string:error_name>')
def error(error_name):
    """Shows the transfer errors"""
    json_data = json.load(open(os.path.join('static', 'data', 'errors.json'), 'r'))['errors']
    return render_template('error.html', error_name=error_name, errors=json_data[error_name])


def add(dict, cust, key, val):
    """Helper function to add an item in a dictionary"""
    if cust not in dict:
        dict[cust] = {}

    if key in dict[cust]:
        dict[cust][key] += val
    else:
        dict[cust][key] = val

def getDatasetInfo(ds):
    """Returns the tier, era and type of the given dataset"""
    # get the data tier of the dataset
    tier = ds.split('/')[-1]
    # get the type and era of the dataset 
    for type in ERAS:
        for era in ERAS[type]:
            if era in ds:
                return {'tier': tier, 'era': era, 'type': type}

    return {'tier': tier, 'era':'unknown', 'type':'unknown'}
 
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
        if size == 0:
            return "0"
        elif size < GB:
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


ERAS = {
  'data': (
    'GlobalMar08', 'CRUZET1', 'CRUZET2', 'CRUZET3', 'CRUZET4', 'EW35',
    'CRUZET09', 'CRAFT09', 'BeamCommissioning08', 'Commissioning08', 
    'BeamCommissioning09', 'Commissioning09', 'Commissioning10', 'Run2010A', 
    'Run2010B', 'HIRun2010', 'Commissioning11', 'Run2011A', 'Run2011B', 
    'HIRun2011', 'Commissioning12', 'Run2012A', 'Run2012B', 'Run2012C', 
    'Run2012D', 'PARun2012', 'HIRun2013', 'Run2013A', 'Run2015B' 
  ),
  'mc': (
    'Summer08', 'Fall08', 'Winter09', 'Summer09', 'Spring10', 'Summer10', 
    'Fall10', 'Winter10', 'Spring11', 'Summer11', 'Fall11', 'Summer12', 
    'Summer12_DR53X', 'HiWinter13', 'Nov2011_HI', 'PreProd12_7TeV', 'Summer13',
    'Summer13dr53X','Fall13','HiFall13','UpgFall13','Fall13wmLHE','Fall13pLHE',
    'HiFall11','CommissioningDisk', 'MCRUN2'
  ),
  'other': (
    'RelVal', 'StoreResults', 'CMSSW', 'T0TEST', 'HC', 'SAM', 
    'h2tb2007', 'Online', 'JobRobot','IntegrationTest_130508'
  )
}

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=8080)
