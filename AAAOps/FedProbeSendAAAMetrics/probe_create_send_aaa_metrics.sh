#!/bin/bash
THEPATH=/opt/TransferTeam/AAAOps/FedProbeSendAAAMetrics
FED_json=$THEPATH/out/federations.json
THELOG=$THEPATH/logs/probe_create_send_aaa_metrics.log
KIBANA_PAGE=https://monit-kibana.cern.ch/kibana/goto/5d1128ff8482ac3b00e4be3d5a06e954

export X509_USER_PROXY=$HOME/.globus/slsprobe.proxy
if [ -f $X509_USER_PROXY ] ; then
   if [ $(voms-proxy-info -timeleft 2>/dev/null) -lt 3600 ] ; then
	printf "$(/bin/hostname -s) $(basename $0) We have a problem with $X509_USER_PROXY.\n$(voms-proxy-info -all | sed 's#%#%%#g')" | mail -s "ERROR $(/bin/hostname -s) $(basename $0) proxy issue 1" $notifytowhom
   fi
else   
   printf "$(/bin/hostname -s) $(basename $0) We have a problem with $X509_USER_PROXY.\nIt does not exist" | mail -s "ERROR $(/bin/hostname -s) $(basename $0) proxy issue 2" $notifytowhom
fi
notifytowhom=bockjoo__AT__gmail__dot__com
export PYTHONPATH=$PYTHONPATH:$THEPATH/CMSMonitoring/src/python/
notifytowhom=$(echo $notifytowhom | sed 's#__AT__#@#' | sed 's#__dot__#\.#')

[ -d $THEPATH/out ] || mkdir -p $THEPATH/out

python3 $THEPATH/create_fedmaps.py > $THEPATH/create_fedmaps.log 2>&1

if [ ! -r $FED_json ]; then
	echo "We have a problem creating JSON file.\n"
	printf "$(/bin/hostname -s) $(basename $0) We have a problem creating JSON file.\n" | mail -s "ERROR $(/bin/hostname -s) $(basename $0)" $notifytowhom
	exit 1
fi

cat $FED_json | python -m json.tool 2>/dev/null 1>/dev/null
if [ $? -ne 0 ] ; then
	printf "$(/bin/hostname -s) $(basename $0) We have a problem with $FED_json.\n" | mail -s "ERROR $(/bin/hostname -s) $(basename $0)" $notifytowhom -a $FED_json
	exit 1
fi
[ -d $(dirname $THELOG) ] || mkdir -p $(dirname $THELOG)

rm -f $THEPATH/fed.json
python3 $THEPATH/aaa_federation.py  --amq $THEPATH/credentials.json > $THEPATH/aaa_federation.log 2>&1
status=$?
if [ $(date +%M ) -lt 15 ] ; then
   if [ $status -eq 0 ] ; then
      printf "$(/bin/hostname -s) $(basename $0) AAA metrics sent.\nSee $KIBANA_PAGE\n" | mail -s "INFO $(/bin/hostname -s) $(basename $0)" $notifytowhom -a $THEPATH/logs/probe_create_send_aaa_metrics.log
   else
      printf "$(/bin/hostname -s) $(basename $0) There might have been an issue or more with sending AAA metrics\nSee $KIBANA_PAGE\n" | mail -s "ERROR $(/bin/hostname -s) $(basename $0)" $notifytowhom -a $THEPATH/logs/probe_create_send_aaa_metrics.log
   fi
fi
nprod_exp=55
if [ -f $THEPATH/check_subscribed_sites.sh ] ; then
   nprod=$($THEPATH/check_subscribed_sites.sh | tail -1 | awk '{print $2}')
   if [ $nprod_exp -gt $nprod ] ; then
      printf "$(/bin/hostname -s) $(basename $0) We have a problem with $nprod\n" | mail -s "Warn $(/bin/hostname -s) $(basename $0)" $notifytowhom 
      #exit 1
   fi
   echo "Sites subscribed to the Production Federation: " $nprod
fi

[ -f ${THELOG}_$(date +%Y%m%d) ] || touch  ${THELOG}_$(date +%Y%m%d)
if [ -f $THELOG ] ; then
   cat $THELOG >> ${THELOG}_$(date +%Y%m%d)
fi

exit $status
