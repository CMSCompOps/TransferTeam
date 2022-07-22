#!/bin/bash
THEPATH=/opt/TransferTeam/AAAOps/FedProbeSendAAAMetrics
FED_json=$THEPATH/out/federations.json
THELOG=$THEPATH/logs/probe_create_send_aaa_metrics.log
KIBANA_PAGE=https://monit-kibana.cern.ch/kibana/goto/5d1128ff8482ac3b00e4be3d5a06e954
GRAFANA_PAGE="https://monit-grafana.cern.ch/d/5njhdTrWk/site-subscription?from=now-7d&orgId=11&to=now"

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
if [ $? -ne 0 ] ; then
	printf "$(/bin/hostname -s) $(basename $0) We have a problem in running python3 $THEPATH/create_fedmaps.py\n" | mail -s "ERROR $(/bin/hostname -s) $(basename $0)" $notifytowhom
fi
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

# Server Version List
(
     echo "To: "$(echo $notifytowhom | sed "s#__AT__#@#" | sed "s#__dot__#\.#g")
     echo "Subject: XRootD Version Role List"
     echo "Content-Type: text/html"
     echo "<html>"
     echo "<table>"
     echo "<tr bgcolor='yellow'><td>Site</td><td>Endpoint</td><td>Version</td><td>Role</td></td>"
     grep "\"sites\"\|\"endpoints\"\|version\|role" $FED_json | while read site ; do read endpoints ; read version ; read role ; site=$(echo $site | cut -d\" -f4) ; endpoints=$(echo $endpoints | cut -d\" -f4) ; version=$(echo $version | cut -d\" -f4) ; [ "x$version" == "xtimeout" ] && version=$(echo $(xrdfs $endpoints query config version | grep ^v)) ; role=$(echo $role | cut -d\" -f4) ; [ "x$role" == "xtimeout" ] && role=$(echo $(xrdfs $endpoints query config role)) ; echo "<tr bgcolor='yellow'><td>$site </td><td> $endpoints </td><td> $version </td><td> $role </td></td>" ; done
     echo "</table>"
     echo "</html>"
) | /usr/sbin/sendmail -t


rm -f $THEPATH/fed.json
python3 $THEPATH/aaa_federation.py  --amq $THEPATH/credentials.json > $THEPATH/aaa_federation.log 2>&1
status=$?
# Check any error from xrdmapc
xrdmapc_error=$(grep \\[ $THEPATH/out/xrdmapc_prod_1.txt | grep -v "invalid addr" |sort -u)   
xrdmapc_port0_error=$(grep ":0$\|:0 " $THEPATH/out/xrdmapc_prod_1.txt | awk '{if ($2 == "Man") print $3 ; else print $2}' | sed 's#:0$##g' | while read h ; do grep -v $h:0 $THEPATH/out/xrdmapc_prod_1.txt | grep -q $h  $THEPATH/out/xrdmapc_prod_1.txt ; [ $? -eq 0 ] || echo ${h}:0 ; done)
if [ $status -eq 0 ] ; then
      if [ $(date +%M ) -lt 15 ] ; then
         printf "$(/bin/hostname -s) $(basename $0) AAA metrics sent.\nSee $KIBANA_PAGE\n$GRAFANA_PAGE\nxrdmapc errors: \n$xrdmapc_error\nPort 0 Errors: ${xrdmapc_port0_error}\n" | mail -s "INFO $(/bin/hostname -s) $(basename $0)" $notifytowhom -a $THEPATH/logs/probe_create_send_aaa_metrics.log
      fi
else
      printf "$(/bin/hostname -s) $(basename $0) There might have been an issue or more with sending AAA metrics\nSee $KIBANA_PAGE\n$GRAFANA_PAGE\nxrdmapc errors: \n$xrdmapc_error\nPort 0 Errors: ${xrdmapc_port0_error}\n" | mail -s "ERROR $(/bin/hostname -s) $(basename $0)" $notifytowhom -a $THEPATH/logs/probe_create_send_aaa_metrics.log
fi

#nprod_exp=55
nprod_exp=54
if [ -f $THEPATH/check_subscribed_sites.sh ] ; then
   subscribed_sites=$($THEPATH/check_subscribed_sites.sh)
   nprod=$(printf "$subscribed_sites\n" | tail -1 | awk '{print $2}')
   printf "$subscribed_sites\n" > $THEPATH/subscribed_sites_$nprod.txt
   if [ $nprod_exp -gt $nprod ] ; then
      thediff=
      if [ -f $THEPATH/subscribed_sites_$nprod_exp.txt ] ; then
         thediff=$(diff $THEPATH/subscribed_sites_$nprod.txt $THEPATH/subscribed_sites_$nprod_exp.txt | sed 's#%#%%#g' | grep T | cut -d\" -f2)
      fi
      printf "$(/bin/hostname -s) $(basename $0) We have a problem with $nprod\n$thediff\n" | mail -s "Warn $(/bin/hostname -s) $(basename $0)" $notifytowhom 
      #exit 1
   fi
   echo "Sites subscribed to the Production Federation: " $nprod
fi

printf "$(/bin/hostname -s) $(basename $0) \nxrdmapc errors:\n$xrdmapc_error\nPort 0 Errors: ${xrdmapc_port0_error}\n"

[ -f ${THELOG}_$(date +%Y%m%d) ] || touch  ${THELOG}_$(date +%Y%m%d)
if [ -f $THELOG ] ; then
   cat $THELOG >> ${THELOG}_$(date +%Y%m%d)
fi

exit $status
