#!/bin/bash
THEPATH=/opt/TransferTeam/AAAOps/FedProbeSendAAAMetrics
FED_json=$THEPATH/out/federations.json
THELOG=$THEPATH/logs/probe_create_send_aaa_metrics.log
KIBANA_PAGE=https://monit-kibana.cern.ch/kibana/goto/5d1128ff8482ac3b00e4be3d5a06e954
GRAFANA_PAGE="https://monit-grafana.cern.ch/d/5njhdTrWk/site-subscription?from=now-7d&orgId=11&to=now"

export X509_USER_PROXY=$HOME/.globus/slsprobe.proxy
if [ -f $X509_USER_PROXY ] ; then
   if [ $(voms-proxy-info -timeleft 2>/dev/null) -lt 3600 ] ; then
	printf "$(/bin/hostname -s) $(basename $0) We have a problem with $X509_USER_PROXY.\n$(voms-proxy-info -all | sed 's#%#%%#g')" | mail -r noreply@cern.ch -s "ERROR $(/bin/hostname -s) $(basename $0) proxy issue 1" $notifytowhom
   fi
else   
   printf "$(/bin/hostname -s) $(basename $0) We have a problem with $X509_USER_PROXY.\nIt does not exist" | mail -r noreply@cern.ch -s "ERROR $(/bin/hostname -s) $(basename $0) proxy issue 2" $notifytowhom
fi
notifytowhom=bockjoo__AT__gmail__dot__com
export PYTHONPATH=$PYTHONPATH:$THEPATH/CMSMonitoring/src/python/
notifytowhom=$(echo $notifytowhom | sed 's#__AT__#@#' | sed 's#__dot__#\.#')

[ -d $THEPATH/out ] || mkdir -p $THEPATH/out

python3 $THEPATH/create_fedmaps.py > $THEPATH/create_fedmaps.log 2>&1
if [ $? -ne 0 ] ; then
	printf "$(/bin/hostname -s) $(basename $0) We have a problem in running python3 $THEPATH/create_fedmaps.py\n\n$THEPATH/create_fedmaps.log:\n$(cat $THEPATH/create_fedmaps.log | sed 's#%#%%#g')\n" | mail -r noreply@cern.ch -s "ERROR $(/bin/hostname -s) $(basename $0)" $notifytowhom
fi
if [ ! -r $FED_json ]; then
	echo "We have a problem creating JSON file.\n"
	printf "$(/bin/hostname -s) $(basename $0) We have a problem creating JSON file.\n\nn$THEPATH/create_fedmaps.log:\n$(cat $THEPATH/create_fedmaps.log | sed 's#%#%%#g')\n" | mail -r noreply@cern.ch -s "ERROR $(/bin/hostname -s) $(basename $0)" $notifytowhom
	exit 1
fi

cat $FED_json | python -m json.tool 2>/dev/null 1>/dev/null
if [ $? -ne 0 ] ; then
	printf "$(/bin/hostname -s) $(basename $0) We have a problem with $FED_json.\n" | mail -r noreply@cern.ch -s "ERROR $(/bin/hostname -s) $(basename $0)" $notifytowhom -a $FED_json
	exit 1
fi
[ -d $(dirname $THELOG) ] || mkdir -p $(dirname $THELOG)

# Server Version List
if [ ] ; then
(
is_int() {
  if [ $1 ] ; then
     theval=$1
     if [ "x$theval" == "x" ] ; then
        return 1
     else
        if [ "x`echo $theval | egrep -v '^[0-9]+$'`" != "x" ] ; then
           return 1
        else
           return 0
        fi
     fi
  else
     return 1
  fi
}
     timeout=10
     echo "To: "$(echo $notifytowhom | sed "s#__AT__#@#" | sed "s#__dot__#\.#g")
     echo "Reply-To: noreply@cern.ch"
     echo "Subject: XRootD Version Role List"
     echo "Content-Type: text/html"
     echo "<html>"
     echo "<table>"
     echo "<tr bgcolor='yellow'><td>Site</td><td>Endpoint</td><td>Version</td><td>Role</td></td>"
     grep "\"sites\"\|\"endpoints\"\|version\|role" $FED_json | \
     while read site ; do
           read endpoints
           read version
           read role
           site=$(echo $site | cut -d\" -f4)
           echo "$site" | grep -q T3 && continue
           endpoints=$(echo $endpoints | cut -d\" -f4)
           version=$(echo $version | cut -d\" -f4)
           role=$(echo $role | cut -d\" -f4)
           # port 0 is an invalid port
           port=$(echo $endpoints | cut -d: -f2) ; [ $port -eq 0 ] && continue
           [ "x$version" == "xtimeout" ] && version=$(echo $(perl -e "alarm $timeout ; exec @ARGV" xrdfs $endpoints query config version | grep "^v\|Alarm clock"))
           [ "$version" == "Alarm clock" ] && version="$timeout(sec)TO"
           [ "x$role" == "xtimeout" ] && role=$(echo $(perl -e "alarm $timeout ; exec @ARGV" xrdfs $endpoints query config role))
           [ "$role" == "Alarm clock" ] && role="$timeout(sec)TO"
           bgcolor="yellow"
           a=$(echo "$version" | grep v | sed "s#[a-z]##g" | sed "s#[A-Z]##g" | cut -d. -f1)
           [ "x$a" == "x" ] && a=1
           [ $(is_int $a ; echo $?) -eq 0 ] || a=1
           a=$(expr 100000 \* $a)
           b=$(echo "$version" | grep v | sed "s#[a-z]##g" | sed "s#[A-Z]##g" | cut -d. -f2)
           [ "x$b" == "x" ] && b=1
           [ $(is_int $b ; echo $?) -eq 0 ] || b=1
           b=$(expr 1000 \* $b)
           c=$(echo "$version" | grep v | sed "s#[a-z]##g" | sed "s#[A-Z]##g" | cut -d. -f3)
           [ "x$c" == "x" ] && c=1
           [ $(is_int $c ; echo $?) -eq 0 ] || c=1
           c=$(expr 10 \* $c)
           expr $a + $b + $c 2>/dev/null 1>/dev/null && \
           [ $(expr $a + $b + $c) -lt 504000 ] && bgcolor="red"
           #[ "x$version" == "xv5.4.3" ] || [ "x$version" == "xv5.4.2" ] || bgcolor="red"
           
           echo "<tr bgcolor='$bgcolor'><td>$site </td><td> $endpoints </td><td> $version <"'!'"-- a=$a b=$b c=$c status=$? --> </td><td> $role </td></td>"
     done
     echo "</table>"
     echo "</html>"
) | /usr/sbin/sendmail -t
fi # if [ ] ; then

rm -f $THEPATH/fed.json
python3 $THEPATH/aaa_federation.py  --amq $THEPATH/credentials.json > $THEPATH/aaa_federation.log 2>&1
status=$?
# Check any error from xrdmapc
xrdmapc_error=$(grep \\[ $THEPATH/out/xrdmapc_prod_1.txt | grep -v "invalid addr" |sort -u)   
xrdmapc_port0_error=$(grep ":0$\|:0 " $THEPATH/out/xrdmapc_prod_1.txt | awk '{if ($2 == "Man") print $3 ; else print $2}' | sed 's#:0$##g' | while read h ; do grep -v $h:0 $THEPATH/out/xrdmapc_prod_1.txt | grep -q $h  $THEPATH/out/xrdmapc_prod_1.txt ; [ $? -eq 0 ] || echo ${h}:0 ; done)
if [ $status -eq 0 ] ; then
      if [ $(date +%M ) -lt 15 ] ; then
         :
         #printf "$(/bin/hostname -s) $(basename $0) AAA metrics sent.\nSee $KIBANA_PAGE\n$GRAFANA_PAGE\nxrdmapc errors: \n$xrdmapc_error\nPort 0 Errors: ${xrdmapc_port0_error}\n" | mail -r noreply@cern.ch -s "INFO $(/bin/hostname -s) $(basename $0)" $notifytowhom -a $THEPATH/logs/probe_create_send_aaa_metrics.log
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
      day_of_week=$(date +%u%H%M%S)
      if [ $day_of_week -gt 1000000 -a $day_of_week -lt 1002800 ] ; then
	  echo "<html>" > $THEPATH/site_aaa_status.html
	  echo "<table>" >> $THEPATH/site_aaa_status.html
	  echo "<tr bgcolor='yellow'> <td>Site</td> <td>Life Status</td> <td>SAM Status</td> <td>WkCount</td> <td>Expected</td> </tr>" >> $THEPATH/site_aaa_status.html
          printf "%20s %20s %20s %7s %7s\n" Site "Life Status" "SAM Status" WkCount Expected > $THEPATH/site_aaa_status.txt
      fi
      if [ ! -f $THEPATH/site_aaa_status.html  ] ; then
	  echo "<html>" > $THEPATH/site_aaa_status.html
	  echo "<table>" >> $THEPATH/site_aaa_status.html
      fi
      if [ ! -f $THEPATH/site_aaa_status.txt  ] ; then
	  echo "<tr bgcolor='yellow'> <td>Site</td> <td>Life Status</td> <td>SAM Status</td> <td>WkCount</td> <td>Expected</td> </tr>" >> $THEPATH/site_aaa_status.html
          printf "%20s %20s %20s %7s %7s\n" Site "Life Status" "SAM Status" WkCount Expected > $THEPATH/site_aaa_status.txt
      fi
      sam3result=
      for thesite in $thediff ; do
          $THEPATH/cms_sam3_check.sh $thesite > $THEPATH/out/cms_sam3_check.${thesite}.txt 2>&1
          status=$?
          result="SAM3 OK" ; [ $status -eq 0 ] || result="SAM3 FAIL"
          site_status=$(python3 -m json.tool $THEPATH/cms_sam3_check_monit_prod_cmssst_search.out | grep -A 2 $thesite | grep status | cut -d\" -f4 | head -1)
	  siteLifeStatus=$(export GRAFANA_VIEWER_TOKEN=$(cat $THEPATH/token.txt) ; python /opt/TransferTeam/AAAOps/FedProbeSendAAAMetrics/siteLifeStatus.py $thesite)
          if [ "x$siteLifeStatus" == "x" ] ; then
	     siteLifeStatus=UNKNOWN
          fi
          sam3result="$sam3result\n$thesite($site_status $result siteLifeStatus=$siteLifeStatus)\n"
	  expected=Yes
	  if [ "$result" == "SAM OK" ] ; then
	      [ $(echo "$siteLifeStatus" | grep -q "wait\|morgue" ; echo $?) -eq 0 ] && expected=No
	  fi
	  if [ $(grep -q "$thesite" $THEPATH/site_aaa_status.txt ; echo $?) -eq 0 ] ; then
	      siteline=$(grep "$thesite" $THEPATH/site_aaa_status.txt)
	      WkCount_previous=$(grep "$thesite" $THEPATH/site_aaa_status.txt | awk '{print $5}')
	      WkCount=$(expr $WkCount_previous + 1)
	      sed -i "/$(echo $thesite | sed 's^/^\\\/^g')/ d" $THEPATH/site_aaa_status.txt
              printf "%20s %20s %20s %7s %7s\n" "$thesite" "$siteLifeStatus" "$result" $WkCount $expected >> $THEPATH/site_aaa_status.txt
	      sed -i "/$(echo $thesite | sed 's^/^\\\/^g')/ d" $THEPATH/site_aaa_status.html
	      echo "<tr bgcolor='yellow'> <td>$thesite</td> <td>$siteLifeStatus</td> <td>$result</td> <td>$WkCount</td> <td>$expected</td> </tr>" >> $THEPATH/site_aaa_status.html
	  else
              printf "%20s %20s %20s %7s %7s\n" "$thesite" "$siteLifeStatus" "$result" 1 $expected >> $THEPATH/site_aaa_status.txt
	      echo "<tr bgcolor='yellow'> <td>$thesite</td> <td>$siteLifeStatus</td> <td>$result</td> <td> 1 </td> <td>$expected</td> </tr>" >> $THEPATH/site_aaa_status.html
	  fi
      done
      if [ -f $THEPATH/site_aaa_status.html ] ; then
	  thestring="</table>"
	  sed -i "/$(echo $thestring | sed 's^/^\\\/^g')/ d" $THEPATH/site_aaa_status.html
	  thestring="</html>"
	  sed -i "/$(echo $thestring | sed 's^/^\\\/^g')/ d" $THEPATH/site_aaa_status.html
          echo "</table>" >> $THEPATH/site_aaa_status.html
          echo "</html>" >> $THEPATH/site_aaa_status.html
      fi
      #if [ "x$thediff" == "xT2_UA_KIPT" ] ; then
      echo $sam3result | grep -q "SAM3 OK" && printf "$(/bin/hostname -s) $(basename $0)  \n$(cat $THEPATH/site_aaa_status.html)\n$(cat $THEPATH/site_aaa_status.txt)\nWe have a problem with $nprod\n$sam3result\n\n$(for thesite in $thediff ; do cat $THEPATH/out/cms_sam3_check.${thesite}.txt ; done)\n" | mail -r noreply@cern.ch -s "Warn $(/bin/hostname -s) $(basename $0)" $notifytowhom
      if [ $(echo $sam3result | grep -q "SAM3 OK" ; echo $?) -eq 0 ] ; then
       (
         echo "To: $notifytowhom"
         echo "Subject: echo $(basename $0) on $(/bin/hostname -s)"
	 echo "Reply-to: noreply@cern.ch"
         echo "Content-Type: text/html"
	 cat $THEPATH/site_aaa_status.html	 
       )  | /usr/sbin/sendmail -t
      fi
      #else
      #   echo $sam3result | grep -q "SAM3 OK" && \
      #   printf "$(/bin/hostname -s) $(basename $0) We have a problem with $nprod\n$sam3result\n\n$(for thesite in $thediff ; do cat $THEPATH/out/cms_sam3_check.${thesite}.txt ; done)\n" | mail -r noreply@cern.ch -s "Warn $(/bin/hostname -s) $(basename $0)" $notifytowhom 
      #fi
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
