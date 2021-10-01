#!/bin/bash

notifytowhom=cms-comp-ops-transfer-team@cernNOSPAMPLEASE.ch

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
      printf "$(/bin/hostname) $(basename $0)\n$(date)\n$(ls -al $thelog )\n$(cat $thelog)\n" | mail -s "$(/bin/hostname) $(basename $thelog)" $(echo $notifytowhom | sed 's#NOSPAMPLEASE##') -a $thelog
   fi
fi

