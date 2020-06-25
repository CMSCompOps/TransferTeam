import urllib.request as request
import urllib
import json
import requests
import os
import pandas
from pandas.io.json import json_normalize
from bs4 import BeautifulSoup as soup
import warnings
warnings.filterwarnings('ignore')

def file_read(fname):
        content_array = []
        with open(fname) as f:
                for line in f:
                        content_array.append(line)
                return content_array

def which_to_invalidate_in_dbs(fname):
    invalidate = []
    files = file_read(fname)
    for line_ in range(len(files)):
        os.system("xrdfs cms-xrd-global.cern.ch locate -d -m "+line_+" > aux.txt")
        sites = file_read("aux.txt")
        if sites[0] == "[FATAL] Redirect limit has been reached":
            invalidate.append(line_)
    return invalidate

def invalidate_in_dbs(list_of_files):
    
