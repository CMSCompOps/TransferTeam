#!/usr/bin/env python
import csv
import sys
import operator
import itertools
import xml.etree.cElementTree as ET
import xml.dom.minidom as minidom

try:
    lfnlist=open(sys.argv[1])
except:
    print "Please provide lfn list file as argument"
    sys.exit(1)

try:
    reader = csv.reader(lfnlist)
    values = list(reader)
finally:
    lfnlist.close()

root = None
root = ET.Element("data", version="2.0")
dbs = ET.SubElement(root,"dbs",name="https://cmsweb.cern.ch/dbs/prod/global/DBSReader",dls="dbs")

values.sort(key = operator.itemgetter(0,1))

for key, items in itertools.groupby(values, operator.itemgetter(0)):
        dataset = ET.SubElement(dbs,"dataset", name=key)
        dataset.set("is-open","y")
        for key2, items2 in itertools.groupby(items, operator.itemgetter(1)):    
                block = ET.SubElement(dataset,"block", name=key2)
                block.set("is-open", "n")                
                for subitem in items2:
                        file = ET.SubElement(block,"file",name=subitem[2],bytes=subitem[3],checksum=subitem[4]+","+subitem[5])

outfile = open(sys.argv[1]+'.xml', 'w')
outfile.writelines(minidom.parseString(ET.tostring(root)).toprettyxml(indent = "    "))
outfile.close()
