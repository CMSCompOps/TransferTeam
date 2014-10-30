#!/usr/bin/env python

import sys,getopt,urllib,os,time,re
from xml.etree import ElementTree as ET
from xml.dom import minidom

try:
    import json
except ImportError:
    import simplejson as json

def help():
    print "input    : input file with lfn per line"
    print "error    : error regex"
    print "output   : output html file (without extension)" 


SRC_DIR = os.path.abspath(os.path.dirname(__file__)) + "/"
OUT_DIR = '/afs/cern.ch/user/m/mtaze/work/www/dashboard/'

instance='prod'
inputFile = None
errorRegex = None
outputFile = None
headerCorruptTable = ['Source','Destination','LFN','Errors']
try:
    opts, args = getopt.getopt(sys.argv[1:], "", ["input=","error=","output="])
except getopt.GetoptError:
    print  >> sys.stderr, 'Failed to parse options'
    sys.exit(2)

# check command line parameter
for opt, arg in opts :
    if opt == "--input" :
        inputFile = arg
    if opt == "--output":
        outputFile = arg
    elif opt == "--error" :
        errorRegex = arg

def createLink(text,href):
    link = ET.Element('a')
    link.set("href",str(href))
    link.text = str(text)
    return link

def createCell(data, header=False):
    if header:
        cell = ET.Element("th")
    else:
        cell = ET.Element("td")
    cell.text = str(data)
    return cell


def initErrorTable(tableContent):
    table = ET.Element("table")
    table.set("class", "table table-striped")
    table.set("id","corrupt_file_table")

    # headers 
    row = ET.Element("tr")
    for thText in headerCorruptTable:
        row.append(createCell(thText, True))
    table.append(row)

    # content
    for trText in tableContent:
        row = ET.Element("tr")
        row.append(createCell(trText['src']))
        row.append(createCell(trText['dest']))
        row.append(createCell(trText['lfn']))

        errorLink = "https://cmsweb.cern.ch/phedex/%s/Activity::ErrorInfo?fileid=%s;tofilter=%s;fromfilter=%s" % (instance, trText['file_id'], trText['dest'], trText['src'])
        errorCell = createCell("")
        errorCell.append(createLink("errors",errorLink))
        row.append(errorCell)

        table.append(row)

    return table

def checkResultForError(result):
    for link in result['phedex']['link']:
        src = link.get('from', '')
        dest = link.get('to','')
        for block in link['block']:
            for file in block['file']:
                if errorRegex == None:
                    tableContent.append({'src':src,'dest':dest,'lfn':file['name'],'file_id':file['id']})
                    return
                else:
                    for error in file['transfer_error']:
                        if error['detail_log']['$t'] and re.search(r""+errorRegex,error['detail_log']['$t']):
                            tableContent.append({'src':src,'dest':dest,'lfn':file['name'],'file_id':file['id']})
                            return
                        

def getResults(retries):
    if retries == 0:
        return None
    try:
        url='https://cmsweb.cern.ch/phedex/datasvc/json/%s/errorlog?lfn=%s' % (instance,lfn)
        result = json.load(urllib.urlopen(url))
        return result
    except:
        return getResults(retries-1)

tableContent = []
with open(inputFile, 'r') if inputFile != None else sys.stdin as file:
    for line in file:
        lfn = line.rstrip()
        result = getResults(3);
        if result:
            checkResultForError(result) 
            
html = open(SRC_DIR+"tmpl/"+outputFile+".tmpl").read()
fp = open(os.path.join(OUT_DIR, outputFile+".html"), "w")
fp.write(html.format(
    date=time.strftime("%x %X"),
    error_table=minidom.parseString(ET.tostring(initErrorTable(tableContent))).toprettyxml(),
))
fp.close()
