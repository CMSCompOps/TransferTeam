#!/usr/bin/env python

import sys,os,urllib,time, collections
from xml.etree import ElementTree as ET
from xml.dom import minidom

try:
    import json
except ImportError:
    import simplejson as json

datasvcURL = 'https://cmsweb.cern.ch/phedex/datasvc/json/prod/' 
OUTPUT_DIR = '/afs/cern.ch/user/m/mtaze/work/www/dashboard/'
SRC_DIR = os.path.abspath(os.path.dirname(__file__)) + "/"

UNIT = 1000 ** 4 #TB

# headers used in tables
headerNodePanel = ["Node Name", "Latest File Transfer", "Total Size(TB)", "% Bytes", "Oldest Subscription"]
headerNodePanelColmd = [2,3,2,1,3]
colmdForProgressBar = headerNodePanelColmd[3]

headerSubscriptionTable = ["Subscription","Latest File Transfer","Total Size(TB)","% Bytes","Time Create","Estimated Arrival Time"]
headerDatasetTable = ["Dataset","Latest File Transfer","Total Size(TB)","Estimated Arrival Time", "Problem"]

# suggestion tables
suggestionTexts = {
                   "-1": "These blocks are still open, if they are not still being produced, there can be something wrong",
                   "-2":" Transfer of these blocks have been suspended manually, you may want to check subscription page and unsuspend them",
                   "-3": "asdf",
                   "-4": "asdf",
                   "-5": "No link from source to destination, you may want to commission the missing link, or agents might be down",
                   "-6": "Following files don't have replica, you may want to crosscheck&invalidate them"
                   }
suggestionHeaders = {
                     "-1": ["Block","Destination"],
                     "-2": ["Block","Destination"],
                     "-3": [],
                     "-4": [],
                     "-5": ["LFN","Origin Node","Destination"],
                     "-6": ["LFN","Origin Node","Destination"]
                     }


# to prevent iterate over chars, create a list from an element
def getIterable(x):
    if isinstance(x, collections.Iterable):
        return x
    else:
        return [x]

# seconds to human-readible string
def getTimeString(seconds):
    try:
        seconds = long(seconds)
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
    except:
        return "NA"

def to_TB(amount):
    return "%.3f" % (amount / float(UNIT))
def to_3f(amount):
    return "%.3f" % amount


def createCell(data, header=False):
    if header:
        cell = ET.Element("th")
    else:
        cell = ET.Element("td")

    cell.text = str(data)
    return cell

def createHeaders(headerList):
    row = ET.Element("tr")
    for header in headerList:
        row.append(createCell(header, True))
    return row
    
def createDatasetTable(datasets):
    table = ET.Element("table")
    table.set("class", "table table-striped table-bordered table-condensed")
    
    # headers 
    headers = createHeaders(headerDatasetTable)
    table.append(headers)
    
    for dataset in datasets:
        row = ET.Element("tr")
        row.append(createCell(dataset['name']))
        row.append(createCell(getTimeString(dataset['time_update'])))
        row.append(createCell(to_TB(dataset['bytes'])))
        row.append(createCell(getTimeString(dataset['ETA'])))
    
        basisCell = createCell("")
        for basis in getIterable(dataset['basis']):
            basisTag = ET.Element('div')
            basisTag.text = basis
            if int(basis) < 0:
                basisTag.set("class", "basis"+basis+" label label-danger")
            elif int(basis) > 0:
                basisTag.set("class", "basis"+basis+" label label-warning")
            else:
                basisTag.set("class", "basis"+basis+" label label-success")
                
            basisCell.append(basisTag)
        row.append(basisCell)
        table.append(row)
    
    return table



def createSubscriptionTable(subscriptions,node):
    table = ET.Element("table")
    table.set("class", "table table-hover")
    table.set("id","latency_table")
    
    # headers 
    headers = createHeaders(headerSubscriptionTable)
    table.append(headers)

    # subscription rows
    for key in subscriptions:
        row = ET.Element("tr")
        row.set("data-toggle","collapse")
        # to make it uniq "node,key"
        row.set("data-target","#%s%s"%(node,key))
        if subscriptions[key]['type'] == 0:
            row.set("class","warning")
        else:
            row.set("class","info")
        row.set("style","cursor: pointer;")
        row.append(createCell(key))
        row.append(createCell(getTimeString(subscriptions[key]['time_update'])))
        row.append(createCell(to_TB(subscriptions[key]['bytes'])))
        tdProgress = createCell("")
        tdProgress.append(createProgressBar(to_3f(subscriptions[key]['percent_bytes']),True))
        row.append(tdProgress)
        row.append(createCell(getTimeString(subscriptions[key]['time_create'])))
        row.append(createCell(getTimeString(subscriptions[key]['ETA'])))
        table.append(row)
        
        # create dataset table
        div = ET.Element('div')
        div.set("id","%s%s"%(node,key))
        div.set("class","collapse")
        subTable = createDatasetTable(subscriptions[key]['dataset'])
        div.append(subTable)

        # container for dataset table
        row = ET.Element("tr")
        cell = createCell("")
        cell.set("colspan",str(len(headerSubscriptionTable)))
        cell.append(div)
        row.append(cell)
        table.append(row)
        
    return table


def panelSubsTable(nodes,node):
    div = ET.Element('div')
    div.set("id",node)
    div.set("class","panel-collapse collapse")
    
    subDiv = ET.Element('div')
    subDiv.set("class","panel-body")
    subDiv.append(createSubscriptionTable(nodes[node]['subscription'],node))
    
    div.append(subDiv)
    return div


def createNodePanelRow(nodes,node):
    divMain = ET.Element('div')
    divMain.set("class","panel panel-default")
        
    # panel row
    divPanel = ET.Element('div')
    divPanel.set("class","panel-heading")
    divPanel.set("style","background-color:#4A97DA;color:#fff;font-weight:bold;")

    values = [node, getTimeString(nodes[node]['time_update']), to_TB(nodes[node]['bytes']), createProgressBar(to_3f(nodes[node]['percent_bytes']),False), getTimeString(nodes[node]['time_create'])]
    nodeDiv = createNodePanelDiv(values, headerNodePanelColmd)

    nodeDiv.set("data-toggle","collapse")
    nodeDiv.set("data-target","#"+node)
    nodeDiv.set("data-parent","#node_parent")
    nodeDiv.set("class","row")
    nodeDiv.set("style","cursor: pointer;")

    divPanel.append(nodeDiv)
    divMain.append(divPanel)
    
    # panel subscription - shown on click
    divSubs = panelSubsTable(nodes,node)
    divMain.append(divSubs)
    
    return divMain


def createNodePanelDiv(values,colmds):
    rowDiv = ET.Element('div')
    rowDiv.set("class","row")
    for colmd,val in zip(colmds,values):
        colDiv = ET.Element('div')
        valStr = str(val)
        # progress bar div
        if valStr.startswith("<Element"):
            colDiv.set("class", "progress col-md-"+str(colmd))
            colDiv.set("style","padding-left:0px;padding-right:0px;margin-bottom:0px")
            colDiv.append(val)
        else:
            colDiv.set("class", "col-md-"+str(colmd))
            colDiv.text = valStr
        rowDiv.append(colDiv)
        
    return rowDiv


def createProgressBar(percent, isSubsBar):
    if isSubsBar:
        div = ET.Element('div')
        div.set("class", "progress")
        div.set("style","margin-bottom:0px")
    
    divBar = ET.Element('div')
    divBar.set("class","progress-bar progress-bar-success")
    divBar.set("style","width:"+percent+"%;")
    
    spanBar = ET.Element('span')
    spanBar.text = str(percent)
    divBar.append(spanBar)
    
    if isSubsBar:
        div.append(divBar)
        return div
    else:
        return divBar

def createLatencyTable(nodes):
    divMain = ET.Element('div')
    divMain.set("id","node_parent")
    divMain.set("class","container-fluid")
    
    # header
    divHeader = ET.Element('div')
    divHeader.set("class","row")
    
    for colmd,header in zip(headerNodePanelColmd,headerNodePanel):
        row = ET.Element('div')
        row.set("class", "col-md-"+str(colmd))
        row.text = str(header)
        divHeader.append(row)
        
    divMain.append(divHeader)
    
    # nodes
    for node in nodes:
        divPanelRow = createNodePanelRow(nodes,node)
        divMain.append(divPanelRow)
        
    return divMain




def createSuggestionPanel(table,text):
    divContainer = ET.Element("div")
    divContainer.set("class","panel panel-primary")    

    divHeading = ET.Element("div")
    divHeading.set("class","panel-heading")
    divHeading.text = text

    divContainer.append(divHeading)
    divContainer.append(table)

    return divContainer


def createSuggestionTable(nodes):
   
    mainDiv = ET.Element("div")

    suggestionTables = {}

    for node in nodes:
        suggestion = nodes[node]['suggestion']

        for problem in suggestion:
            # create table if not already
            if problem not in suggestionTables:
                suggestionTables[problem] = ET.Element("table")
                suggestionTables[problem].set("class", "table table-striped table-bordered table-condensed")
                # headers 
                headers = createHeaders(suggestionHeaders[problem])
                suggestionTables[problem].append(headers)
                
            for item in suggestion[problem]:
                row = ET.Element("tr")
                if problem == "-6" or problem == "-5":
                    row.append(createCell(item['lfn']))
                    row.append(createCell(item['origin_node']))
                    row.append(createCell(node))
                elif problem == "-2" or problem == "-1":
                    row.append(createCell(item['block']))
                    row.append(createCell(node))
                    
                suggestionTables[problem].append(row)


    # append each suggestion panel to main div
    for key in suggestionTables:
        mainDiv.append(createSuggestionPanel(suggestionTables[key], suggestionTexts[key]))
        
    return mainDiv

def appendTo(dict,key,val):
    list = dict.get(key)
    if not list:
        list = []
    list.append(val)
    dict[key] = list
    

def addBasisInfo(suggestion,problem,args):
    if problem == "-6" or problem == "-5":
        # get files without replica
        url = datasvcURL + 'missingfiles?block=%s&node=%s' % (args[0], args[1])
        resultBlockArrive = json.load(urllib.urlopen(url.replace("#","%23")))
        for block in resultBlockArrive['phedex']['block']:
            for file in block['file']:
                appendTo(suggestion,problem, {'lfn': file['name'], 'origin_node':file.get('origin_node','None')})
    elif problem == "-2" or problem == "-1":
        appendTo(suggestion,problem, {'block':args[0]})
        

def retriveInfoFromPhEDEx(nodeList):
    nodes = {}
    
    # init dictionary
    for node in nodeList:
        nodes[node] = {'subscription':{}, 'time_create':float("inf"), 'time_update':0, 'bytes':0, 'percent_bytes':0, 'suggestion':{}}
        
        
    for node in nodes:
        # get incomplete subscriptions
        url = datasvcURL + 'subscriptions?node=%s&create_since=0&percent_max=99.99999' % node
        resultSubs = json.load(urllib.urlopen(url))
        
        subscriptionList = nodes[node]['subscription']
        # each dataset should be returned only once by datasvc due to given specific node name
        for dataset in resultSubs['phedex']['dataset']:
            # safety check since some datasets don't have subscription attribute
            if 'subscription' not in dataset:
                continue
            
            # assuming that each dataset can be seen only in one incomplete subscription
            subscription = dataset['subscription'][0]
            subsKey = subscription['request']
            
            # init necessary fields for this subscription if it doesn't exist already
            if subsKey not in subscriptionList:
                subscriptionList[subsKey] = {'bytes':0,
                                             'percent_bytes': subscription['percent_bytes'],
                                             'time_create':subscription['time_create'], 
                                             'time_update':0,
                                             'ETA':0,
                                             'type': 0,
                                             'dataset':[]}
                
                # update node attributes with the subscription attributes
                nodes[node]['time_create'] = min(nodes[node]['time_create'], subscription['time_create'])
                nodes[node]['percent_bytes'] += subscription['percent_bytes']
                
                # transferrequests service to get the <comments>, if it contains "prestaging" set subscription type to 1
                # (Dave&Andrew said that they add "prestaing" string to comment to distinguish)
                try:
                    url = datasvcURL + 'transferrequests?request=%s&node=%s' % (subsKey, node)
                    resultRequest = json.load(urllib.urlopen(url))
                    subsComment = resultRequest['phedex']['request'][0]['requested_by']['comments']
            
                    if "prestaging" in str(subsComment).lower():
                        subscriptionList[subsKey]['type'] = 1
                except:
                    print >> sys.stderr, 'Failed to get comment for the subscription '+subsKey
            
            # will be init below
            datasetName = dataset['name']
            blockTimeUpdate = 0
            destETA = 0
            basis = []

                
            # blockarrive - get ETA and collect possible problems
            url = datasvcURL + 'blockarrive?dataset=%s&to_node=%s' % (datasetName, node)
            resultBlockArrive = json.load(urllib.urlopen(url))
            for block in resultBlockArrive['phedex']['block']:
                for destination in block['destination']:
                    # time_arrive, basis
                    destETA = max(destETA, destination['time_arrive'] if destination['time_arrive'] else float("inf"))
                    problem = str(destination['basis'])
                    if problem not in basis:
                        basis.append(problem)

                    # get more info&suggestion for problems - populate suggestion list which will be used to create Suggestion Table
                    addBasisInfo(nodes[node]['suggestion'],problem,[block['name'],node])

                        
            # blockreplica - get the latest transfer time to this node
            url = datasvcURL + 'blockreplicas?dataset=%s&node=%s' % (datasetName, node)
            resultBlockReplica = json.load(urllib.urlopen(url))
            for block in resultBlockReplica['phedex']['block']:
                for replica in block['replica']:
                    blockTimeUpdate = max(blockTimeUpdate, replica['time_update'])
                    
            # update node attributes with the dataset attributes
            nodes[node]['time_update'] = max(nodes[node]['time_update'], blockTimeUpdate)
            nodes[node]['bytes'] += dataset['bytes']
            
            # update the main dictionary with the collected info above
            subscriptionList[subsKey]['time_update'] = max(subscriptionList[subsKey]['time_update'], blockTimeUpdate)
            subscriptionList[subsKey]['ETA'] = max(subscriptionList[subsKey]['ETA'], destETA)
            subscriptionList[subsKey]['bytes'] += dataset['bytes']
            subscriptionList[subsKey]['dataset'].append({'name':datasetName, 
                                                         'bytes':dataset['bytes'],
                                                         'time_update':blockTimeUpdate, 
                                                         'ETA':destETA,
                                                         'basis':basis
                                                       })

        # get percent of bytes to show in the top-most panel view - total bytes percent of subs / number of subscriptions
        nodes[node]['percent_bytes'] /= len(nodes[node]['subscription']) if nodes[node]['subscription'] else 1

    return nodes


# get all disk nodes
diskNodeList=[]
url= datasvcURL + 'nodes?node=T1*_Disk'
resultNode = json.load(urllib.urlopen(url))
for node in resultNode['phedex']['node']:
    diskNodeList.append(node['name'])

# cern nodes
cernNodeList = ['T0_CH_CERN_MSS','T2_CH_CERN']

# get all necessary info from PhEDEx datasvc
nodes_t1disk = retriveInfoFromPhEDEx(diskNodeList)
nodes_cern = retriveInfoFromPhEDEx(cernNodeList) 

# get template files 
html = open(SRC_DIR+"tmpl/main.tmpl").read()
html_suggestion = open(SRC_DIR+"tmpl/suggestions.tmpl").read()

# output to file   
fp = open(os.path.join(OUTPUT_DIR, "index.html"), "w")
fp.write(html.format(
    date=time.strftime("%x %X"),
    latency_table_disk=minidom.parseString(ET.tostring(createLatencyTable(nodes_t1disk))).toprettyxml(),
    latency_table_cern=minidom.parseString(ET.tostring(createLatencyTable(nodes_cern))).toprettyxml()
))
fp.close()

fp = open(os.path.join(OUTPUT_DIR, "suggestions.html"), "w")
fp.write(html_suggestion.format(
    date=time.strftime("%x %X"),
    suggestion_table=minidom.parseString(ET.tostring(createSuggestionTable(dict(nodes_t1disk.items() + nodes_cern.items())))).toprettyxml()
))
fp.close()
