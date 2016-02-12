#!/usr/bin/env python

from sys import argv
from json import load

with open(argv[1]) as jsonFile:
  stuck = load(jsonFile)

for k,v in stuck.iteritems():
  if k.find('SIM')>=0 or k.find('GEN')>=0 or k.find('LHE')>=0:
    print k
