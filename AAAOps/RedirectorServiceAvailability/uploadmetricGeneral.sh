#!/bin/bash

#notifytowhom=cms-comp-ops-transfer-team@cernNOSPAMPLEASE.ch,bockjoo@gmailNOSPAMPLEASE.com
notifytowhom=bockjoo__AT__gmail__dot__com
notifytowhom=$(echo $notifytowhom | sed 's#__AT__#@#' | sed 's#__dot__#\.#')
GRAFANA_PAGE="https://monit-grafana.cern.ch/d/serviceAvailability/overview-service-availability?orgId=11&var-category=All&from=now-24h&to=now-15m%2Fm"

DATE=$(date)
echo $DATE
echo "ExecutingScript"

cd /opt/TransferTeam/AAAOps/RedirectorServiceAvailability
[ -d logs ] || mkdir -p logs
logs=logs
thelog=$(pwd)/logs/uploadmetricGeneral.log

# General script
date
echo INFO sending the previous /var/www/html/aaa-probe/KIBANA_PROBES_GENERAL.json so that we can have a regular 15th minute entry for Grafana
python3 send_metrics.py > $logs/XRDFED_send.log 2>&1
echo INFO content of logs/XRDFED_send.log
cat $logs/XRDFED_send.log
date

echo INFO executing XRDFED-kibana-probe_JSON_General.py 
python3 XRDFED-kibana-probe_JSON_General.py > $logs/XRDFED_probe_json.log 2>&1
status=$?
if [ $status -ne 0 ] ; then
	printf "$(/bin/hostname -s) $(basename $0) We have a problem in running python3 XRDFED-kibana-probe_JSON_General.py\n\n$logs/XRDFED_probe_json.log:\n$(cat $logs/XRDFED_probe_json.log | sed 's#%#%%#g')\n" | mail -s "ERROR $(/bin/hostname -s) $(basename $0)" $notifytowhom
fi
rdirs=$(grep redirector $logs/XRDFED_probe_json.log | awk '{print $3}')
rdirs_degraded=
for r in $rdirs ; do
    grep redirector $logs/XRDFED_probe_json.log | grep "$r" | grep -q Available # Degraded # Available
    if [ $? -ne 0 ] ; then
       #grep redirector $logs/XRDFED_probe_json.log | grep "$r" | grep -q Degraded # Available # Degraded
       #if [ $? -eq 0 ] ; then
          rdir_degraded=$(grep redirector $logs/XRDFED_probe_json.log | grep "$r" | awk '{print $(NF-1)"+"$NF}')
          rdirs_degraded="$rdirs_degraded ${r}+$rdir_degraded"
       #else
       #3fi
    fi
done
if [ "x$rdirs_degraded" != "x" ] ; then
   printf "$(/bin/hostname -s) $(basename $0) We have one or more degraded redirectors\n\n$logs/XRDFED_probe_json.log:\n$(cat $logs/XRDFED_probe_json.log | sed 's#%#%%#g')\nTry this:\nperl -e \"alarm 180 ; exec @ARGV\" xrdcp -d 1 -f -DIReadCacheSize 0 -DIRedirCntTimeout 180 -DIConnectTimeout 30 -DITransactionTimeout 60 -DIRequestTimeout 60 root://rdir//store/mc/SAM/GenericTTbar/AODSIM/CMSSW_9_2_6_91X_mcRun1_realistic_v2-v1/00000/A64CCCF2-5C76-E711-B359-0CC47A78A3F8.root /dev/null\n" | mail -s "ERROR $(/bin/hostname -s) $(basename $0)" $notifytowhom
fi

echo INFO $logs/XRDFED_probe_json.log
cat $logs/XRDFED_probe_json.log
date
echo INFO running send_metrics.py
python3 send_metrics.py > $logs/XRDFED_send.log 2>&1
echo INFO content of logs/XRDFED_send.log
cat $logs/XRDFED_send.log
date
echo INFO Done

if [ -f $thelog ] ; then
   a=1
   [ $status -eq 0 ] && { grep -q -i "caught overall timeout" $logs/XRDFED_probe_json.log ; [ $(expr $a + $?) -eq $a ] && status=1 ; } ;
   if [ $status -ne 0 ] ; then
      printf "$(/bin/hostname) $(basename $0)\n$(date)\n$(ls -al $thelog )\n$(cat $thelog)\n" | mail -s "$(/bin/hostname) $(basename $thelog)" $(echo $notifytowhom | sed 's#NOSPAMPLEASE##g')
   fi
fi

