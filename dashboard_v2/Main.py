#!/usr/bin/env python
import json, collections
from HTMLBuilder import HTMLBuilder

try:
    import json
except ImportError:
    import simplejson as json

GB = 1000.0 ** 3
TB = 1000.0 ** 4

pageList=[{'link':'index.html', 'text':'Transfers', 'active':True},
          {'link':'error.html', 'text':'Errors', 'active':False}]

builder = HTMLBuilder();
elContainer = builder.createDocument(pageList)  



baseURL = 'https://cmsweb.cern.ch/phedex/'
baseWebPageURL = baseURL + 'prod/'
baseDatasvcURL = baseURL + 'datasvc/xml/prod/'

link = {
'Routing': baseWebPageURL + 'Activity::Routing?showinvalid=on&tofilter=%s&blockfilter=%s',
'Transfer': baseWebPageURL + 'Activity::TransferDetails?andor=and&tofilter=%s',
'SubscriptionByDataset': baseWebPageURL + 'Data::Subscriptions#state=create_since=0&node=%s&filter=%s',
'SubscriptionByRequest': baseWebPageURL + 'Data::Subscriptions#state=create_since=0&node=%s&request=%s',
'QueuePlot': baseWebPageURL + 'Activity::QueuePlots?graph=request&no_mss=false&period=l24h&dest_filter=%s',
'LinkByDestination': baseWebPageURL + 'Components::Links?to_filter=%s',
'LinkBySourceDestination': baseWebPageURL + 'Components::Links?andor=and&from_filter=%s&to_filter=%s',
'IncompleteBlockReplicas': baseDatasvcURL + 'blockreplicas?complete=n&dataset=%s',
'FileReplicasByDataset': baseDatasvcURL + 'filereplicas?dataset=%s',
'SuspendScript': 'https://github.com/dmwm/PHEDEX/blob/master/Utilities/RouterSuspend'
}

basisInfo={
   2:{'text':'Waiting for re-routing', 'link':link['Routing']},
   1:{'text':'Destination Queue Full', 'link':link['QueuePlot']},
   0:{'text':'OK', 'link':''},
  -1:{'text':'Open Block', 'link':link['IncompleteBlockReplicas']},
  -2:{'text':'Suspended manually', 'link':link['SubscriptionByDataset']},
  -3:{'text':'No download link', 'link':link['LinkByDestination']},
  -4:{'text':'Suspended by Router', 'link':link['SuspendScript']},
  -5:{'text':'Missing Link', 'link':link['LinkBySourceDestination']},
  -6:{'text':'No replica', 'link':link['FileReplicasByDataset']}
}


def getDatasetInfo(data):
    info = collections.OrderedDict()
    info['Name'] = data['name']
    info['Transferred Files'] = "%s / %s" % (data['node_files'], data['files'])
    info['Transferred Bytes'] = "%s / %s" % (builder.getSizeString(data['node_bytes'], ext=False), builder.getSizeString(data['bytes']))
    info['Routed Files'] = builder.createLink(data['route_files'], link['Routing'] % (data['destination'], data['name']))
    info['Files In Transfer'] = builder.createLink(data['xfer_files'], link['Transfer'] % data['destination'])
    info['Latest file transfer'] = builder.getTimeString(data['latest_replica'])
    info['Replica'] = ','.join(data['replica'])
    info['Routed From'] = ','.join(data['source'])
    info['Block Level Problems'] = getBasisHTML(data)
    info['ETA'] = builder.getTimeString(data['time_arrive'])
    return info


def getBasisHTML(data):
    labels = ""
    for basis in data['basis']:
        basis = int(basis)
        if basis == 2:
            link = builder.createLink(basisInfo[basis]['text'], basisInfo[basis]['link'] % (data['destination'], data['name']))
        elif basis == 1:
            link = builder.createLink(basisInfo[basis]['text'], basisInfo[basis]['link'] % data['destination'])
        elif basis == 0:
            link = basisInfo[basis]['text']
        elif basis == -1:
            link = builder.createLink(basisInfo[basis]['text'], basisInfo[basis]['link'] % data['name'])
        elif basis == -2:
            link = builder.createLink(basisInfo[basis]['text'], basisInfo[basis]['link'] % (data['destination'], data['name']))
        elif basis == -3:
            link = builder.createLink(basisInfo[basis]['text'], basisInfo[basis]['link'] % data['destination'])
        elif basis == -4:
            link = builder.createLink(basisInfo[basis]['text'], basisInfo[basis]['link'])
        elif basis == -5:
            link = builder.createLink(basisInfo[basis]['text'], basisInfo[basis]['link'] % (data['destination'], '|'.join(data['replica'])))
        elif basis == -6:
            link = builder.createLink(basisInfo[basis]['text'], basisInfo[basis]['link'] % data['name'])
        
        if basis > 0:
            color = "warning"
        elif basis < 0:
            color = "danger"
        else:
            color = "success"
            
        labels += builder.toString(builder.createLabel(link, clazz=color+" basis%s"%basis))
    return labels

with open("output.txt") as f:
    data = json.load(f)
    
    # create empty panel container
    elPanel = builder.createPanelContainer()
    for node in data:
        
        # create table for requests
        elRequestTable = builder.createTable(['Req No','Total TB','Completion','Time Create'])
        for request in data[node]:
            # create div for dataset info container
            elDatasetContainer = builder.createDiv()
            for datasetInfo in data[node][request]:
                datasetInfo['destination'] = node
                info = getDatasetInfo(datasetInfo)
                # create dataset info box for each dataset in the request
                elDatasetTable = builder.createTableWith2Col(info, fontSize=10)
                builder.addChild(elDatasetContainer,elDatasetTable)


            # calc values for request by using all the datasets in it
            reqInfo = {}
            reqInfo['bytes'] = sum([long(x['bytes']) for x in data[node][request]])
            reqInfo['node_bytes'] = sum([long(x['node_bytes']) for x in data[node][request]])
            reqInfo['time_create'] = data[node][request][0]['time_create']
            
            
            # create tr for each request
            elRequestRow = builder.createRow([builder.createLink(request, link['SubscriptionByRequest'] % (node,request)),
                                              builder.getSizeString(reqInfo['bytes']), 
                                              ("%.3f" % ((reqInfo['node_bytes']*100.0) / reqInfo['bytes']))[:-1] + "%", # to prevent rounding from 99.99 to 100
                                              builder.getTimeString(reqInfo['time_create'])],
                                             clazz="warning searchable_request")
            # add tr into table
            builder.addChild(elRequestTable, elRequestRow)
            
            elDatasetCollapsible = builder.createCollapsible(elRequestRow,elDatasetContainer)
            # add collapsible row into table
            builder.addChild(elRequestTable, elDatasetCollapsible)

        # create panel for each node, and add request table inside
        panelItem = builder.addPanelItem(node, elRequestTable, "searchable_node")
        # add panel into panel container
        builder.addChild(elPanel,panelItem)

# add panel to the root parent
builder.addChild(elContainer, builder.createSearchBox())
builder.addChild(elContainer, elPanel)
builder.save("index.html")


#
# Create Error page
#
pageList=[{'link':'index.html', 'text':'Transfers', 'active':False},
          {'link':'error.html', 'text':'Errors', 'active':True}]

builder = HTMLBuilder();
elContainer = builder.createDocument(pageList)
#with open("error.json") as f:
#    data = json.load(f)
    #elTable = data['%No%file%']

# create empty panel container
elPanel = builder.createPanelContainer()

elTable = builder.createJSONTable("error.json", ["lfn","source","destination"])
panelItem = builder.addPanelItem("No file", elTable)

# add panel into panel container
builder.addChild(elPanel,panelItem)

builder.addChild(elContainer, elPanel)
builder.save("error.html")