'''
Created on Mar 27, 2013
Edited on Jan 26, 2017

@author: cassel
@edited: Jorge Diaz and David Urbina
@last_edited David Urbina

To add a new site, you must edit the {SITES} and {PLEDGES} variables.
If last week data does not exist for the site, it will be set to this week data
If PLEDGES value does not exist for the site, it will be set to 0
'''
import json
import sys
import os
import os.path
import re
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import argparse

from matplotlib.colors import colorConverter
from xml.etree import ElementTree as ET
from datetime import date

import utils

#relative path to the script of dumps directory
DUMP_DIR = "dumps"

# can be relative path to the script or absolute path
OUTPUT_ROOT = "/afs/cern.ch/work/c/cmstteam/www/storageoverview"
UNIT = 1000 ** 4 #TB

SITES = (
    "T0_CH_CERN_MSS",
    "T1_DE_KIT_MSS",
    "T1_ES_PIC_MSS",
    "T1_FR_CCIN2P3_MSS",
    "T1_IT_CNAF_MSS",
    "T1_RU_JINR_MSS",
    "T1_UK_RAL_MSS",
    "T1_US_FNAL_MSS",
    "T1_DE_KIT_Disk",
    "T1_ES_PIC_Disk",
    "T1_FR_CCIN2P3_Disk",
    "T1_IT_CNAF_Disk",
    "T1_RU_JINR_Disk",
    "T1_UK_RAL_Disk",
    "T1_US_FNAL_Disk",
    "T2_CH_CERN"
)
# TB
PLEDGES = {
    "T0_CH_CERN_MSS": 44000,
    "T1_DE_KIT_MSS": 10000,
    "T1_ES_PIC_MSS": 5100,
    "T1_FR_CCIN2P3_MSS": 8100,
    "T1_IT_CNAF_MSS": 12000,
    "T1_RU_JINR_MSS": 5000,
    "T1_UK_RAL_MSS": 8000,
    "T1_US_FNAL_MSS": 40000,
    "T1_DE_KIT_Disk": 3300,
    "T1_ES_PIC_Disk": 1683,
    "T1_FR_CCIN2P3_Disk": 2700,
    "T1_IT_CNAF_Disk": 3960,
    "T1_RU_JINR_Disk": 2800,# SE(2800TB) + cache for tapes(400TB)
    "T1_UK_RAL_Disk": 2640,
    "T1_US_FNAL_Disk": 13200,
    "T2_CH_CERN": 5370
}
T0CERNPLEDGE=44000
T0CERNUSED=31524.8*UNIT
# special condition for FNAL, total used by PhEDEx: (total[custodial]-0.5)*1.1
FNALTAPE="T1_US_FNAL_MSSjorge"
T1FNALMSSUSED=0

ERAS_DATA = (
    'GlobalMar08', 'CRUZET1', 'CRUZET2', 'CRUZET3', 'CRUZET4', 'EW35',
    'CRUZET09', 'CRAFT09', 'BeamCommissioning08', 'Commissioning08', 
    'BeamCommissioning09', 'Commissioning09', 'Commissioning10', 'Run2010A', 
    'Run2010B', 'HIRun2010', 'Commissioning11', 'Run2011A', 'Run2011B', 
    'HIRun2011', 'Commissioning12', 'Run2012A', 'Run2012B', 'Run2012C', 
    'Run2012D', 'PARun2012', 'HIRun2013', 'Run2013A' 
)

ERAS_MC = (
    'Summer08', 'Fall08', 'Winter09', 'Summer09', 'Spring10', 'Summer10', 
    'Fall10', 'Winter10', 'Spring11', 'Summer11', 'Fall11', 'Summer12', 
    'Summer12_DR53X', 'HiWinter13', 'Nov2011_HI', 'PreProd12_7TeV', 'Summer13',
    'Summer13dr53X','Fall13','HiFall13','UpgFall13','Fall13wmLHE','Fall13pLHE','HiFall11','CommissioningDisk',
    'LowPU2010','Spring14dr','SHCALUpg142023','Spring14miniaod','GEM2019Upg14','Muon2023Upg14' 
)

ERAS_OTHER = ("RelVal", "StoreResults", "CMSSW", "T0TEST", "HC", "SAM", 
    "h2tb2007", "Online", "JobRobot","IntegrationTest_130508"
)

MAPPING = {
    "T0TEST" : "TEST", 
    "TOTEST" : "TEST",
    "JobRobot" : "TEST",
    "HC" : "TEST",
    "SAM" : "TEST", 
    "CMSSW" : "RelVal"
}

URL = "https://cmsweb.cern.ch/phedex/datasvc/xml/prod/blockreplicas"

def to_TB(amount):
    return "%.3f" % (amount / float(UNIT),)    

def to_3f(amount):
    return "%.3f" % amount    

def to_whole_TB(amount):
    return int(round(amount / float(UNIT), 0))

def prepare_output_directory():
    """Prepare the output directory,
    create if it doesn't exist, what should be in the most cases.
    """
    
    if OUTPUT_ROOT.startswith("/"):
        output = OUTPUT_ROOT
    else:
        current_dir = os.path.dirname(os.path.realpath(__file__))
        output = os.path.join(current_dir, OUTPUT_ROOT)

    for subf in date.today().strftime("%Y %m %d").split():
        output = os.path.join(output, subf)
    try:
        os.makedirs(output)
        return output
    except OSError as ex:
        if ex.errno == os.errno.EACCES:
            print "Permission denied to create folder: %s" % output
            sys.exit(ex.errno)
        elif ex.errno == os.errno.EEXIST:
            print "%s directory already exists, will be overwritten" % output
            return output
        else:
            print "Unexpected error: %s" % ex
            sys.exit(ex.errno)
           
def get_output_root_directory():
    if OUTPUT_ROOT.startswith("/"):
        output = OUTPUT_ROOT
    else:
        current_dir = os.path.dirname(os.path.realpath(__file__))
        output = os.path.join(current_dir, OUTPUT_ROOT)
    return output

class SiteData(object):
    def __init__(self, name):
        self.name = name
        self.use_old = False
        self.data = {}
        self.last_week_data = {}
        self.current_week_data = {}
        
    def addinfo(self, era, erainfo, last_week=False):
        self.use_old = last_week
        self._select_source()
        if era not in self.data:
            self.data[era] = erainfo
        else:
            msg = "Something wrong with data dump, I should not be here"
            raise StandardError(msg)
        
    def get(self, era=None, tier=None, cust=None,
            last_week=False, eras_list=ERAS_DATA, delta=False):
        if delta:
            self.use_old = False
            current = self._get_number(era, tier, cust, eras_list)
            self.use_old = True
            old = self._get_number(era, tier, cust, eras_list)
            self.use_old = False
            return current - old
        else:
            self.use_old = last_week
            return self._get_number(era, tier, cust, eras_list)

    def get_eras_set(self, eras_list=ERAS_DATA):
        
        return set(self.data.keys()) & set(eras_list)
    
    def get_tiers_set(self, eras_list=ERAS_DATA):
        tiers = set()
        for era, erainfo in self.data.items():
            if era in eras_list:
                tiers |= set(erainfo.keys())
        return tiers

    def _select_source(self):
        if self.use_old:
            self.data = self.last_week_data
        else:
            self.data = self.current_week_data

    def _get_number(self, era=None, tier=None, cust=None, eras_list=None):
        self._select_source()
        result = 0
        if era or tier:
            if era and tier:
                try:
                    if cust != None:
                        result = self.data[era][tier][cust]
                    else:
                        result = sum(self.data[era][tier])
                except KeyError:
                    result = 0
            elif era:
                try:
                    for tier in self.data[era].values():
                        if cust != None:
                            result += tier[cust]
                        else:
                            result += sum(tier)
                except KeyError:
                    result = 0
            elif tier:
                try:
                    for era in self.data.values():
                        for t, info in era.items():
                            if t == tier:
                                if cust != None:
                                    result += info[cust]
                                else:
                                    result += sum(info)
                except KeyError:
                    result = 0 
        else:
            for era, erainfo in self.data.items():
                if era in eras_list:
                    for tier in erainfo.values():
                        if cust != None:
                            result += tier[cust]
                        else:
                            result += sum(tier)
            
        return result

class TableMaker(object):
    def __init__(self, data, output_dir):
        self.sites = data
        self.output_dir = output_dir

    def _add_phedex_totals(self, table):
        url = "https://cmsweb.cern.ch/phedex/datasvc/json/prod/nodeusage"
        interests = re.compile(r".*_node_bytes$")
        row = ET.Element("tr")
        row.append(self._create_cell("phedex"))
        
        grand_total = 0
        for site in self.sites:
            params = {"node":"{site}".format(site=site.name)}
            data = json.loads(utils.download_data(url, params))["phedex"]["node"][0]
            total = 0
            for key, value in data.items():
                if interests.match(key):
                    total += int(value)
                    grand_total += value
            row.append(self._create_cell(to_TB(total)))
        row.append(self._create_cell(to_TB(grand_total)))
        table.append(row)
            
    def summary(self, last_week=False, delta=False):
        table = self._create_table()
        row = ET.Element("tr")
        row.append(self._create_cell(""))
        self._add_site_names(table, row)

        self._collect(table, cust=True, last_week=last_week, eras_list=ERAS_DATA, replace=True, delta=delta)
        self._collect(table, cust=False, last_week=last_week, eras_list=ERAS_DATA, replace=True, delta=delta)
        self._collect(table, cust=True, last_week=last_week, eras_list=ERAS_MC, replace=True, delta=delta)
        self._collect(table, cust=False, last_week=last_week, eras_list=ERAS_MC, replace=True, delta=delta)
        self._collect(table, cust=True, last_week=last_week, eras_list=ERAS_OTHER, replace=True, delta=delta)
        self._collect(table, cust=False, last_week=last_week, eras_list=ERAS_OTHER, replace=True, delta=delta)
        self._add_totals(table)
        if not last_week and not delta:
            self._add_phedex_totals(table)
        return table
    
    def meetingSummary(self, isTape=False):
        table = self._create_table()
        row = ET.Element("tr")
        row.append(self._create_cell(""))
        
        # Site names
        #if isTape:
        #    row.append(self._create_cell("T0_CH_CERN", header=True))
        
        self._add_site_names(table, row)

        # Pledges
        row = ET.Element("tr")
        row.append(self._create_cell("Pledge for PhEDEx [TB]", header=True))
        
        
        total = 0
        #if isTape:
        #    row.append(self._create_cell(to_3f(T0CERNPLEDGE), color=True))
        #    total += T0CERNPLEDGE
            
        for site in self.sites:
            data = PLEDGES[site.name] if site.name in PLEDGES else 0
            total += data
            row.append(self._create_cell(to_3f(data), color=True))
            
        row.append(self._create_cell(to_3f(total), color=True))
        table.append(row)

        # Used (PhEDEx)
        url = "https://cmsweb.cern.ch/phedex/datasvc/json/prod/nodeusage"
        interests = re.compile(r".*_node_bytes$")
        row = ET.Element("tr")
        row.append(self._create_cell("Used (PhEDEx) [TB]", header=True))
        grand_total = 0
        
        #if isTape:
        #    row.append(self._create_cell(to_TB(T0CERNUSED)))
        #    grand_total += T0CERNUSED
        
        for site in self.sites:
            params = {"node":"{site}".format(site=site.name)}
            data = json.loads(utils.download_data(url, params))["phedex"]["node"][0]
            total = 0
            for key, value in data.items():
                if interests.match(key):
                    total += long(value)
                    
            if site.name == FNALTAPE:
                row.append(self._create_cell(to_TB(T1FNALMSSUSED)))
                grand_total += T1FNALMSSUSED
            else:
                row.append(self._create_cell(to_TB(total)))
                grand_total += total
                
        row.append(self._create_cell(to_TB(grand_total)))
        table.append(row)
        
	# Diff (PhEDEx)
        url = "https://cmsweb.cern.ch/phedex/datasvc/json/prod/nodeusage"
        interests = re.compile(r".*_node_bytes$")
        row = ET.Element("tr")
        row.append(self._create_cell("Difference [TB]", header=True))
        grand_total = 0
        
        #if isTape:
        #    row.append(self._create_cell(to_TB(T0CERNPLEDGE*UNIT - T0CERNUSED)))
        #    grand_total += T0CERNUSED
        
        for site in self.sites:
            params = {"node":"{site}".format(site=site.name)}
            pledgeSite = PLEDGES[site.name] if site.name in PLEDGES else 0
            data = json.loads(utils.download_data(url, params))["phedex"]["node"][0]
            total = 0
            for key, value in data.items():
                if interests.match(key):
                    total += long(value)
            total = pledgeSite*UNIT - total        
            if site.name == FNALTAPE:
                row.append(self._create_cell(to_TB(PLEDGES[FNALTAPE]*UNIT - T1FNALMSSUSED)))
                grand_total += T1FNALMSSUSED
            else:
                row.append(self._create_cell(to_TB(total)))
                grand_total += total
                
        row.append(self._create_cell(to_TB(grand_total)))
        table.append(row)        

        # Usable
        url = "https://cmsweb.cern.ch/phedex/datasvc/json/prod/nodeusage"
        interests = re.compile(r".*_node_bytes$")
        row = ET.Element("tr")
        row.append(self._create_cell("Usable [TB]", header=True))
        grand_total = 0
        
        #if isTape:
        #    row.append(self._create_cell(to_TB(T0CERNPLEDGE*UNIT - T0CERNUSED)))
        #    grand_total += T0CERNUSED
        
        for site in self.sites:
            params = {"node":"{site}".format(site=site.name)}
            pledgeSite = PLEDGES[site.name] if site.name in PLEDGES else 0
            data = json.loads(utils.download_data(url, params))["phedex"]["node"][0]
            total = 0
            for key, value in data.items():
                if interests.match(key):
                    total += long(value)
            total = pledgeSite*UNIT - total        
            '''
            if site.name == "T1_US_FNAL_MSS":
                row.append(self._create_cell(to_TB(0)))
            elif site.name == "T1_DE_KIT_MSS":
                row.append(self._create_cell(to_TB(0)))
                #row.append(self._create_cell(to_TB(PLEDGES[FNALTAPE]*UNIT - T1FNALMSSUSED)))
                #grand_total += T1FNALMSSUSED
            else:
                row.append(self._create_cell(to_TB(total)))
                grand_total += total
             '''
            row.append(self._create_cell(to_TB(total)))
            grand_total += total
        row.append(self._create_cell(to_TB(grand_total)))
        table.append(row)        

        return table
        
    def jsonSummary(self, isTape=False):
        jsonsummary = {}
        jsonsummary['Used'] = {}
        jsonsummary['Free'] = {}
        jsonsummary['Pledge'] = {}
        jsonsummary['Usable'] = {}
        url = "https://cmsweb.cern.ch/phedex/datasvc/json/prod/nodeusage"
        interests = re.compile(r".*_node_bytes$")
        # Site names
        #if isTape:
        #    jsonsummary['Pledge']["T0_CH_CERN_MSS"] = T0CERNPLEDGE
        #    jsonsummary['Used']['T0_CH_CERN_MSS'] = T0CERNUSED /UNIT
        #    jsonsummary['Free']['T0_CH_CERN_MSS'] = T0CERNPLEDGE - (T0CERNUSED /UNIT)
        for site in self.sites:
            jsonsummary['Pledge'][site.name] = PLEDGES[site.name] if site.name in PLEDGES else 0
            params = {"node":"{site}".format(site=site.name)}
            data = json.loads(utils.download_data(url, params))["phedex"]["node"][0]
            total = 0
            for key, value in data.items():
                if interests.match(key):
                    total += long(value)
            jsonsummary['Used'][site.name] = total/UNIT
            jsonsummary['Free'][site.name] = (PLEDGES[site.name]*UNIT - total)/UNIT
            if site.name == FNALTAPE:
                jsonsummary['Used'][site.name] = int( T1FNALMSSUSED /UNIT)
                jsonsummary['Free'][site.name] = int((PLEDGES[site.name]*UNIT - T1FNALMSSUSED)/UNIT)
       
        for site in jsonsummary['Free']:
            '''
            if (site == 'T1_US_FNAL_MSS' or site =='T1_DE_KIT_MSS'):
                jsonsummary['Usable'][site] = 0
            else:
                jsonsummary['Usable'][site]=jsonsummary['Free'][site]
            '''
            jsonsummary['Usable'][site]=jsonsummary['Free'][site] 
        return jsonsummary
    
    
    def _create_html(self, title, filename, func, **kwargs):
        html = """
<html>
<body>
    <h1>{title}</h1>
    {body}
</body>
</html>
"""     
        fp = open(os.path.join(self.output_dir, filename),"w")
        body = func(**kwargs)
        
        body = ET.tostring(body)
        fp.write(html.format(title=title, body=body))
        fp.close()
        
    def produce_htmls(self, storage):
        if storage.lower() == 'disk':
            type="disk"
            typeStr="Disk"
        else:
            type="tape"
            typeStr="Tape"
            
        self._create_html(
                title="Current Week " + typeStr + " Storage Overview", 
                filename=type + "_storage_overview_current.html", 
                func=self.summary, 
                last_week=False, 
                delta=False)
        
        self._create_html(
                title="Previous Week " + typeStr + " Storage Overview", 
                filename=type + "_storage_overview_previous.html", 
                func=self.summary, 
                last_week=True, 
                delta=False)
        
        self._create_html(
                title="Delta between Current and Previous Week " + typeStr + " Storage Overview", 
                filename=type + "_storage_overview_delta.html", 
                func=self.summary, 
                last_week=False, 
                delta=True)
        
        for site in self.sites:
            self._create_html(
                    title= typeStr + " Storage Overview {0}".format(site.name), 
                    filename=type + "_storage_overview_{0}.html".format(site.name), 
                    func=self._create_site_summary, 
                    site=site)
        
        self._create_html(
                title="Current Week " + typeStr + " Storage Overview: Detailed View for Data", 
                filename=type + "_storage_overview_current_data_detailed.html", 
                func=self._create_detailed, 
                eras_list=ERAS_DATA, 
                era="Acquisition era", 
                tier="Data Tier", 
                cust="Cust./Non-Cust.")
        
        self._create_html(
                title="Previous Week " + typeStr + " Storage Overview: Detailed View for Data", 
                filename=type + "_storage_overview_previous_data_detailed.html", 
                func=self._create_detailed, 
                eras_list=ERAS_DATA, 
                era="Acquisition era", 
                tier="Data Tier", 
                cust="Cust./Non-Cust.", 
                last_week=True)
        
        self._create_html(
                title="Delta Week " + typeStr + " Storage Overview: Detailed View for Data", 
                filename=type + "_storage_overview_delta_data_detailed.html", 
                func=self._create_detailed, 
                eras_list=ERAS_DATA, 
                era="Acquisition era", 
                tier="Data Tier", 
                cust="Cust./Non-Cust.", 
                delta=True)
        
        self._create_html(title="Current Week " + typeStr + " Storage Overview: Era/Tier View for Data", filename=type + "_storage_overview_current_data_era_tier.html", func=self._create_detailed, eras_list=ERAS_DATA, era="Acquisition era", tier="Data Tier")
        self._create_html(title="Previous Week " + typeStr + " Storage Overview: Era/Tier View for Data", filename=type + "_storage_overview_previous_data_era_tier.html", func=self._create_detailed, eras_list=ERAS_DATA, era="Acquisition era", tier="Data Tier", last_week=True)
        self._create_html(title="Delta Week " + typeStr + " Storage Overview: Era/Tier View for Data", filename=type + "_storage_overview_delta_data_era_tier.html", func=self._create_detailed, eras_list=ERAS_DATA, era="Acquisition era", tier="Data Tier", delta=True)

        self._create_html(title="Current Week " + typeStr + " Storage Overview: Era/Cust./Non-Cust. View for Data", filename=type + "_storage_overview_current_data_era_cust.html", func=self._create_detailed, eras_list=ERAS_DATA, era="Acquisition era", cust="Cust./Non-Cust.")
        self._create_html(title="Previous Week " + typeStr + " Storage Overview: Era/Cust./Non-Cust. View for Data", filename=type + "_storage_overview_previous_data_era_cust.html", func=self._create_detailed, eras_list=ERAS_DATA, era="Acquisition era", cust="Cust./Non-Cust.", last_week=True)
        self._create_html(title="Delta Week " + typeStr + " Storage Overview: Era/Cust./Non-Cust. View for Data", filename=type + "_storage_overview_delta_data_era_cust.html", func=self._create_detailed, eras_list=ERAS_DATA, era="Acquisition era", cust="Cust./Non-Cust.", delta=True)

        self._create_html(title="Current Week " + typeStr + " Storage Overview: Era View for Data", filename=type + "_storage_overview_current_data_era.html", func=self._create_detailed, eras_list=ERAS_DATA, era="Acquisition era")
        self._create_html(title="Previous Week " + typeStr + " Storage Overview: Era View for Data", filename=type + "_storage_overview_previous_data_era.html", func=self._create_detailed, eras_list=ERAS_DATA, era="Acquisition era", last_week=True)
        self._create_html(title="Delta Week " + typeStr + " Storage Overview: Era View for Data", filename=type + "_storage_overview_delta_data_era.html", func=self._create_detailed, eras_list=ERAS_DATA, era="Acquisition era", delta=True)

        self._create_html(title="Current Week " + typeStr + " Storage Overview: Era View for Custodial Data", filename=type + "_storage_overview_current_cust_data_era.html", func=self._create_detailed, eras_list=ERAS_DATA, era="Acquisition era", cust="Cust.", only_one_cust=True)
        self._create_html(title="Previous Week " + typeStr + " Storage Overview: Era View for Custodial Data", filename=type + "_storage_overview_previous_cust_data_era.html", func=self._create_detailed, eras_list=ERAS_DATA, era="Acquisition era", cust="Cust", only_one_cust=True, last_week=True)
        self._create_html(title="Delta Week " + typeStr + " Storage Overview: Era View for Custodial Data", filename=type + "_storage_overview_delta_cust_data_era.html", func=self._create_detailed, eras_list=ERAS_DATA, era="Acquisition era", cust="Cust", only_one_cust=True, delta=True)

        self._create_html(title="Current Week " + typeStr + " Storage Overview: Era View for Non-Custodial Data", filename=type + "_storage_overview_current_non_cust_data_era.html", func=self._create_detailed, eras_list=ERAS_DATA, era="Acquisition era", cust="Non-Cust.", only_one_cust=False)
        self._create_html(title="Previous Week " + typeStr + " Storage Overview: Era View for Non-Custodial Data", filename=type + "_storage_overview_previous_non_cust_data_era.html", func=self._create_detailed, eras_list=ERAS_DATA, era="Acquisition era", cust="Non-Cust.", only_one_cust=False, last_week=True)
        self._create_html(title="Delta Week " + typeStr + " Storage Overview: Era View for Non-Custodial Data", filename=type + "_storage_overview_delta_non_cust_data_era.html", func=self._create_detailed, eras_list=ERAS_DATA, era="Acquisition era", cust="Non-Cust.", only_one_cust=False, delta=True)

        self._create_html(title="Current Week " + typeStr + " Storage Overview: Tier View for Data", filename=type + "_storage_overview_current_data_tier.html", func=self._create_detailed, eras_list=ERAS_DATA, tier="Data Tier")
        self._create_html(title="Previous Week " + typeStr + " Storage Overview: Tier View for Data", filename=type + "_storage_overview_previous_data_tier.html", func=self._create_detailed, eras_list=ERAS_DATA, tier="Data Tier", last_week=True)
        self._create_html(title="Delta Week " + typeStr + " Storage Overview: Tier View for Data", filename=type + "_storage_overview_delta_data_tier.html", func=self._create_detailed, eras_list=ERAS_DATA, era="Data Tier", delta=True)

        self._create_html(title="Current Week " + typeStr + " Storage Overview: Tier View for Custodial Data", filename=type + "_storage_overview_current_cust_data_tier.html", func=self._create_detailed, eras_list=ERAS_DATA, tier="Data Tier", cust="Cust.", only_one_cust=True)
        self._create_html(title="Previous Week " + typeStr + " Storage Overview: Tier View for Custodial Data", filename=type + "_storage_overview_previous_cust_data_tier.html", func=self._create_detailed, eras_list=ERAS_DATA, tier="Data Tier", last_week=True, cust="Cust.", only_one_cust=True)
        self._create_html(title="Delta Week " + typeStr + " Storage Overview: Tier View for Custodial Data", filename=type + "_storage_overview_delta_cust_data_tier.html", func=self._create_detailed, eras_list=ERAS_DATA, era="Data Tier", delta=True, cust="Cust.", only_one_cust=True)

        self._create_html(title="Current Week " + typeStr + " Storage Overview: Tier View for Non-Custodial Data", filename=type + "_storage_overview_current_non_cust_data_tier.html", func=self._create_detailed, eras_list=ERAS_DATA, tier="Data Tier", cust="Cust.", only_one_cust=False)
        self._create_html(title="Previous Week " + typeStr + " Storage Overview: Tier View for Non-Custodial Data", filename=type + "_storage_overview_previous_non_cust_data_tier.html", func=self._create_detailed, eras_list=ERAS_DATA, tier="Data Tier", last_week=True, cust="Cust.", only_one_cust=False)
        self._create_html(title="Delta Week " + typeStr + " Storage Overview: Tier View for Non-Custodial Data", filename=type + "_storage_overview_delta_non_cust_data_tier.html", func=self._create_detailed, eras_list=ERAS_DATA, era="Data Tier", delta=True, cust="Cust.", only_one_cust=False)




        self._create_html(title="Current Week " + typeStr + " Storage Overview: Detailed View for MC", filename=type + "_storage_overview_current_mc_detailed.html", func=self._create_detailed, eras_list=ERAS_MC, era="Acquisition era", tier="Data Tier", cust="Cust./Non-Cust.")
        self._create_html(title="Previous Week " + typeStr + " Storage Overview: Detailed View for MC", filename=type + "_storage_overview_previous_mc_detailed.html", func=self._create_detailed, eras_list=ERAS_MC, era="Acquisition era", tier="Data Tier", cust="Cust./Non-Cust.", last_week=True)
        self._create_html(title="Delta Week " + typeStr + " Storage Overview: Detailed View for MC", filename=type + "_storage_overview_delta_mc_detailed.html", func=self._create_detailed, eras_list=ERAS_MC, era="Acquisition era", tier="Data Tier", cust="Cust./Non-Cust.", delta=True)
        
        self._create_html(title="Current Week " + typeStr + " Storage Overview: Era/Tier View for MC", filename=type + "_storage_overview_current_mc_era_tier.html", func=self._create_detailed, eras_list=ERAS_MC, era="Acquisition era", tier="Data Tier")
        self._create_html(title="Previous Week " + typeStr + " Storage Overview: Era/Tier View for MC", filename=type + "_storage_overview_previous_mc_era_tier.html", func=self._create_detailed, eras_list=ERAS_MC, era="Acquisition era", tier="Data Tier", last_week=True)
        self._create_html(title="Delta Week " + typeStr + " Storage Overview: Era/Tier View for MC", filename=type + "_storage_overview_delta_mc_era_tier.html", func=self._create_detailed, eras_list=ERAS_MC, era="Acquisition era", tier="Data Tier", delta=True)

        self._create_html(title="Current Week " + typeStr + " Storage Overview: Era/Cust./Non-Cust. View for MC", filename=type + "_storage_overview_current_mc_era_cust.html", func=self._create_detailed, eras_list=ERAS_MC, era="Acquisition era", cust="Cust./Non-Cust.")
        self._create_html(title="Previous Week " + typeStr + " Storage Overview: Era/Cust./Non-Cust. View for MC", filename=type + "_storage_overview_previous_mc_era_cust.html", func=self._create_detailed, eras_list=ERAS_MC, era="Acquisition era", cust="Cust./Non-Cust.", last_week=True)
        self._create_html(title="Delta Week " + typeStr + " Storage Overview: Era/Cust./Non-Cust. View for MC", filename=type + "_storage_overview_delta_mc_era_cust.html", func=self._create_detailed, eras_list=ERAS_MC, era="Acquisition era", cust="Cust./Non-Cust.", delta=True)

        self._create_html(title="Current Week " + typeStr + " Storage Overview: Era View for MC", filename=type + "_storage_overview_current_mc_era.html", func=self._create_detailed, eras_list=ERAS_MC, era="Acquisition era")
        self._create_html(title="Previous Week " + typeStr + " Storage Overview: Era View for MC", filename=type + "_storage_overview_previous_mc_era.html", func=self._create_detailed, eras_list=ERAS_MC, era="Acquisition era", last_week=True)
        self._create_html(title="Delta Week " + typeStr + " Storage Overview: Era View for MC", filename=type + "_storage_overview_delta_mc_era.html", func=self._create_detailed, eras_list=ERAS_MC, era="Acquisition era", delta=True)

        self._create_html(title="Current Week " + typeStr + " Storage Overview: Era View for Custodial MC", filename=type + "_storage_overview_current_cust_mc_era.html", func=self._create_detailed, eras_list=ERAS_MC, era="Acquisition era", cust="Cust.", only_one_cust=True)
        self._create_html(title="Previous Week " + typeStr + " Storage Overview: Era View for Custodial MC", filename=type + "_storage_overview_previous_cust_mc_era.html", func=self._create_detailed, eras_list=ERAS_MC, era="Acquisition era", cust="Cust", only_one_cust=True, last_week=True)
        self._create_html(title="Delta Week " + typeStr + " Storage Overview: Era View for Custodial MC", filename=type + "_storage_overview_delta_cust_mc_era.html", func=self._create_detailed, eras_list=ERAS_MC, era="Acquisition era", cust="Cust", only_one_cust=True, delta=True)

        self._create_html(title="Current Week " + typeStr + " Storage Overview: Era View for Non-Custodial MC", filename=type + "_storage_overview_current_non_cust_mc_era.html", func=self._create_detailed, eras_list=ERAS_MC, era="Acquisition era", cust="Non-Cust.", only_one_cust=False)
        self._create_html(title="Previous Week " + typeStr + " Storage Overview: Era View for Non-Custodial MC", filename=type + "_storage_overview_previous_non_cust_mc_era.html", func=self._create_detailed, eras_list=ERAS_MC, era="Acquisition era", cust="Non-Cust.", only_one_cust=False, last_week=True)
        self._create_html(title="Delta Week " + typeStr + " Storage Overview: Era View for Non-Custodial MC", filename=type + "_storage_overview_delta_non_cust_mc_era.html", func=self._create_detailed, eras_list=ERAS_MC, era="Acquisition era", cust="Non-Cust.", only_one_cust=False, delta=True)

        self._create_html(title="Current Week " + typeStr + " Storage Overview: Tier View for MC", filename=type + "_storage_overview_current_mc_tier.html", func=self._create_detailed, eras_list=ERAS_MC, tier="Data Tier")
        self._create_html(title="Previous Week " + typeStr + " Storage Overview: Tier View for MC", filename=type + "_storage_overview_previous_mc_tier.html", func=self._create_detailed, eras_list=ERAS_MC, tier="Data Tier", last_week=True)
        self._create_html(title="Delta Week " + typeStr + " Storage Overview: Tier View for MC", filename=type + "_storage_overview_delta_mc_tier.html", func=self._create_detailed, eras_list=ERAS_MC, era="Data Tier", delta=True)

        self._create_html(title="Current Week " + typeStr + " Storage Overview: Tier View for Custodial MC", filename=type + "_storage_overview_current_cust_mc_tier.html", func=self._create_detailed, eras_list=ERAS_MC, tier="Data Tier", cust="Cust.", only_one_cust=True)
        self._create_html(title="Previous Week " + typeStr + " Storage Overview: Tier View for Custodial MC", filename=type + "_storage_overview_previous_cust_mc_tier.html", func=self._create_detailed, eras_list=ERAS_MC, tier="Data Tier", last_week=True, cust="Cust.", only_one_cust=True)
        self._create_html(title="Delta Week " + typeStr + " Storage Overview: Tier View for Custodial MC", filename=type + "_storage_overview_delta_cust_mc_tier.html", func=self._create_detailed, eras_list=ERAS_MC, era="Data Tier", delta=True, cust="Cust.", only_one_cust=True)

        self._create_html(title="Current Week " + typeStr + " Storage Overview: Tier View for Non-Custodial MC", filename=type + "_storage_overview_current_non_cust_mc_tier.html", func=self._create_detailed, eras_list=ERAS_MC, tier="Data Tier", cust="Cust.", only_one_cust=False)
        self._create_html(title="Previous Week " + typeStr + " Storage Overview: Tier View for Non-Custodial MC", filename=type + "_storage_overview_previous_non_cust_mc_tier.html", func=self._create_detailed, eras_list=ERAS_MC, tier="Data Tier", last_week=True, cust="Cust.", only_one_cust=False)
        self._create_html(title="Delta Week " + typeStr + " Storage Overview: Tier View for Non-Custodial MC", filename=type + "_storage_overview_delta_non_cust_mc_tier.html", func=self._create_detailed, eras_list=ERAS_MC, era="Data Tier", delta=True, cust="Cust.", only_one_cust=False)



        self._create_html(title="Current Week " + typeStr + " Storage Overview: Detailed View for other", filename=type + "_storage_overview_current_other_detailed.html", func=self._create_detailed, eras_list=ERAS_OTHER, era="Acquisition era", tier="Data Tier", cust="Cust./Non-Cust.")
        self._create_html(title="Previous Week " + typeStr + " Storage Overview: Detailed View for other", filename=type + "_storage_overview_previous_other_detailed.html", func=self._create_detailed, eras_list=ERAS_OTHER, era="Acquisition era", tier="Data Tier", cust="Cust./Non-Cust.", last_week=True)
        self._create_html(title="Delta Week " + typeStr + " Storage Overview: Detailed View for other", filename=type + "_storage_overview_delta_other_detailed.html", func=self._create_detailed, eras_list=ERAS_OTHER, era="Acquisition era", tier="Data Tier", cust="Cust./Non-Cust.", delta=True)


    def _create_site_summary(self, site=None):
        table = self._create_table()
        row = ET.Element("tr")
        row.append(self._create_cell("Overview for: %s" % site.name, header=True))
        headings = ("Custodial Delta [TB]", 
                    "Custodial Total [TB]", 
                    "Non-Custodial Delta [TB]", 
                    "Non-Custodial Total [TB]",
                    "Total Delta [TB]",
                    "Total Total [TB]")
        for heading in headings:
            cell = self._create_cell(heading, header=True) 
            row.append(cell)
        table.append(row)
        
        
        totals = [0, 0, 0, 0, 0, 0]
        for eras_list in (ERAS_DATA, ERAS_MC, ERAS_OTHER):
            row = ET.Element("tr")
            if eras_list == ERAS_DATA:
                row.append(self._create_cell("Data"))
            elif eras_list == ERAS_MC:
                row.append(self._create_cell("MC"))
            else:
                row.append(self._create_cell("Other"))
            amount = site.get(eras_list=eras_list, cust=True, delta=True)
            totals[0] += amount
            row.append(self._create_cell(to_TB(amount)))
            amount = site.get(eras_list=eras_list, cust=True)
            
            totals[1] += amount
            
            
            row.append(self._create_cell(to_TB(amount)))
            amount = site.get(cust=False, delta=True, eras_list=eras_list)
            
            totals[2] += amount
            
            
            row.append(self._create_cell(to_TB(amount)))
            amount = site.get(cust=False, eras_list=eras_list)
            
            totals[3] += amount
            
            row.append(self._create_cell(to_TB(amount)))
            amount = site.get(delta=True, eras_list=eras_list)
            
            totals[4] += amount
            row.append(self._create_cell(to_TB(amount)))
            amount = site.get(eras_list=eras_list)
            totals[5] += amount

            row.append(self._create_cell(to_TB(amount)))
            table.append(row)

        row = ET.Element("tr")
        row.append(self._create_cell("Total"))
        for item in totals:
            row.append(self._create_cell(to_TB(item)))
        table.append(row)
        
        # special condition for FNAL, total used by PhEDEx: (total[custodial]-0.5)*1.1
        if site.name == FNALTAPE:
            global T1FNALMSSUSED
            T1FNALMSSUSED = (totals[1] - 0.5*UNIT) * 1.1
            
        return table

    def _create_table(self):
        table = ET.Element("table")
        table.set("border", "1")
        table.set("cellspacing", "0")
        table.set("cellpadding", "2")
        table.set("bordercolor", "#e2e2e2")
        return table

    def _create_cell(self, data, header=False, color=False):
        
        if header:
            font = ET.Element("font")
            font.set("color", "#ffffff")
            font.text =  "%s" % (data,)
            cell = ET.Element("th")
            cell.set("bgcolor", "#687684")
            cell.append(font)
        else:
            cell = ET.Element("td")
            if color:
                cell.set("bgcolor", "#edf4f9")
            
            cell.text = "%s" % (data,)
                
        return cell

    def _collect(self, table, era=None, tier=None, cust=None, 
                 last_week=False, eras_list=ERAS_DATA, replace=False, delta=False):
        
        row = ET.Element("tr")
        if era != None:
            row.append(self._create_cell(era))
        if tier != None:
            row.append(self._create_cell(tier))
        if cust != None:
            tag = "cust." if cust else "non-cust."
            if replace:
                if eras_list == ERAS_DATA:
                    tag = "%s data" % tag
                elif eras_list == ERAS_MC:
                    tag = "%s mc" % tag 
                else:
                    tag = "%s other" % tag
            row.append(self._create_cell(tag))
                                
        total = 0
        for site in self.sites:
            data = site.get(era=era, tier=tier, cust=cust, last_week=last_week, eras_list=eras_list, delta=delta)
            site.temp_total += data
            total += data
            row.append(self._create_cell(to_TB(data)))
        row.append(self._create_cell(to_TB(total)))
        if total > 0:
            table.append(row)

    def _add_headers(self, row, **kwargs):
        if "era" in kwargs:
            row.append(self._create_cell(kwargs["era"], header=True))
            
        if "tier" in kwargs:
            row.append(self._create_cell(kwargs["tier"], header=True))

        if "cust" in kwargs:
            row.append(self._create_cell(kwargs["cust"], header=True))

    def _add_totals(self, table, **kwargs):
        row = ET.Element("tr")
        row.append(self._create_cell("TOTAL"))
        i=1
        if "only_one_cust" in kwargs:
            i = 2
        for x in range(len(kwargs)-i):
            row.append(self._create_cell(""))
        grand_total = 0
        
        for site in self.sites:
            total = site.temp_total
            grand_total += total
            row.append(self._create_cell(to_TB(total)))
        row.append(self._create_cell(to_TB(grand_total)))
        table.append(row)

    def _add_site_names(self, table, row=None):
        if row is None:
            row = ET.Element("tr")
        for site in self.sites:
            row.append(self._create_cell(site.name, header=True))
            site.temp_total = 0
        row.append(self._create_cell("All sites", header=True))
        table.append(row)

    def _create_detailed(self, eras_list, last_week=False, delta=False, **kwargs):
        table = self._create_table()
        row = ET.Element("tr")
        self._add_headers(row, **kwargs)
        eras = set()
        
        if "era" in kwargs:
            for site in self.sites:
                eras |= site.get_eras_set(eras_list)
                
        tiers = set()
        if "tier" in kwargs:
            for site in self.sites:
                tiers |= site.get_tiers_set(eras_list)
        
        custs = set()
        if "cust" in kwargs:
            if "only_one_cust" in kwargs:
                custs = (kwargs["only_one_cust"],)
            else:
                custs = (True, False)
        
        self._add_site_names(table, row)
        
        if eras:
            for era in sorted(eras):
                if tiers:
                    for tier in sorted(tiers):
                        if custs:
                            for cust in custs:
                                self._collect(table, era=era, tier=tier, cust=cust, last_week=last_week, eras_list=eras_list, delta=delta)
                        else:
                            self._collect(table, era=era, tier=tier, last_week=last_week, eras_list=eras_list, delta=delta)
                elif custs:
                    for cust in custs:
                        self._collect(table, era=era, cust=cust, last_week=last_week, eras_list=eras_list, delta=delta)
                else:
                    self._collect(table, era=era, last_week=last_week, eras_list=eras_list, delta=delta)
        elif tiers:
            for tier in tiers:
                if custs:
                    for cust in custs:
                        self._collect(table, tier=tier, cust=cust, last_week=last_week, eras_list=eras_list, delta=delta)
                else:
                    self._collect(table, tier=tier, last_week=last_week, eras_list=eras_list, delta=delta)
                    
        self._add_totals(table, **kwargs)
        
        return table

class PlotMaker(object):
    def __init__(self, data):
        self.sites = data
        self.colors = [colorConverter.to_rgba(c) for c in ('r','g','m','c','y','b','k')]
        self.labels = [s.name for s in self.sites]

    def calculate_stack_offsets(self, previous,current,positive,negative):
        result = []
        for item in range(len(current)):
            result.append(0)

        for item in range(len(previous)):
            if previous[item] < 0:
                negative[item] = negative[item] + previous[item]
            else :
                positive[item] = positive[item] + previous[item]
            if current[item] < 0:
                result[item] = negative[item]
            else :
                result[item] = positive[item]

        return (result,positive,negative)


    def create_bar_plot(self, filename, title, labels, legends, data):
        plt.figure(figsize=(16,6),dpi=300)

        N = len(labels)
        ind = np.arange(N)+.5 
        width = 0.5

        plots = []
        left_edge = []
        left_edge_negative = []
        left_edge_positive = []
        for index in range(N):
            left_edge.append(0.)
            left_edge_negative.append(0.)
            left_edge_positive.append(0.)
        plots.append(plt.barh(ind, map(to_whole_TB, data[0]), width, color=self.colors[0], align='center', left=left_edge))
        for index in range(len(legends)-1):
            (left_edge,left_edge_positive,left_edge_negative) = self.calculate_stack_offsets(map(to_whole_TB, data[index]),map(to_whole_TB, data[index+1]),left_edge_positive,left_edge_negative)
            plots.append(plt.barh(ind, map(to_whole_TB, data[index+1]), width, color=self.colors[(index+1)%7], align='center', left=left_edge))

        fontsize = 20
        plt.title(title,fontsize=fontsize)
        plt.yticks(ind, labels)
        plt.xlabel('TB',fontsize=fontsize)
        plt.legend( [ plot[0] for plot in plots], legends, loc='center left', bbox_to_anchor=(1.05, .5) )
        plt.grid(True)
        ax = plt.gca()
        ax.get_xaxis().get_major_formatter().set_useOffset(False)
        ax.get_xaxis().get_major_formatter().set_scientific(False)
        for tick in ax.xaxis.get_major_ticks():
            tick.label1.set_fontsize(fontsize)
        for tick in ax.yaxis.get_major_ticks():
            tick.label1.set_fontsize(fontsize)
        leg = ax.get_legend()
        ltext  = leg.get_texts()
        plt.setp(ltext, fontsize=fontsize)

        plt.subplots_adjust(left=.2,right=0.75)

        plt.savefig(filename,format='png')
        plt.close()


    def create_overview_bar(self, title, filename, delta=False):
        
        data = []
        for site in self.sites:
            data.append([
                    site.get(cust=True, eras_list=ERAS_DATA, delta=delta),
                    site.get(cust=False, eras_list=ERAS_DATA, delta=delta),
                    site.get(cust=True, eras_list=ERAS_MC, delta=delta),
                    site.get(cust=False, eras_list=ERAS_MC, delta=delta),    
            ])

        types = [ 'custodial data', 'non-custodial data', 'custodial MC', 'non-custodial MC' ]

        self.create_bar_plot(
                    filename.replace('.png','_by_type.png'),
                    title,
                    types,
                    self.labels,
                    data
        )
        
        data = []
        
        data.append([site.get(cust=True, eras_list=ERAS_DATA, delta=delta) for site in self.sites])
        data.append([site.get(cust=False, eras_list=ERAS_DATA, delta=delta) for site in self.sites])
        data.append([site.get(cust=True, eras_list=ERAS_MC, delta=delta) for site in self.sites])
        data.append([site.get(cust=False, eras_list=ERAS_MC, delta=delta) for site in self.sites])
        
        self.create_bar_plot(
                    filename.replace(".png", "_by_site.png"), 
                    title, 
                    self.labels, 
                    types, 
                    data
        )
        
    def create_overview_pie(self, mode, title, filename):
        plt.figure(figsize=(10,7.5), dpi=300)
        plt.axes([0.15, 0., 0.7, 0.933])
        data = []
        for site in self.sites:
            if mode == 'data' :
                data.append(site.get(cust=True, eras_list=ERAS_DATA))
            elif mode == 'mc' :
                data.append(site.get(cust=True, eras_list=ERAS_MC))
            else :
                _data = site.get(cust=True, eras_list=ERAS_DATA)
                _mc = site.get(cust=True, eras_list=ERAS_MC)
                data.append(_data + _mc)

        fontsize = 25
        myPie = plt.pie(
                    data, 
                    labels=self.labels, 
                    autopct='%1.f%%', 
                    shadow=False, 
                    colors=self.colors)
        for x in myPie[2]:
            x.set_color('w')
            x.set_fontsize(fontsize)
        for x in myPie[1]:
            x.set_fontsize(fontsize-5)
        plt.title(title, fontsize=fontsize+5)
        plt.savefig(filename,format='png')
        plt.close()

def apply_mapping(era):
    for item in MAPPING.keys():
        if era.startswith(item):
            return MAPPING[item]
    return era

def xml_reader(filename, nodename):
    """
    Return xml file reader, which iterates through xml file returning
    replica information in tuple (node, blockname, size, custodiality) 
    one by one
    """
    nodename = "{0}".format(nodename)
    name = None
    counter = 0
    context = ET.iterparse(filename, events=("start", "end"))
    context = iter(context)
    event, root = context.next()
    for event, element in context:
        if event == "end":
            continue
        if element.tag == "block":
            name = element.get("name")
            continue
        if element.tag == "replica" and element.get("node") != nodename:
            continue

        sizebytes, node, cust = element.get("bytes"), element.get("node"), element.get("custodial")
        if not name or not bytes or not node or not cust:
            continue
        if name.count("/") != 3:
            continue

        counter += 1
        yield node, name, int(sizebytes), cust

        root.clear()

def get_era(dataset):
    # @todo: check for RelVal in the full name 
    era_part = dataset.split("/")[2]
    for eras_tuple in (ERAS_DATA, ERAS_MC, ERAS_OTHER):
        for era in sorted(eras_tuple, key=lambda x: len(x), reverse=True):
            if era_part.startswith(era):
                return apply_mapping(era)
                
    print "POSSIBLY NEW ERA: ", era_part.split("-")[0], dataset
    return "GENERIC"

def get_tier(dataset):
    return dataset.split("/")[-1]

def create_data_dump():
    dump = {}
    for sitename in SITES:
        params = {"node":"{0}".format(sitename)}
        fd = utils.download_file(URL, params)
        stats = {}
        
        reader = xml_reader(fd, sitename)
        for block in reader:
            dataset = block[1].split("#")[0]
            era = get_era(dataset)
            cust = 1 if block[3] == "y" else 0     
            ind = 0 + cust
            if era not in stats:
                stats[era] = {}
            tier = get_tier(dataset)
            if tier not in stats[era]:
                stats[era][tier] = [0,0] # bytes, cust bytes 
            try:
                stats[era][tier][ind] += block[2]
            except IndexError:
                print "ERROR: ", block
        dump[sitename] = stats
    return dump
        
def create_main_html(tables_tape,tables_disk, sites_tape, sites_disk, output_dir):
    html = open("main_page.tmpl").read()
    
    column_tape = ""  
    for site in sites_tape:
        column_tape += '<a href="tape_storage_overview_'+site.name+'.html">' + site.name + '</a> ' 


    column_disk = ""  
    for site in sites_disk:
        column_disk += '<a href="disk_storage_overview_'+site.name+'.html">' + site.name + '</a> '

    fp = open(os.path.join(output_dir, "main.html"), "w")
    fp.write(html.format(
                title='Storage Overview',
                title_tape='Tape Storage Overview',
                title_disk='Disk Storage Overview',
                date=date.today(),
                summary_tape=ET.tostring(tables_tape.summary()),
                delta_summary_tape=ET.tostring(tables_tape.summary(delta=True)),
                summary_disk=ET.tostring(tables_disk.summary()),
                delta_summary_disk=ET.tostring(tables_disk.summary(delta=True)),
                column_tape=column_tape,
                column_disk=column_disk, 
                fulldate=date.today()
                )) 

    fp.close()
    
def create_meeting_html(tables_tape,tables_disk, output_dir, output_root_dir):
    html = open("meeting_page.tmpl").read()
    

    fp = open(os.path.join(output_dir, "meeting.html"), "w")
    fp.write(html.format(
                title='Storage Overview',
                date=date.today(),
                tape_usage=ET.tostring(tables_tape.meetingSummary(isTape=True)),
                disk_usage=ET.tostring(tables_disk.meetingSummary(isTape=False))
                )) 

    fp.close()

def create_json_file(tables_tape,tables_disk, output_dir, output_root_dir):
    jsonTotal = {}
    jsonTotal['Disk'] = tables_disk.jsonSummary(isTape=False)
    jsonTotal['Tape'] = tables_tape.jsonSummary(isTape=True)
    fp = open(os.path.join(output_dir, "StorageOverview.json"), "w")
    fp.write(json.dumps(jsonTotal))
    fp.close()

def parse_args():
    """Parse and return provided arguments if any"""
    parser = argparse.ArgumentParser()
    parser.add_argument('last_week', nargs='?', 
            help='name of the last week dump',
            metavar=('last_week_dump',))
    parser.add_argument('current_week_dump', nargs='?', 
            help='name of the current week dump',
            metavar=('current_week_dump',))
    args = parser.parse_args()
    return args
        
def main():
    args = parse_args()
    dump_name = None
    last_week_dump = None
    if args.last_week:
        last_week_dump = args.last_week
    if args.current_week_dump:
        dump_name = args.current_week_dump

    if not last_week_dump:
        stat = lambda path: os.stat(os.path.join(DUMP_DIR, path))
        sort_func = lambda path: stat(path).st_mtime
        latest_dump = sorted(os.listdir(DUMP_DIR), key=sort_func)[-1]
        last_week_dump = os.path.join(DUMP_DIR, latest_dump)
        print last_week_dump

    output_dir = prepare_output_directory()
    output_root_dir = get_output_root_directory();
    
    year, month, day = date.today().strftime("%Y %m %d").split()

    if dump_name:
        dump = json.load(open(dump_name))
    else:
        dump = create_data_dump()
        dump_name = "dump_{0}_{1}_{2}.json".format(year, month, day)
        json.dump(dump, open(os.path.join(DUMP_DIR, dump_name), "w"))

    dump_old = json.load(open(last_week_dump))
    
    sites_tape = []
    sites_disk = []
    for sitename in SITES:
        site = SiteData(sitename)
        for era, erainfo in dump[site.name].items():
            site.addinfo(era, erainfo)
        # last week data exists for this site
        if site.name in dump_old:
            for era, erainfo in dump_old[site.name].items():
                site.addinfo(era, erainfo, True)
        # site is added newly, set this week's data also as last week data
        else:
            for era, erainfo in dump[site.name].items():
                site.addinfo(era, erainfo, True)
            
        if sitename.lower().endswith("_disk") or sitename.upper() == 'T2_CH_CERN':
            sites_disk.append(site)
        elif sitename.lower().endswith("_mss") or sitename.upper() == 'T0_CH_CERN':
            sites_tape.append(site)
        else:
            print 'ERROR: Unknown site name, please check: %s' % sitename
    
    
    tables_tape = TableMaker(sites_tape, output_dir)
    tables_disk = TableMaker(sites_disk, output_dir)
    
    # Output for tapes
    tables_tape.produce_htmls('tape')
    #====== Dependent on matplotlib 2.0 (needs python 2.7 to run)=========== 
    plots = PlotMaker(sites_tape)
    total_name = os.path.join(output_dir, 'total_tape_storage_overview.png')
    delta_name = os.path.join(output_dir, 'delta_tape_storage_overview.png')
    plots.create_overview_bar('Total Tape Storage Overview', total_name)
    plots.create_overview_bar('Delta Tape Storage Overview', delta_name, delta=True)

    pie = os.path.join(output_dir, 'custodial_tape_storage_pie.png')
    plots.create_overview_pie('','Custodial Tape Storage Overview',pie)
    pie = os.path.join(output_dir, 'custodial_data_tape_storage_pie.png')
    plots.create_overview_pie('data','Custodial Data Tape Storage Overview', pie)
    pie = os.path.join(output_dir, 'custodial_mc_tape_storage_pie.png')
    plots.create_overview_pie('mc','Custodial MC Tape Storage Overview', pie)
    #=======================================================================

    # Output for disks
    tables_disk.produce_htmls('disk')
    #====== Dependent on matplotlib 2.0 (needs python 2.7 to run)=========== 
    plots = PlotMaker(sites_disk)
    total_name = os.path.join(output_dir, 'total_disk_storage_overview.png')
    delta_name = os.path.join(output_dir, 'delta_disk_storage_overview.png')
    plots.create_overview_bar('Total Disk Storage Overview', total_name)
    plots.create_overview_bar('Delta Disk Storage Overview', delta_name, delta=True)
    #=======================================================================
    
    # Create main.html and meeting.html
    create_main_html(tables_tape, tables_disk, sites_tape, sites_disk, output_dir)
    create_meeting_html(tables_tape, tables_disk, output_dir, output_root_dir)

    #Create Json
    create_json_file(tables_tape, tables_disk, output_dir, output_root_dir)

    #create the soft link for the folder
    linkPath = output_root_dir+"/latest";
    if os.path.islink(linkPath):
        os.unlink(linkPath)
        
    os.symlink(output_dir, linkPath)

if __name__ == '__main__':
    # change current working directory to the path
    # where python executable actually is
    os.chdir(os.path.dirname(os.path.realpath(__file__)))
    main()
