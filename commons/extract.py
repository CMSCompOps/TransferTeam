#! /usr/bin/env python 
import sys 
import xml.etree.ElementTree as ET 
from bz2 import BZ2File 
#tree = ET.parse(BZ2File(sys.argv[1])) 
tree = ET.parse(sys.argv[1])
for entry in tree.getiterator('entry'): 
    print entry.get('name')
