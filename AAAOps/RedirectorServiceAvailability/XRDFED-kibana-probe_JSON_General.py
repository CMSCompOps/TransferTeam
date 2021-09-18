#!/usr/bin/python3
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
#import Lemon.XMLAPI
import socket
import atexit
import threading
import tempfile
import json
import shutil
import multiprocessing
html_dir = '/var/www/html/aaa-probe/'   # will create per-service json files here
#Bockjoo Uncomment and comment a line below 
LOCKFILE='/var/lock/subsys/xrdfed-kibana-probe'
if 'ufhpc' in socket.gethostname() :
   LOCKFILE='/opt/TransferTeam/AAAOps/RedirectorServiceAvailability/var/lock/subsys/xrdfed-kibana-probe-general'
# Bockjoo Uncomment and comment a line below 
#probes_json='KIBANA_PROBES.json'
probes_json='KIBANA_PROBES_GENERAL.json'
timeout_sec = 10 * 60
class Alarm(Exception):
    pass
def alarm_handler(signum, frame):
    print ("ERROR: caught overall timeout after "+str(timeout_sec)+"s\n")
    clear_lock()
    sys.exit(2)
    raise Alarm
def clear_lock():
    try:
        os.unlink(LOCKFILE)      
    except Exception as e:
        print ("could not remove lockfile:"+str(e))
def env_setup():
    os.environ['X509_USER_CERT']='/root/.globus/slsprobe-cert.pem'
    os.environ['X509_USER_KEY']='/root/.globus/slsprobe-key.pem'
    os.environ['X509_USER_PROXY']='/root/.globus/slsprobe.proxy'
    if 'ufhpc' in socket.gethostname() : os.environ['X509_USER_PROXY']=os.environ['HOME']+'/.cmsuser.proxy'
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
    except Exception as e:
        print ("could not remove proxy file:"+str(e))
def try_lock():
    ret =  subprocess.call(['lockfile','-5','-r2',LOCKFILE])
    if ret > 0:
        print ("could not create lockfile")
        return False
    return True

def check_ping(hostname):
    with open(os.devnull, 'w') as DEVNULL:
        try:
            subprocess.check_call(
                ['ping', '-c', '3', hostname],
                stdout=DEVNULL,  # suppress output
                stderr=DEVNULL
            )
            is_up = True
        except subprocess.CalledProcessError:
            is_up = False
    return is_up

def prepare_dictionary(servicename,redirector):
    is_up = check_ping(redirector[:redirector.find(':')])
    dic={'service':servicename, 'host': redirector[:redirector.find(':')]}
    print(servicename," is up ",is_up)
    if is_up == False:
        dic['version'] = 'unavailable'
        dic['status'] = 'unavailable'
        dic['comment'] = "Unpingable host"
        dic["xrdcp_below_time"] = 0
        dic["xrdcp_above_time"] = 0
    else:
        # OLD (errtext,version,out) = xrd_info(redirector) 
        (errtext,version,out) = xrd_info(redirector,'version') # NEW
        if(errtext):
            dic['version'] = 'unavailable'
            dic['status'] = 'unavailable'
            errtext = errtext.replace("'", "")
            errtext = errtext.replace('"', '')
            dic['comment'] = "Error getting info from redirector: "+errtext
            dic["xrdcp_below_time"] = 0
            dic["xrdcp_above_time"] = 0
        else:
            dic['version'] = version
    return dic
def xrdcp_test(redirector,file):
    (errtext,out,err,elapsed) = run_xrd_commands("xrdcp",
                                                 ["-d","1",
                                                  "-f",
                                                  "-DIReadCacheSize","0",
                                                  "-DIRedirCntTimeout","180",
                                                  "root://"+redirector+'/'+file,
                                                  '/dev/null'],180)
    #print ("DEBUG xrd_test ",redirector," errtext ",errtext, " err ", err )
    return (errtext,err,elapsed)
def xrd_info(redirector,what):
    theargs = [redirector, "query", "config", what]
    if 'version' in what or 'role' in what : command = 'xrdfs'
    else :
       command = 'xrdmapc'
       theargs = [ '--list', 'all', redirector ]
    config_out = "unknown"
    count = 0
    count_limit = 3
    timelimit = 2
    if 'xrdmapc' in command :
       timelimit = 90
       count_limit = 1
    while (count < count_limit):
       (errtext,out,err,elapsed) = run_xrd_commands(command, theargs, timelimit) #"xrdfs",
                                                      #[redirector,
                                                      # "query","config", # 1:kXR_QStats
                                                      # what])         # a_ll stats
    
       if 'xrdmapc' in command :
          if out :
             errtext = err
             config_out = out
             break
       if err:
          #errtext = ''
          #config_out = 'error'
          config_out = err.replace(b'\n',b'').decode()
       else:
          #config_out=out
          #if 'xrdmapc' in command :
          #   break
          #else : 
          config_out = out.replace(b'\n',b'').decode()
          #   # to check if count matters config_out=config_out+'+'+str(count)
          if out.replace(b'\n',b'') : break
          time.sleep(1)
       count += 1
    #print ( 'DEBUG count = ',count,' config_out ',config_out, ' redirector ',redirector)
    if not 'xrdmapc' in command :
       if not config_out : config_out = 'timeout'
       if 'Auth failed' in config_out : config_out = 'Auth failed'
    return (errtext,config_out,out)

def run_xrd_commands(cmd,args,timelimit):
    dev_null = open('/dev/null', 'r')
    errtxt = ''
    elapsed = -1.0
    if 'xrdcp' in cmd :
       xrd_args = [ 'perl','-e',"alarm "+str(timelimit)+" ; exec @ARGV", cmd,   # one-line wrapper that *actually* kills the command
                    "-DIConnectTimeout","30",
                    "-DITransactionTimeout","60",
                    "-DIRequestTimeout","60" ] + args
    else :
       xrd_args = [ 'perl','-e',"alarm "+str(timelimit)+" ; exec @ARGV", cmd ] + args    


    #if 'xrdmapc' in cmd :
    #    xrd_args = [ cmd, ] + args    
    try:
        start = time.time()
        proc = subprocess.Popen(xrd_args,
                                stdin=dev_null,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        (out, err) = proc.communicate()
        ret = proc.returncode
        elapsed = (time.time() - start)
        #print ( ' out ',out )
        #if 'xrdmapc' in cmd : return ('',out,err,elapsed)
        err_redir_index = err.rfind(b'Received redirection to')
        err_index3010 = err.rfind(b'(error code: 3010')  # (permission denied) may be sort-of-OK - we are talking to final storage already - UK
        err_index3005 = err.rfind(b'(error code: 3005')  # (no user mapping) - INFN
        if err_redir_index >= 0 and (err_index3010 >= 0 or err_index3005 >= 0):
            #print ("errtxt will be empty because ",err)
            errtxt = ''
        else:    
            #print ("errtxt will not be empty because ret ",ret," err ",err)
            if(ret > 0):
               errtxt = "client-side error - exit code "+str(ret)+"\n"
            err_index = err.rfind(b'Last server error')
            if err_index >= 0:
               err_end_index=err.find(b"\n",err_index)
               errtxt = errtxt + err[err_index:err_end_index]
            #print ("errtxt will not be empty because ret ",ret," err_index ", err_index, " err ",err)
    except Exception as e :
        errtext = errtxt + "Exception: "+str(e)
        out = 'Try did not work :O'
        print(out)
    dev_null.close()
    
    return (errtxt,out,err,elapsed)

def test_redirector(dicci, servicename, redirector, file_below=None, file_above=None, extra_notes=""):
    servicename=servicename.upper()
    notes_text = "Redirector: "+redirector
    availability = 'Available'
    availinfo = ''
    c = ''
    if 'status' in dicci and dicci['status'] == 'unavailable':
        availability = dicci['status']
        #pass
    elif file_below == None and file_above == None:
        availability = 'Unavialable'
        c = 'Non-existing File Above and File Below.'
        dicci['xrdcp_below_time'] = 0
        dicci['xrdcp_below_time'] = 0
    else:
        if (file_below):
            notes_text = notes_text + "File below: " + file_below
            (err_below,dump_below,elapsed_below) = xrdcp_test(redirector, file_below)
            #print ("DEBUG FILE_BELOW Test redirector ",redirector," err_below ",err_below)
            if err_below:
                availability = 'Degraded'
                #availinfo=availinfo+" Error below redirector "+err_below
                dump_sane = re.sub(b'---*',b'__',dump_below)
                c = c+"Error for file BELOW: "+err_below+". Dumpsane: "+str(dump_sane.decode())+ '.'
                dicci['xrdcp_below_time'] = 0
            else:
                #availinfo=availinfo+" File below: OK "
                dicci['xrdcp_below_time'] = elapsed_below
        else:
            c = "Error for file BELOW: Non-existing File Below. "
            dicci['xrdcp_below_time'] = 0
        if(file_above):
            notes_text = notes_text + "File elsewhere: " + file_above
            (err_above,dump_above,elapsed_above) = xrdcp_test(redirector, file_above)
            #print ("DEBUG FILE_ABOVE Test redirector ",redirector," err_above ",err_above)
            if err_above :
                availability = 'Degraded'
                #availinfo=availinfo+" Error above redirector "+err_above
                dump_sane = re.sub(b'---*',b'__',dump_above)
                c = c+"Error for file ABOVE: "+err_above+". Dumpsane: "+str(dump_sane.decode())+'.'
                dicci['xrdcp_above_time'] = 0
            else:
                #availinfo = availinfo+" File above: OK "
                dicci['xrdcp_above_time'] = elapsed_above
        else:
            c = c + "Error for file ABOVE: Non-existing File Above."
            dicci['xrdcp_above_time'] = 0
    #availinfo = availinfo + " " + notes_text
    dicci['status']= str(availability)
    if c == '':
        c = 'N/A'
    c = c.replace("\n", "")
    c = c.replace("\r", "")
    dicci ['Comment'] = c
    with open(html_dir  + probes_json, 'a') as f:
        json.dump(dicci, f)
        f.write('\n')

def main():
    debug = 0
    if not 'ufhpc' in socket.gethostname():
       atexit.register(clear_lock)
    if len(sys.argv) > 1:
       if sys.argv[1] == '-d':
          debug=1
    if not 'ufhpc' in socket.gethostname():
       if not try_lock():
          sys.exit(1)
    if not os.path.exists(html_dir):
        os.makedirs(html_dir)
    env_setup()
    timeout_sec = 10 * 60  # limit overall runtime to 10min
    signal.signal(signal.SIGALRM, alarm_handler)
    ATLASLINK="%BR%Monitoring:%BR%\n http://atl-prod07.slac.stanford.edu:8080/display?page=xrd_report/aggregated/total_xrootd_lgn %BR%\n http://dashb-atlas-xrootd-transfers.cern.ch/ui %BR%\nhttp://dashb-atlas-ssb.cern.ch/dashboard/request.py/siteview#currentView=FAX+redirectors&highlight=false %BR%\n"
    CMSLINK="%BR%Monitoring:%BR%\n http://xrootd.t2.ucsd.edu/dashboard/ %BR%\n http://dashb-cms-xrootd-transfers.cern.ch/ui %BR%\n"
    FILEABOVE="/store/mc/SAM/GenericTTbar/AODSIM/CMSSW_9_2_6_91X_mcRun1_realistic_v2-v1/00000/A64CCCF2-5C76-E711-B359-0CC47A78A3F8.root"
    FILEBELOW="/store/mc/SAM/GenericTTbar/AODSIM/CMSSW_9_2_6_91X_mcRun1_realistic_v2-v1/00000/A64CCCF2-5C76-E711-B359-0CC47A78A3F8.root"    
    services = {
        "XRDFED_CMS-GLOBAL01":{'redirector':'cms-xrd-global01.cern.ch:1094',
                             'file_below': FILEABOVE,
                             'file_above': FILEBELOW,
                             'extra_notes':CMSLINK},
        "XRDFED_CMS-GLOBAL02":{'redirector':'cms-xrd-global02.cern.ch:1094',
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
        "XRDFED_CMS-EU-IPv6":{ 'redirector':'xrootd-cms-redir-int.cr.cnaf.infn.it:1094',
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
                         'extra_notes':CMSLINK}
	}
    signal.alarm(timeout_sec)
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
                test_redirector(** argus)        
            else:
                t = threading.Thread(target=test_redirector, kwargs = argus)  # read: "run a thread with the test function and all the parameters above as arguments"
                t.start()
                #t.join()
                #os.system('source ~/single_quotes.sh')
        #print(diccionaries)
    except Alarm:
        print ("ERROR: caught overall timeout after "+str(timeout_sec)+"s\n")
        clear_lock()
        sys.exit(2)
    print ("Check ",html_dir+probes_json)
    signal.alarm(0)
if __name__ == '__main__':
    for file in os.listdir(html_dir):
        if file == probes_json:
            os.remove(html_dir+probes_json)
            break
    #p = multiprocessing.Process(target=main)
    #p.start()
    #p.join(180)

    #if p.is_alive():
    #    print"killing process"
    #    os._exit(1)
        #p.terminate()
        #p.join()
    main()
