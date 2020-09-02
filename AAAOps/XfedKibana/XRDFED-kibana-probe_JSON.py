#!/usr/bin/python
# functional probe and SLS extractor for the "federation" xroot services
# highlights:
# - stateless (i.e. run from cron whenever needed)
# - will try to prevent parallel runs via lockfile
# - multithreaded, one thread per service to be tested
# - overall runtime cap at 10min
# - could extract some statistics from xroot directly, but these are ever-increasing counters
# Problems:
# - need to update the code whenever a service is addded/deleted/changed
# - uses "random" files on various Xroot services all over the world, these are (for now) the same as used by the experiments but these might change..

import xml.dom.minidom 
import subprocess
import os
import sys
import signal
import re
import time
import Lemon.XMLAPI
import socket
import atexit
import threading
import tempfile
import json
import shutil

html_dir = '/root/ogarzonm/'   # will create per-service json files here

LOCKFILE='/var/lock/subsys/xrdfed-kibana-probe'

class Alarm(Exception):
    pass

def alarm_handler(signum, frame):
    print "ERROR: caught overall timeout after "+str(timeout_sec)+"s\n"
    clear_lock()
    sys.exit(2)
    raise Alarm

def clear_lock():
    try:
        os.unlink(LOCKFILE)      
    except Exception,e:
        print "could not remove lockfile:"+str(e)

def env_setup():
    os.environ['X509_USER_CERT']='/root/.globus/slsprobe-cert.pem'
    os.environ['X509_USER_KEY']='/root/.globus/slsprobe-key.pem'
    os.environ['X509_USER_PROXY']='/root/.globus/slsprobe.proxy'
    os.environ['KRB5CCNAME']='FILE:/dev/null'
    os.environ['PATH']=os.environ['PATH']+":/opt/globus/bin/"

def get_proxy():
    dev_null = open('/dev/null', 'rw')
    (proxyfd,proxy)=tempfile.mkstemp(prefix='x509_xrdfed_',suffix='.pem')
    os.close(proxyfd)
    os.environ['X509_USER_PROXY']=proxy
    ret =  subprocess.call(['grid-proxy-init','-pwstdin'],stdin=dev_null,)  
    if ret > 0:
        raise Exception("Cannot get X509 proxy")
    dev_null.close()
    
def cleanup_proxy():
    try:
        os.unlink(os.environ['X509_USER_PROXY'])
    except Exception,e:
        print "could not remove proxy file:"+str(e)

def try_lock():
    ret =  subprocess.call(['lockfile','-5','-r2',LOCKFILE])
    if ret > 0:
        print "could not create lockfile"
        return False
    return True

def prepare_dictionary(servicename,redirector):
    (errtext,version,out) = xrd_info(redirector)
    dic={'service':servicename, 'version': version, 'host': redirector[:redirector.find(':')]}
    if(errtext):
        dic['status'] = 'unavailable'
        dic['availinfo'] = " Error getting info from redirector: "+err_info
        dic["xrdcp_below_time"] = 0
        dic["xrdcp_above_time"] = 0
    return dic

def dnsalias_to_nodes(redirector):
    (host,port) = redirector.split(':')
    all_hosts = []
    data=socket.getaddrinfo(host,port,0, 0, socket.SOL_TCP )
    for addr in data:
        (family, socktype, proto, canonname, sockaddr) = addr
        (hostname, aliaslist, ipaddrlist) = socket.gethostbyaddr(sockaddr[0])
        if not hostname in all_hosts:
            all_hosts.append(hostname)
    return all_hosts

def xrdcp_test(redirector,file):
    (errtext,out,err,elapsed) = run_xrd_commands("xrdcp",
                                                 ["-d","1",
                                                  "-f",
                                                  "-DIReadCacheSize","0",
                                                  "-DIRedirCntTimeout","180",
                                                  "root://"+redirector+'/'+file,
                                                  '/dev/null'])
    return (errtext,err,elapsed)

def xrd_info(redirector):
    version = "(unknown)"
    (errtext,out,err,elapsed) = run_xrd_commands("xrdfs",
                                                      [redirector,
                                                       "query","config", # 1:kXR_QStats
                                                       "version"])         # a_ll stats

    if not out:
        errtext = ''
        os.system("xrdfs "+ redirector+" query config version > /root/aux.txt")
        os.system("head -n 1 /root/aux.txt > /root/aux2.txt")
        f = open('/root/aux2.txt', 'r')
        version = f.read()
        if not version:
            version = "(unknown)"
        else:
            version = version[:-1]
    else:
        if not errtext:
            try:
                dom = xml.dom.minidom.parseString(out)
                root_node = dom.documentElement
                if root_node.tagName == 'statistics':
                    v_attr = root_node.getAttributeNode('ver')
                    version = v_attr.nodeValue
            except Exception,e:
                errtext = "ERROR: cannot parse answer:"+str(e)
    return (errtext,version,out)

def run_xrd_commands(cmd,args):
    dev_null = open('/dev/null', 'r')
    errtxt = ''
    elapsed = -1.0
    xrd_args = [ 'perl','-e',"alarm 180; exec @ARGV", cmd,   # one-line wrapper that *actually* kills the command
                 "-DIConnectTimeout","30",
                 "-DITransactionTimeout","60",
                 "-DIRequestTimeout","60" ] + args
    err = ''
    out = ''
    try:
        ran_try = True
        start = time.time()
        proc = subprocess.Popen(xrd_args,
                                stdin=dev_null,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        (out, err) = proc.communicate()
	
        ret = proc.returncode
        elapsed = (time.time() - start)
        err_redir_index = err.rfind('Received redirection to')
        err_index3010 = err.rfind('(error code: 3010')  # (permission denied) may be sort-of-OK - we are talking to final storage already - UK
        err_index3005 = err.rfind('(error code: 3005')  # (no user mapping) - INFN
        if err_redir_index >= 0 and (err_index3010 >= 0 or err_index3005 >= 0):
            errtxt = ''
        else:    
            if(ret > 0):
                errtxt = "client-side error - exit code "+str(ret)+"\n"
            err_index = err.rfind('Last server error')
            if err_index >= 0:
                err_end_index=err.find("\n",err_index)
                errtxt = errtxt + err[err_index:err_end_index]
    except Exception,e:
        errtext = errtxt + "Exception: "+str(e)
    dev_null.close()
    return (errtxt,out,err,elapsed)
                     
def test_redirector(dicci, servicename, redirector, file_below=None, file_above=None, extra_notes=""):
    servicename=servicename.upper()
    notes_text = "Redirector:"+redirector
    availability = 'available'
    availinfo = ''
    c = 'No comment'

    # prepare the dictionary.
    #dicci['host'] = redirector.split(':')[0]

    # run the functional tests - first some simple check to get the version, if OK look for files
    #(err_info,version,dump_info) = xrd_info(redirector)
    #if(err_info):
    #    
    #    availability = 'unavailable'
    #    availinfo=availinfo+" Error getting info from redirector "+err_info
    #    dicci["xrdcp_below_time"] = 0
        #dicci["status"] = "unavailable"
    if 'status' in dicci and dicci['status'] == 'unavailable':
        pass
    else:
        if (file_below):
            notes_text = notes_text + "File 'below': " + file_below
            (err_below,dump_below,elapsed_below) = xrdcp_test(redirector, file_below)
            if err_below:
                availability = 'degraded'
                availinfo=availinfo+" Error below redirector "+err_below
                dump_sane = re.sub('---*','__',dump_below)
                c = "Detailed output for file BELOW "+redirector+":"+file_below+" "+err_below+" "+dump_sane
                #dicci['comment'] = c
            else:
                availinfo=availinfo+" File below: OK "
                dicci['xrdcp_below_time'] = str(elapsed_below)
        else:
            availinfo=availinfo+" File below: not tested." 
        if(file_above):
            notes_text = notes_text + "File 'elsewhere': " + file_above 
            (err_above,dump_above,elapsed_above) = xrdcp_test(redirector, file_above)
            if err_above :
                #We've changed availability from number to string so this below won't work; Marian commented out on 2015-11-06
                #availability = availability * 0.8  # less important if some remote site is failing..
                availinfo=availinfo+" Error above redirector "+err_above
                # sanitize the raw output in order to not trigger XML errors.. in a comment.
                dump_sane = re.sub('---*','__',dump_above)
                c = "Detailed output for file ABOVE "+redirector+":"+file_above+" "+err_above+" "+dump_sane
                #dicci = {**dicci, **{'comment': c}}
                #serviceUpdate.appendChild(c)
                #need_xml_link=1
            else:
                availinfo = availinfo+" File above: OK "
            #nValue = doc.createElement("numericvalue")
            #nValue.setAttribute("name", "xrdcp_above_time")
            #nValue.setAttribute("desc", "Time to copy a file elsewhere in the federation")
            #nValue.appendChild(doc.createTextNode(str(elapsed_above)))
            dicci['xrdcp_above_time'] = str(elapsed_above)
            #data.appendChild(nValue)
        else:
            availinfo = availinfo+" File above: not tested."

    # save functional test info to XML
    #if need_xml_link:
     #   myhostname = socket.gethostname()
      #  notes_text = notes_text + "Details for failed test: http://" + myhostname + "/aaa-probe/" + servicename + ".xml <br />\n" + "Details for recently failed test : http://vocms039.cern.ch/aaa-probe/err/ <br />\n" 
    availinfo = availinfo + " " + notes_text
    dicci['status']= str(availability)
    if availability == 'unavailable' or availability == 'degraded':
        dicci ['availInfo'] = availinfo
        dicci ['Comment'] = c
    #return dicci
    #dicci['availabilityinfo']=availinfo
    with open(html_dir  +'KIBANA_PROBES.json', 'a') as f:
        json.dump(dicci, f)
        f.write('\n')
    

def main():
    debug = 0
    atexit.register(clear_lock)
    if len(sys.argv) > 1:
	if sys.argv[1] == '-d':
        	debug=1
    if not try_lock():
        sys.exit(1)
    if not os.path.exists(html_dir):
        os.makedirs(html_dir)
    env_setup()
    # get a proxy cert
    # get_proxy()  

    timeout_sec = 10 * 60  # limit overall runtime to 10min
    signal.signal(signal.SIGALRM, alarm_handler)

    ATLASLINK="%BR%Monitoring:%BR%\n http://atl-prod07.slac.stanford.edu:8080/display?page=xrd_report/aggregated/total_xrootd_lgn %BR%\n http://dashb-atlas-xrootd-transfers.cern.ch/ui %BR%\nhttp://dashb-atlas-ssb.cern.ch/dashboard/request.py/siteview#currentView=FAX+redirectors&highlight=false %BR%\n"
    CMSLINK="%BR%Monitoring:%BR%\n http://xrootd.t2.ucsd.edu/dashboard/ %BR%\n http://dashb-cms-xrootd-transfers.cern.ch/ui %BR%\n"
    FILEABOVE="/store/mc/SAM/GenericTTbar/AODSIM/CMSSW_9_2_6_91X_mcRun1_realistic_v2-v1/00000/A64CCCF2-5C76-E711-B359-0CC47A78A3F8.root"
    FILEBELOW="/store/mc/SAM/GenericTTbar/AODSIM/CMSSW_9_2_6_91X_mcRun1_realistic_v2-v1/00000/A64CCCF2-5C76-E711-B359-0CC47A78A3F8.root"    

    services = {
        "XRDFED_CMS-GLOBAL01-NEW":{'redirector':'cms-xrd-global01.cern.ch:1094',
                             'file_below': FILEABOVE,
                             'file_above': FILEBELOW,
                             'extra_notes':CMSLINK},
	
	"XRDFED_CMS-GLOBAL02-NEW":{'redirector':'cms-xrd-global02.cern.ch:1094',
                             'file_below': FILEABOVE,
                             'file_above': FILEBELOW,
                             'extra_notes':CMSLINK},

        "XRDFED_CMS-US-FNAL":{'redirector':'cmsxrootd2.fnal.gov:1094',
                         'file_below': FILEABOVE,
                         'file_above': FILEBELOW,
                         'extra_notes':CMSLINK},

	"XRDFED_CMS-US-UNL":{'redirector':'xrootd.unl.edu:1094',
                         'file_below': FILEABOVE,
                         'file_above': FILEBELOW,
                         'extra_notes':CMSLINK},

        "XRDFED_CMS-EU-BARI":{'redirector':'xrootd.ba.infn.it:1094',
                          'file_below': FILEBELOW,
                          'file_above': FILEABOVE,
                          'extra_notes':CMSLINK},
         
	"XRDFED_CMS-EU-LLR":{'redirector':'llrxrd-redir.in2p3.fr:1094',
                          'file_below': FILEBELOW,
                          'file_above': FILEABOVE,
                          'extra_notes':CMSLINK},
         
	"XRDFED_CMS-EU-PISA":{'redirector':'xrootd-redic.pi.infn.it:1094',
                          'file_below': FILEBELOW,
                          'file_above': FILEABOVE,
                          'extra_notes':CMSLINK},

        "XRDFED_CMS-GLOBAL":{'redirector':'cms-xrd-global.cern.ch:1094',
                             'file_below': FILEABOVE,
                             'file_above': FILEBELOW,
                             'extra_notes':CMSLINK},

        "XRDFED_CMS-US":{'redirector':'cmsxrootd.fnal.gov:1094',
                         'file_below': FILEABOVE,
                         'file_above': FILEBELOW,
                         'extra_notes':CMSLINK},

        "XRDFED_CMS-EU":{'redirector':'xrootd-cms.infn.it:1094',
                         'file_below': FILEBELOW,
                         'file_above': FILEABOVE,
                         'extra_notes':CMSLINK},
	
	"XRDFED_CMS-EU-IPv6":{ 'redirector':'xrootd-cms-redir-01.cr.cnaf.infn.it:1094',
                         	'file_below': FILEBELOW,
                         	'file_above': FILEABOVE,
                         	'extra_notes':CMSLINK},	
	"XRDFED_CMS-TRANSIT":{'redirector':'cms-xrd-transit.cern.ch:1094',
                         'file_below': FILEBELOW,
                         'file_above': FILEABOVE,
                         'extra_notes':CMSLINK},
	
	"XRDFED_CMS-TRANSIT01":{'redirector':'vocms031.cern.ch:1094',
                         'file_below': FILEBELOW,
                         'file_above': FILEABOVE,
                         'extra_notes':CMSLINK},

	"XRDFED_CMS-TRANSIT02":{'redirector':'vocms032.cern.ch:1094',
                         'file_below': FILEBELOW,
                         'file_above': FILEABOVE,
                         'extra_notes':CMSLINK},

	}
    signal.alarm(timeout_sec)
    #shutil.copyfile(html_dir+'KIBANA_PROBES.json', html_dir+'KIBANA_PROBES_2.json')    
    os.remove(html_dir+'KIBANA_PROBES.json')
    #shutil.copyfile(html_dir+'KIBANA_PROBES.json', html_dir+'KIBANA_PROBES_2.json')
    try:
        diccionaries = []
        for xrd in services:
            services[xrd].update(servicename=xrd)
            servicename = xrd
            dicci = prepare_dictionary(servicename, services[xrd]['redirector'])
            diccionaries.append(dicci)
        for dicci in diccionaries:
            service = dicci['service']
            argus = services[service]
            argus['dicci'] = dicci
            if debug:
                test_redirector(** services[xrd])        
            else:
                t = threading.Thread(target=test_redirector, kwargs = argus)  # read: "run a thread with the test function and all the parameters above as arguments"
                t.start()
    except Alarm:
        print "ERROR: caught overall timeout after "+str(timeout_sec)+"s\n"
        clear_lock()
        sys.exit(2)
    signal.alarm(0)
    #shutil.copyfile(html_dir+'KIBANA_PROBES.json', html_dir+'KIBANA_PROBES_2.json')  
    # not cleaning up the proxy files (are shared via the ENV, and we don't want an extra thread to just remove that file, or wait for the individual tests to finish...

if __name__ == '__main__':
    main()
