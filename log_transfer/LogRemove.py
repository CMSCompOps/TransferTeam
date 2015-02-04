import time
from Common import Request
from Common import Logger
try: import json
except ImportError: import simplejson as json

urlPhedex = 'https://phedex-dev.cern.ch/phedex/datasvc/json/ops/'
urlDelete = urlPhedex + 'delete'

def getOldDatasets():
    datasetList = []
    date = time.time() - 60*60*24*2
    urlSubscription = urlPhedex + 'subscriptions?node=T2_CH_CERN&dataset=/Log*/*/*&create_since=!%s' % date
    result = json.loads(request.send(urlSubscription))
    for dataset in result['phedex']['dataset']:
        datasetList.append(dataset['name'])
    return datasetList

if __name__ == '__main__':
    # Get request object for future PhEDEx calls
    request = Request()

    # get datasets with subscription to EOS older than N months
    Logger.log('retrieving list of old datasets'
    oldDatasets = getOldDatasets();
    Logger.log('number of old datasets: %s' % len(oldDatasets))

