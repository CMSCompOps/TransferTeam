#!/bin/bash
#
# Bockjoo Kim
# WHAT : Minimally large effort Emulation of CMS SAM Dashboard in plain cgi/HTML or for failed test alert
# Reference : https://monit-grafana.cern.ch/d/2LNN04NMk/user-carizapo-sitemon?orgId=11
#             https://monit-kibana-acc.cern.ch/kibana/app/kibana#/discover?_g=(filters:!(),refreshInterval:(pause:!t,value:0),time:(from:now-17h,to:now))&_a=(columns:!(data.metric_name,data.service_flavour,data.dst_experiment_site,data.status),filters:!(('$state':(store:appState),meta:(alias:!n,disabled:!f,index:'monit_prod_sam3_enr_*',key:data.dst_experiment_site,negate:!f,params:(query:T2_US_Florida),type:phrase,value:T2_US_Florida),query:(match:(data.dst_experiment_site:(query:T2_US_Florida,type:phrase))))),index:'monit_prod_sam3_enr_*',interval:auto,query:(language:kuery,query:''),sort:!(metadata.timestamp,desc))
#             https://monit-kibana-acc.cern.ch/kibana/goto/7f572448ab2bbd36280ad87a3f499abe
#             SAM test twiki : https://twiki.cern.ch/twiki/bin/view/CMSPublic/CompOpsSAMTests
#             SAM test twiki : https://twiki.cern.ch/twiki/bin/view/CMS/SAMTestEmulationHowto
#             Gitlab : https://gitlab.cern.ch/etf/cmssam/-/tree/master
#
#inputs=/opt/cms/services/HammerCloudXrootdMonitoring
inputs=/opt/TransferTeam/AAAOps/FedProbeSendAAAMetrics
notifytowhom=bockjoo__AT__gmail__dot__com
#THESITE=T2_US_Florida
#tld=rc.ufl.edu # change this
#port=8443
#webroot=http://$(/bin/hostname -s).${tld}:${port}/cgi-bin
#thesite=
#used_percent_warning=70 # change this if needed
#used_percent=$(df -h /$(echo $inputs | cut -d/ -f2) | grep -v Filesystem | awk '{print $(NF-1)}' | sed 's#%##g')
#if [ $used_percent -gt $used_percent_warning ] ; then
#   (
#     echo "To: "$(echo $notifytowhom | sed "s#__AT__#@#" | sed "s#__dot__#\.#g")
#     echo "Subject: Warning not enough space in /opt"
#     echo "Content-Type: text/html"
#     echo "<html>"
#     echo "<pre>"
#     echo "$(/bin/hostname)" "$0" "<br/>"
#     echo "Used: $used_percent (%) vs Used Warning: $used_percent_warning (%)"
#     du -sh $inputs/*
#     echo "</pre>"
#     echo "</html>"
#     #cat $inputs/$(echo $basename_0 | sed "s#.sh##")_${now_is}.html
#     echo
#   ) | /usr/sbin/sendmail -t  
#fi

basename_0=$(basename $0)
gte="now-40m/m"
lte="now"
scroll="20m"
size=10000
theprofile=CMS_CRITICAL_FULL
#theprofile=CMS_CRITICAL
#theprofile=CMS_FULL
DBID=9673
EVERY_X_HOUR=1
#unique_f=data.metric_name # data.CRAB_JobLogURL
##tie_breaker_id=metadata.kafka_timestamp # data.CRAB_TaskCreationDate
#tie_breaker_id=metadata.timestamp # data.CRAB_TaskCreationDate
unique_f=metadata.timestamp # data.CRAB_JobLogURL
tie_breaker_id=data.metric_name # data.CRAB_TaskCreationDate
tie_breaker_id=metadata.kafka_timestamp #
#index_json="{\"search_type\": \"query_then_fetch\", \"index\": [\"monit_prod_cms_rucio_raw_events*\"], \"ignore_unavailable\": true}"

detail_link_prefix="https://monit-grafana.cern.ch/d/siYq3DxZz/wlcg-sitemon-test-details?orgId=20&var-id="
cms_wiki_how_to_sam="https://twiki.cern.ch/twiki/bin/view/CMS/SAMTestEmulationHowto"

#printf "Content-type: text/html\n\n"

functions=$inputs/`basename ${0}`.fuctions.`date -u +%s`
perl -n -e 'print if /^####### BEGIN Functions 12345/ .. /^####### ENDIN Functions 12345/' < $0 | grep -v "Functions 12345" > $functions
source $functions
rm -f $functions

#[ $# -gt 0 ] && thesite=$1
#[ $# -gt 1 ] && gte=$2
#[ $# -gt 2 ] && lte=$3


#thestrings=`echo $QUERY_STRING | sed "s#&# #g"`
#for thestring in $thestrings ; do
#    echo "$thestring" | grep -q -e "test_howto\|test_id\|test_output\|site\|gte\|lte\|match_all"
#    [ $? -eq 0 ] || continue
#    eval $thestring
#    if [ "x$site" != "x" ] ; then
#       thesite=$site
#    fi
#done

#thestrings=`echo $QUERY_STRING | sed "s#&# #g"`
#for thestring in $thestrings ; do
#    echo "$thestring" | grep -q -e "test_howto\|test_id\|test_output\|site\|gte\|lte\|match_all"
#    [ $? -eq 0 ] || continue
#    if [ "x$test_id" != "x" ] ; then
#       print_test_output $test_id $site
#       exit 0
#    fi
#    if [ "x$test_howto" != "x" ] ; then
#       echo "<html><pre>"
#       echo "How to emulate this SAM test ( $test_howto )"
#       thefunction=readme_$(echo $test_howto | sed "s|\.|__dot__|g" | sed "s|-|__dash__|g")
#       $thefunction
#       echo "</pre></html>"
#       exit 0
#    fi
#done

#if [ "x$thesite" == "x" ] ; then
#   thesite=$(basename $(readlink -f /cvmfs/cms.cern.ch/SITECONF/local))
#fi
#if [ "x$thesite" == "x" ] ; then
#   printf "Content-type: text/html\n\n"
#   echo ERROR $(basename $0) provide the argument for the site name
#   exit 0
#fi
#if [ $(echo $thesite | wc -w) -ne 1 ] ; then
#   printf "Content-type: text/html\n\n"
#   echo ERROR $(basename $0) Unfortunately number of sitename is not unique or zero.
#   exit 0
#fi


#now_is=$(date +%s)_${thesite}
#now_is=$(date +%s)_american_sites
#echo "<html>" > $inputs/$(echo $basename_0 | sed "s#.sh##")_${now_is}.html

# All the template json files needed here found in $inputs
#sitemon_agg_metric_json=es.q.match_sitemon_raw_metric.json
token_txt=cms_sam3_check_token.txt
sort_search_json=cms_sam3_check_sort_search.json
sort_search_after_json=cms_sam3_check_sort_search_after.json
search_details=es.q.match_sitemon_raw_metric_search_details.json
sort_search_id_json=es.q.match_sitemon_raw_metric_sort_search_id.json
perl -n -e 'print if /^####### BEGIN token_txt/ .. /^####### ENDIN token_txt/' < $0 | grep -v "token_txt" > $token_txt
perl -n -e 'print if /^####### BEGIN sort_search_json/ .. /^####### ENDIN sort_search_json/' < $0 | grep -v "sort_search_json" > ${sort_search_json}.in
perl -n -e 'print if /^####### BEGIN sort_search_after_json/ .. /^####### ENDIN sort_search_after_json/' < $0 | grep -v "sort_search_after_json" > ${sort_search_after_json}.in

GTE=$(echo $gte | sed 's#/# #' | awk '{print $1}')
LTE=$(echo $lte | sed 's#/# #' | awk '{print $1}')
#sites="T2_US_Caltech T2_US_Florida T2_US_MIT T2_US_Nebraska T2_US_Purdue T2_US_UCSD T2_US_Wisconsin T2_BR_SPRACE T2_BR_UERJ"
#sites=T2_US_Florida
#sites="T2_US_Florida T2_US_Caltech T2_US_MIT T2_US_Nebraska T2_US_Purdue T2_US_UCSD T2_US_Wisconsin T2_BR_SPRACE T2_BR_UERJ T1_US_FNAL T2_US_Vanderbilt T2_UK_London_Brunel T3_US_Colorado" #  T2_KR_KISTI T2_FR_CCIN2P3 T0_CH_CERN T1_UK_RAL"
#sites="T2_US_Florida T2_RU_ITEP" # T2_PK_NCP" # T2_US_Caltech T2_US_MIT T2_US_Nebraska T2_US_Purdue T2_US_UCSD T2_US_Wisconsin T2_BR_SPRACE T2_BR_UERJ T1_US_FNAL T2_KR_KISTI T2_FR_CCIN2P3 T0_CH_CERN T1_UK_RAL"

#sites="T2_US_Florida T2_AT_Vienna T2_BE_IIHE T2_BE_UCL T2_BR_SPRACE T2_BR_UERJ T2_CH_CERN T2_CH_CSCS T2_CN_Beijing T2_DE_DESY T2_DE_RWTH T2_EE_Estonia T2_ES_CIEMAT T2_ES_IFCA T2_FI_HIP T2_FR_GRIF_IRFU T2_FR_IPHC T2_GR_Ioannina T2_HU_Budapest T2_IN_TIFR T2_IT_Bari T2_IT_Legnaro T2_IT_Pisa T2_IT_Rome T2_KR_KISTI T2_PK_NCP T2_PL_Swierk T2_PT_NCG_Lisbon T2_RU_IHEP T2_RU_INR T2_RU_ITEP T2_RU_JINR T2_TR_METU T2_TW_NCHC T2_UA_KIPT T2_UK_London_Brunel T2_UK_London_IC T2_UK_SGrid_RALPP T2_US_Caltech T2_US_MIT T2_US_Nebraska T2_US_Purdue T2_US_UCSD T2_US_Vanderbilt T2_US_Wisconsin T0_CH_CERN"
if [ $# -lt 1 ] ; then
   echo ERROR: $(basename $0) site
   exit 1
fi

[ $# -gt 0 ] && thesite="$1"
 
error_message=""
#error_message_html=""
#extra_metric_names=""
#for thesite in $sites ; do


#sed -e "s#@@gte@@#$gte#" -e "s#@@lte@@#$lte#" -e "s#@@thesite@@#$thesite#" -e "s#@@profile@@#$theprofile#" $inputs/${sitemon_agg_metric_json}.in > ${sitemon_agg_metric_json}_${now_is}
#nhits=$(curl -H "Content-Type: application/x-ndjson" -H "Authorization: Bearer $(cat $inputs/token.txt)" -XGET https://monit-grafana.cern.ch/api/datasources/proxy/${DBID}/_msearch --data-binary "@${sitemon_agg_metric_json}_${now_is}" 2>/dev/null | sed 's#"hits":#\nhits_total #' | grep ^hits_total | cut -d: -f2 | cut -d, -f1)

#sed -e "s#@@gte@@#$gte#" -e "s#@@lte@@#$lte#" -e "s#@@thesite@@#$thesite#" -e "s#@@profile@@#$theprofile#" -e "s#@@size@@#$size#" -e "s#@@unique_f@@#$unique_f#" -e "s#@@tie_breakter_id@@#$tie_breaker_id#" $inputs/${sort_search_json}.in > ${sort_search_json}_${now_is}
#nsearch=$(expr $nhits / $size)

#echo "<pre>"
#echo "<FONT size=3 color='green'> <b> Site:$thesite SAM Test Status </b> </FONT>"
#echo "<title><center><FONT color='green'> <b> Site:$thesite SAM Test Status </b> </FONT></center></title>"
#echo "<center><FONT size=7 color='green'> <b> Site:$thesite SAM Test Status </b> </FONT></center>" >> $inputs/$(echo $basename_0 | sed "s#.sh##")_${now_is}.html
#echo INFO Site=$thesite nhits=$nhits query json follows
#cat ${sort_search_json}_${now_is}
#echo "</pre>"

#for i in $(seq 0 $nsearch) ; do
i=0
while : ; do
   i=$(expr $i + 1)
   if [ $i -eq 1 ] ; then
      sed -e "s#@@gte@@#$gte#" -e "s#@@lte@@#$lte#" -e "s#@@thesite@@#$thesite#" -e "s#@@profile@@#$theprofile#" -e "s#@@size@@#$size#" -e "s#@@unique_f@@#$unique_f#" -e "s#@@tie_breakter_id@@#$tie_breaker_id#" $inputs/${sort_search_json}.in > $inputs/${sort_search_json}
      curl -H "Content-Type: application/x-ndjson" -H "Authorization: Bearer $(cat $token_txt)" -XGET https://monit-grafana.cern.ch/api/datasources/proxy/${DBID}/_msearch --data-binary "@$inputs/${sort_search_json}" 2>/dev/null 1> $inputs/$(basename $0 | sed "s#\.sh##").$i.out
      rm -f $inputs/${sort_search_json}
   else
      sed -e "s#@@gte@@#$gte#" -e "s#@@lte@@#$lte#" -e "s#@@thesite@@#$thesite#" -e "s#@@profile@@#$theprofile#" -e "s#@@size@@#$size#" -e "s|@@search_after@@|$search_after|" -e "s#@@unique_f@@#$unique_f#" -e "s#@@tie_breakter_id@@#$tie_breaker_id#" $inputs/${sort_search_after_json}.in > $inputs/${sort_search_after_json}
      curl -H "Content-Type: application/x-ndjson" -H "Authorization: Bearer $(cat $token_txt)" -XGET https://monit-grafana.cern.ch/api/datasources/proxy/${DBID}/_msearch --data-binary "@$inputs/${sort_search_after_json}" 2>/dev/null 1> $inputs/$(basename $0 | sed "s#\.sh##").$i.out
      rm -f $inputs/${sort_search_after_json}
   fi
   #echo DEBUG $inputs/$(basename $0 | sed "s#\.sh##").$i.out_${now_is}
   entry=$(sed "s#\"_source\":#\n\"_source\":#g" $inputs/$(echo $basename_0 | sed "s#\.sh##").$i.out | grep ^\"_source\": | wc -l)
   search_after=$(sed 's#sort":#\nsort":#g' $inputs/$(basename $0 | sed "s#\.sh##").$i.out | grep ^sort | tail -1 | cut -d\[ -f2- | cut -d\] -f1)
   #echo DEBUG entry=$entry
   #echo DEBUG search_after=$search_after
   [ $entry -lt $size ] && break
   [ "x$search_after" == "xnull,null" ] && break
   [ "x$search_after" == "x" ] && break
done

#exit 0

#   if [ $i -eq 0 ] ; then
#      curl -H "Content-Type: application/x-ndjson" -H "Authorization: Bearer $(cat $inputs/token.txt)" -XGET https://monit-grafana.cern.ch/api/datasources/proxy/${DBID}/_msearch --data-binary "@${sort_search_json}_${now_is}" 2>/dev/null 1> $(basename $0 | sed "s#\.sh##").$i.out_${now_is}
#      search_after=$(sed 's#sort":#\nsort":#g' $(basename $0 | sed "s#\.sh##").$i.out_${now_is} | grep ^sort | tail -1 | cut -d\[ -f2- | cut -d\] -f1)
#   else
#      sed -e "s#@@thesite@@#$thesite#" -e "s#@@profile@@#$theprofile#" -e "s#@@size@@#$size#" -e "s|@@search_after@@|$search_after|" -e "s#@@unique_f@@#$unique_f#" -e "s#@@tie_breakter_id@@#$tie_breaker_id#" $inputs/${sort_search_after_json}.in > ${sort_search_after_json}_${now_is}
#      curl -H "Content-Type: application/x-ndjson" -H "Authorization: Bearer $(cat $inputs/token.txt)" -XGET https://monit-grafana.cern.ch/api/datasources/proxy/${DBID}/_msearch --data-binary "@${sort_search_after_json}_${now_is}" 2>/dev/null 1> $(basename $0 | sed "s#\.sh##").$i.out_${now_is}
#      search_after=$(sed 's#sort":#\nsort":#g' $(basename $0 | sed "s#\.sh##").$i.out_${now_is} | grep ^sort | tail -1 | cut -d\[ -f2- | cut -d\] -f1)
#   fi
#done

#ls $inputs/$(basename $0 | sed "s#\.sh##").*.out_${now_is}
#exit 0

#timestamps=$(sed 's#"data":#\n"data":#g' $inputs/$(basename $0 | sed "s#\.sh##").*.out | sed 's#,"#,\n"#g' | grep "^\"_id\"\|^\"metric_name\"\|^\"dst_hostname\"\|^\"status\"\|^\"service_flavour\"\|^\"timestamp\"" | grep "\"timestamp\"" | cut -d: -f2 | cut -d, -f1 | cut -d\} -f1 | sort -rn | uniq)
#LEGEND="
#01:org.cms.WN-squid:(/cms/Role_lcgadmin)
#02:org.cms.WN-frontier:(/cms/Role_lcgadmin)
#03:org.cms.WN-basic:(/cms/Role_lcgadmin)
#04:org.cms.SRM-GetPFNFromTFC:(/cms/Role_production)
#05:org.cms.WN-xrootd-access:(/cms/Role_lcgadmin)
#06:org.cms.SE-xrootd-connection
#07:org.cms.WN-xrootd-fallback:(/cms/Role_lcgadmin)
#08:org.cms.WN-mc:(/cms/Role_lcgadmin)
#09:org.cms.WN-env:(/cms/Role_lcgadmin)
#10:org.cms.WN-isolation:(/cms/Role_lcgadmin)
#11:org.cms.SRM-VOPut:(/cms/Role_production)
#12:org.sam.CONDOR-JobSubmit:(/cms/Role_lcgadmin)
#13:org.cms.WN-analysis:(/cms/Role_lcgadmin)
#14:org.cms.SE-xrootd-contain
#15:org.cms.SRM-VOGet:(/cms/Role_production)
#16:org.cms.SE-xrootd-version
#17:org.cms.SE-xrootd-read
#99:org.cms.WN-cvmfs:(/cms/Role_lcgadmin)"
LEGEND="
01:org.cms.WN-squid:(/cms/Role_lcgadmin)
02:org.cms.WN-frontier:(/cms/Role_lcgadmin)
03:org.cms.WN-basic:(/cms/Role_lcgadmin)
04:org.cms.SRM-GetPFNFromTFC:(/cms/Role_production)
05:org.cms.WN-xrootd-access:(/cms/Role_lcgadmin)
06:org.cms.SE-xrootd-connection
07:org.cms.WN-xrootd-fallback:(/cms/Role_lcgadmin)
08:org.cms.WN-mc:(/cms/Role_lcgadmin)
09:org.cms.WN-env:(/cms/Role_lcgadmin)
10:org.cms.WN-isolation:(/cms/Role_lcgadmin)
11:org.cms.SRM-VOPut:(/cms/Role_production)
12:org.sam.CONDOR-JobSubmit:(/cms/Role_lcgadmin)
13:org.cms.WN-analysis:(/cms/Role_lcgadmin)
14:org.cms.SE-xrootd-contain
15:org.cms.SRM-VOGet:(/cms/Role_production)
16:org.cms.SE-xrootd-version
17:org.cms.SE-xrootd-read
18:org.cms.SE-WebDAV-1connection
19:org.cms.SE-WebDAV-2ssl
20:org.cms.SE-WebDAV-3extension
21:org.cms.SE-WebDAV-4crt-read
22:org.cms.SE-WebDAV-5open-access
23:org.cms.SE-WebDAV-6crt-write
24:org.cms.SE-WebDAV-7macaroon
25:org.cms.SE-WebDAV-9summary
26:org.cms.CONDOR-Ping:(/cms-ce-token)
99:org.cms.WN-cvmfs:(/cms/Role_lcgadmin)"
metrics=$(printf "$LEGEND\n" | cut -d: -f2 | grep ^org | sed "s#^org#\\\\\\\|org#g")
metrics=$(echo $metrics | sed "s#\\\\|org#org#" | sed "s# ##g" | sed "s#\\\org#org#")
metrics=$(printf "$LEGEND\n" | cut -d: -f2 | grep ^org | sed "s#^org#\\\|org#g")
metrics=$(echo $metrics | sed "s#\\\|org#org#" | sed "s# ##g")

output=$(sed 's#"data":#\n"data":#g' $inputs/$(basename $0 | sed "s#\.sh##").*.out | sed 's#,"#,\n"#g' | grep "^\"_id\"\|^\"metric_name\"\|^\"dst_hostname\"\|^\"status\"\|^\"service_flavour\"\|^\"timestamp\"" | grep -B 5 -A 5 "$metrics")
#exit 0
if [ ] ; then
    echo "<table>" >> $inputs/$(echo $basename_0 | sed "s#.sh##")_${now_is}.html

    for sf in $(printf "$output\n" | grep "\"service_flavour\"" | sort -u | cut -d\" -f4) ; do
	[ "$sf" == "SRM" ] && continue
	[ "$sf" == "XROOTD" ] && continue
	[ "$sf" == "WEBDAV" ] && continue
	nt=0
	for h in $(printf "$output\n" | grep -A 2 -B 3 $sf | grep "\"dst_hostname\"" | sort -u | cut -d\" -f4) ; do
            nt=$(for t in $(printf "$output\n" | grep -A 2 -B 3 $sf | grep -A 4 -B 1 $h | grep "\"metric_name\"" | cut -d\" -f4 | sort -u) ; do echo $t ; done | wc -l)
            [ $nt -lt 10 ] && { nt=0 ; break ; } ;
	done       
    done
    [ $nt -lt 10 ] && { echo "<pre>" Warning one or more CE has number of tests less than 10 "</pre>" : nt=$nt  >> $inputs/$(echo $basename_0 | sed "s#.sh##")_${now_is}.html ; } ;

    if [ "x$thesite" == "x$THESITE" ] ; then
	if [ $nt -lt 10 ] ; then
	    error_message="$error_message\nERROR one or more CE has number of tests less than 10 nt=$nt \n"
	    #else 
	    #   error_message="$error_message\nINFO All CEs have at least number of tests: nt=$nt \n"
	    error_message=""
	fi
    fi

    echo "<tr><td bgcolor='cyan'>Sitename<td><td bgcolor='cyan'>Flavor</td><td bgcolor='cyan'> Host </td>" >> $inputs/$(echo $basename_0 | sed "s#.sh##")_${now_is}.html
fi # if [ ] ; then

i=0
old_sf=
profile_history_site_link="https://monit-grafana.cern.ch/d/000000619/wlcg-sitemon-historical-profiles?orgId=20&var-vo=cms&var-dst_country=All&var-dst_federation=All&var-dst_tier=2&var-dst_experiment_site=${thesite}&var-service_flavour=All&var-profile=CMS_CRITICAL_FULL&var-dst_hostname=All&var-es_dst_hostname=All&var-recomputation=status"
#for sf in $(printf "$output\n" | grep "\"service_flavour\"" | sort -u | cut -d\" -f4) ; do
#   echo $sf
#done
#exit 0
for sf in $(printf "$output\n" | grep "\"service_flavour\"" | sort -u | cut -d\" -f4) ; do
       i=$(expr $i + 1)
       j=0
       [ "$sf" != "WEBDAV" ] && [ "$sf" != "XROOTD" ] && continue
       #printf "$output\n" | grep -A 2 -B 3  \"service_flavour\":\"$sf\" | grep -A 4 -B 1 \"dst_hostname\":\"$h\" | grep -m 1 -A 5 $t | grep "\"status\"" | cut -d\" -f4
       maxt=0 ; maxh=
       #for h in $(printf "$output\n" | grep -A 2 -B 3 $sf | grep "\"dst_hostname\"" | sort -u | cut -d\" -f4) ; do
       for h in $(printf "$output\n" | grep -A 2 -B 3 \"service_flavour\":\"$sf\" | grep "\"dst_hostname\"" | sort -u | cut -d\" -f4) ; do
           #echo DEBUG $sf $h
           #nt=$(printf "$output\n" | grep -A 2 -B 3 $sf | grep -A 4 -B 1 $h | grep "\"metric_name\"" | cut -d\" -f4 | sort -u | wc -l)
           nt=$(printf "$output\n" | grep -A 2 -B 3 \"service_flavour\":\"$sf\" | grep -A 4 -B 1 \"dst_hostname\":\"$h\" | grep "\"metric_name\"" | cut -d\" -f4 | sort -u | wc -l)
           #for t in $(printf "$output\n" | grep -A 2 -B 3 $sf | grep -A 4 -B 1 $h | grep "\"metric_name\"" | cut -d\" -f4 | sort -u) ; do
           for t in $(printf "$output\n" | grep -A 2 -B 3 \"service_flavour\":\"$sf\" | grep -A 4 -B 1 \"dst_hostname\":\"$h\" | grep "\"metric_name\"" | cut -d\" -f4 | sort -u) ; do
                 m_name=$(echo $t  | sed 's#-/# #g' | awk '{print $1}')
                 L=$(echo $(printf "$LEGEND\n" | grep $m_name | cut -d: -f1))
                 if [ "x$L" == "x" ] ; then
                    echo "$extra_metric_names" | grep -q $t || extra_metric_names="$extra_metric_names <br/> $t"
                 fi
           done
           [ $nt -gt $maxt ] && { maxt=$nt ; maxh=$h ; } ;
       done
#done
#echo DEBUG maxt=$maxt maxh=$maxh
#exit 0
       lstring=
       #for h in $(printf "$output\n" | grep -A 2 -B 3 $sf | grep "\"dst_hostname\"" | sort -u | cut -d\" -f4) ; do
       for h in $(printf "$output\n" | grep -A 2 -B 3 \"service_flavour\":\"$sf\" | grep "\"dst_hostname\"" | sort -u | cut -d\" -f4) ; do
          if [ "$h" == "$maxh" ] ; then
             #[ $i -gt 1 ] && echo "<tr><td>&nbsp;<td><td>&nbsp;</td><td>&nbsp;</td>" >> $inputs/$(echo $basename_0 | sed "s#.sh##")_${now_is}.html
             #for t in $(printf "$output\n" | grep -A 2 -B 3 $sf | grep -A 4 -B 1 $h | grep "\"metric_name\"" | cut -d\" -f4 | sort -u) ; do
             for t in $(printf "$output\n" | grep -A 2 -B 3 \"service_flavour\":\"$sf\" | grep -A 4 -B 1 \"dst_hostname\":\"$h\" | grep "\"metric_name\"" | cut -d\" -f4 | sort -u) ; do
                 m_name=$(echo $t  | sed 's#-/# #g' | awk '{print $1}')
                 L=$(echo $(printf "$LEGEND\n" | grep $m_name | cut -d: -f1))
                 [ "x$L" == "x" ] || { 
                    #echo "<td bgcolor='cyan'> <b> <a href='?test_howto=$m_name' target=_blank> $L </a> </b> </td>"  >> $inputs/$(echo $basename_0 | sed "s#.sh##")_${now_is}.html
                    twiki_toc=${L}_$(echo $m_name | sed "s#\.#_#g" | sed "s#-#_#g")
                    #echo "<td bgcolor='cyan'> <b> <a href='${cms_wiki_how_to_sam}#${twiki_toc}' target=_blank> $L </a> </b> </td>"  >> $inputs/$(echo $basename_0 | sed "s#.sh##")_${now_is}.html
                    lstring="${lstring}|$L"
                  } ;
             done
             #echo "</tr>" >> $inputs/$(echo $basename_0 | sed "s#.sh##")_${now_is}.html
          fi
       done
       #echo DEBUG lstring=$lstring
#done
#exit 0
       #for h in $(printf "$output\n" | grep -A 2 -B 3 $sf | grep "\"dst_hostname\"" | sort -u | cut -d\" -f4) ; do
       for h in $(printf "$output\n" | grep -A 2 -B 3 \"service_flavour\":\"$sf\" | grep "\"dst_hostname\"" | sort -u | cut -d\" -f4) ; do
          profile_history_host_link="https://monit-grafana.cern.ch/d/000000619/wlcg-sitemon-historical-profiles?orgId=20&var-vo=cms&var-dst_country=All&var-dst_federation=All&var-dst_tier=2&var-dst_experiment_site=${thesite}&var-service_flavour=All&var-profile=CMS_CRITICAL_FULL&var-dst_hostname=${h}&var-es_dst_hostname=${h}&var-recomputation=status"
          j=$(expr $j + 1)
          if [ ] ; then
          if [ $i -eq 1 ] ; then # First Service Flavor
             if [ $j -eq 1 ] ; then
                echo "<tr><td><a href='$profile_history_site_link' target=_blank> $thesite </a> <td><td><FONT color='green'>$sf</FONT></td><td> <a href='$profile_history_host_link' target=_blank> $h </a> </td>" >> $inputs/$(echo $basename_0 | sed "s#.sh##")_${now_is}.html
             else
                echo "<tr><td>&nbsp;<td><td>&nbsp;</td><td> <a href='$profile_history_host_link' target=_blank> $h </a> </td>" >> $inputs/$(echo $basename_0 | sed "s#.sh##")_${now_is}.html
             fi
          else
             if [ $j -eq 1 ] ; then
                echo "<tr><td>&nbsp;<td><td><FONT color='green'>$sf</FONT></td><td> <a href='$profile_history_host_link' target=_blank> $h </a> </td>" >> $inputs/$(echo $basename_0 | sed "s#.sh##")_${now_is}.html
             else
                echo "<tr><td>&nbsp;<td><td>&nbsp;</td><td> <a href='$profile_history_host_link' target=_blank> $h </a> </td>" >> $inputs/$(echo $basename_0 | sed "s#.sh##")_${now_is}.html
             fi
          fi
          fi # if [ ] ; then
          im=0
          for legend in $(echo $lstring | sed "s#|# #g") ; do
             im=$(expr $im + 1)
             t=$(printf "$LEGEND\n" | grep "${legend}:" | cut -d: -f2)
             #status=$(printf "$output\n" | grep -A 2 -B 3 $sf | grep -A 4 -B 1 $h | grep -m 1 -A 5 $t | grep "\"status\"" | cut -d\" -f4)
             #id=$(echo $(printf "$output\n" | grep -A 2 -B 3 $sf | grep -A 4 -B 1 $h | grep -m 1 -B 5 $t | grep "\"_id\"" | cut -d\" -f4))
             #timestamp=$(echo $(printf "$output\n" | grep -A 2 -B 3 $sf | grep -A 4 -B 1 $h | grep -B 5 -A 5 $t | grep "\"timestamp\"" | cut -d\" -f3 | cut -d: -f2 | cut -d, -f1 | head -1)) # | cut -d: -f2 | cut -d, -f1 | head -1)) # | grep -m 1 -B 5 -A 5 $t | cut -d\" -f4))
             status=$(printf "$output\n" | grep -A 2 -B 3  \"service_flavour\":\"$sf\" | grep -A 4 -B 1 \"dst_hostname\":\"$h\" | grep -m 1 -A 5 $t | grep "\"status\"" | cut -d\" -f4)
             echo $sf $h $legend t=$t status=$status
             if [ "x$status" != "xOK" ] ; then
                error_message="$error_message\n[$sf][$h][$t]"
             fi
          done # for legend in $(echo $lstring | sed "s#|# #g") ; do
       done # for h in $(printf "$output\n" | grep -A 2 -B 3 \"service_flavour\":\"$sf\" | grep "\"dst_hostname\"" | sort -u | cut -d\" -f4) ; do
done # for sf in $(printf "$output\n" | grep "\"service_flavour\"" | sort -u | cut -d\" -f4) ; do
if [ "x$error_message" != "x" ] ; then
   #printf "$error_message\n"
   echo $thesite NOTOK
   exit 1
fi
exit 0

#           done
#           done
#           done
#exit 0
             #id=$(echo $(printf "$output\n" | grep -A 2 -B 3  \"service_flavour\":\"$sf\" | grep -A 4 -B 1 \"dst_hostname\":\"$h\" | grep -m 1 -B 5 $t | grep "\"_id\"" | cut -d\" -f4))
             #timestamp=$(echo $(printf "$output\n" | grep -A 2 -B 3  \"service_flavour\":\"$sf\" | grep -A 4 -B 1 \"dst_hostname\":\"$h\" | grep -B 5 -A 5 $t | grep "\"timestamp\"" | cut -d\" -f3 | cut -d: -f2 | cut -d, -f1 | head -1)) # | cut -d: -f2 | cut -d, -f1 | head -1)) # | grep -m 1 -B 5 -A 5 $t | cut -d\" -f4))
             #YmdHM=$(date -d@$(expr $timestamp / 1000) +%Y%m%d_%H:%M) 

             #echo DEBUG sf=$sf h=$h legend=$legend t=$t

             #if [ "x$timestamp" == "x" ] ; then
             #   YmdHM=SPARSE
             #else
             #   YmdHM=$(date -d@$(expr $timestamp / 1000) +%m%d%H%M) 
             #fi
             bgcolor=red
             [ "x$status" == "xOK" ] && bgcolor="#90EE90" # green
             [ "x$status" == "xCRITICAL" ] && bgcolor=red
             [ "x$status" == "xWARNING" ] && bgcolor=orange
             [ "x$status" == "xUNKNOWN" ] && bgcolor=grey
             [ "x$status" == "x" ] && bgcolor=white
             m_name=$(echo $t  | sed 's#-/# #g' | awk '{print $1}')
             L=$(echo $(printf "$LEGEND\n" | grep $m_name | cut -d: -f1))
             #if [ "x$L" != "x" ] ; then
             if [ "x$status" == "x" ] ; then
                :
                #echo "<td bgcolor='$bgcolor'> <b><FONT color='yellow'> <a href='?test_howto=$L' target=_blank> $L </a> </FONT> </b> </td>" >> $inputs/$(echo $basename_0 | sed "s#.sh##")_${now_is}.html
                #status=NT
                #detail_link=SPARSE
                #echo "<td bgcolor='$bgcolor'><!-- a href='${detail_link}' target=_blank --> NT <!-- /a --><br/><FONT color='red'> $YmdHM <!-- $L --> </FONT> </td>" >> $inputs/$(echo $basename_0 | sed "s#.sh##")_${now_is}.html
             else
                if  [ "x$timestamp" == "x" ] ; then
                    status=SPARSE
                    detail_link=SPARSE
                #else
                   #sed -e "s#@@gte@@#$gte#" -e "s#@@lte@@#$lte#" -e "s#@@id@@#$id#" -e "s#@@thesite@@#$thesite#" -e "s#@@profile@@#$theprofile#" -e "s#@@size@@#$size#" -e "s#@@unique_f@@#$unique_f#" -e "s#@@tie_breakter_id@@#$tie_breaker_id#" $inputs/${sort_search_id_json}.in > $inputs/${sort_search_id_json}_${now_is}
                   #eval $(curl -H "Content-Type: application/x-ndjson" -H "Authorization: Bearer $(cat $inputs/token.txt)" -XGET https://monit-grafana.cern.ch/api/datasources/proxy/${DBID}/_msearch --data-binary "@$inputs/${sort_search_id_json}_${now_is}" 2>/dev/null | python -m json.tool | grep "\"metric_name\"\|\"timestamp\"" | sed "s#:#=#g" | sed "s# ##g" | sed 's#"##g' | sed "s#,##g" | head -2 | sed "s#timestamp=#thetimestamp=#g" | sed "s#/#__slash__#g" | sed "s#=#__equals__#g" | sed "s#metric_name__equals__#metric_name=#" | sed "s#thetimestamp__equals__#thetimestamp=#")
                
                   #detail_link="https://monit-grafana.cern.ch/d/siYq3DxZz/wlcg-sitemon-test-details?orgId=20&var-metric=${metric_name}&var-dst_hostname=${h}&var-timestamp=${thetimestamp}"
                   #detail_link=$(echo ${detail_link} | sed "s#__slash__#/#g" | sed "s#__equals__#=#g") # / is %2F = is %3D 
                fi
                #echo "<td bgcolor='$bgcolor'><a href='?test_id=$id&site=$thesite' target=_blank> $status </a><br/><FONT color='yellow'> T:$YmdHM <!-- $L --> </FONT> </td>"
                #echo "<td bgcolor='$bgcolor'><a href='${detail_link}' target=_blank> $status </a><br/><FONT color='yellow'> $YmdHM <!-- $L --> </FONT> </td>" >> $inputs/$(echo $basename_0 | sed "s#.sh##")_${now_is}.html
             fi
             if [ "x$status" != "xOK" ] ; then
                #error_message="$error_message\n[$sf][$h][$t] = $status ${detail_link_prefix}${id}\n"
                #error_message="$error_message\n[$sf][$h][$t] = $status ${webroot}/$(basename $0)?test_id=$id&site=$thesite\n${webroot}/$(basename $0)\n"
                #if [ "x$thesite" == "x$THESITE" ] ; then
                   error_message="$error_message\n[$sf][$h][$t] = $status \n${detail_link}\n${webroot}/$(basename $0)?test_id=$id&site=$thesite\n\n_id=$id metric_name=${metric_name} thetimestamp=$thetimestamp\n${detail_link}\n${webroot}/$(basename $0)?test_id=$id&site=$thesite\n${webroot}/$(basename $0)\n\nContent of input json\n$([ -f $inputs/${sort_search_id_json}_${now_is} ] && cat $inputs/${sort_search_id_json}_${now_is})"
                #fi
                #error_message_html="$error_message_html<br/>[$thesite][$sf][$h][$t] = $status <br/><a '${detail_link}'>${detail_link}</a><br/>"                
             fi
             #rm -f $inputs/${sort_search_id_json}_${now_is}
          done
          #echo "</tr>" >> $inputs/$(echo $basename_0 | sed "s#.sh##")_${now_is}.html
       done
done
if [ "x$error_message" != "x" ] ; then
   printf "$error_message\n"
fi
exit 0
#echo "</table>" >> $inputs/$(echo $basename_0 | sed "s#.sh##")_${now_is}.html
#echo "<br/>" >> $inputs/$(echo $basename_0 | sed "s#.sh##")_${now_is}.html
#done # for thesite in $sites

echo "<table>" >> $inputs/$(echo $basename_0 | sed "s#.sh##")_${now_is}.html
echo "<tr><td bgcolor='yellow'>Legend<td><td bgcolor='yellow' align='left'>Metric Name</td></tr>" >> $inputs/$(echo $basename_0 | sed "s#.sh##")_${now_is}.html
for l in $LEGEND ; do
   L=$(echo $l | cut -d: -f1)
   t=$(echo $l | cut -d: -f2)
   echo "<tr><td> $L </td><td align='left'> $t </td></tr>" >> $inputs/$(echo $basename_0 | sed "s#.sh##")_${now_is}.html

done
echo "</table>" >> $inputs/$(echo $basename_0 | sed "s#.sh##")_${now_is}.html
echo "Test numbers &gt; 17 are non-critical CMS tests" >> $inputs/$(echo $basename_0 | sed "s#.sh##")_${now_is}.html
echo "<br/>" >> $inputs/$(echo $basename_0 | sed "s#.sh##")_${now_is}.html
echo "<FONT size=3 color='green'> Extra Metric Names </FONT></br>" >> $inputs/$(echo $basename_0 | sed "s#.sh##")_${now_is}.html
echo "<FONT color='red'> $extra_metric_names </FONT>" >> $inputs/$(echo $basename_0 | sed "s#.sh##")_${now_is}.html
echo "</html>" >> $inputs/$(echo $basename_0 | sed "s#.sh##")_${now_is}.html

#echo error_message=$error_message
if [ "x$error_message" != "x" ] ; then
   #printf "$error_message\n"
   #printf "$(/bin/hostname -s) $(basename $0) SAM3 Test Alert\n$error_message\n" | mail -s "ERROR SAM3 Test Alert" $(echo $notifytowhom | sed "s#__AT__#@#" | sed "s#__dot__#\.#g")
   State=ERROR
   nline_error_message=$(printf "$error_message\n" | grep "$THESITE\|All CEs have at least number of tests" | wc -l)
   [ $nline_error_message -lt 3 ] && State=INFO
#echo DEBUG sending an email

(
   echo "To: "$(echo $notifytowhom | sed "s#__AT__#@#" | sed "s#__dot__#\.#g")
   echo "Subject: State=$State SAM3 Test Alert"
   echo "Content-Type: text/html"
   echo " Start of Content <br/> Number of Error Message Lines: $nline_error_message <br/>"
   printf "$error_message\n" | head -2
   sed -i 's#<html>#<!-- html -->#' $inputs/$(echo $basename_0 | sed "s#.sh##")_${now_is}.html
   echo "<html>"
   echo $(/bin/hostname -s) $(basename $0) SAM3 Test Alert "<br/>"
   echo ERROR MESSAGE $error_message
   echo "$error_message_html"
   echo "<br/>" 
   cat $inputs/$(echo $basename_0 | sed "s#.sh##")_${now_is}.html
   echo
) | /usr/sbin/sendmail -t
else
#echo DEBUG sending an email
#if [ $(expr $(date +%H) % $EVERY_X_HOUR) -eq 0 -a $(date +%M) -lt 15 ] ; then
(
   echo "To: "$(echo $notifytowhom | sed "s#__AT__#@#" | sed "s#__dot__#\.#g")
   echo "Subject: OK SAM3 Tests"
   echo "Content-Type: text/html"
   echo 
   
   cat $inputs/$(echo $basename_0 | sed "s#.sh##")_${now_is}.html
   echo
) # | /usr/sbin/sendmail -t
#fi
fi
rm -f $inputs/$(echo $basename_0 | sed "s#.sh##")_${now_is}.html
rm -f $inputs/${sitemon_agg_metric_json}_${now_is}
rm -f $inputs/${sort_search_json}_${now_is}
rm -f $inputs/${sort_search_after_json}_${now_is}
rm -f $inputs/$(basename $0 | sed "s#\.sh##").*.out_${now_is}

exit 0
####### BEGIN sort_search_json
{"search_type": "query_then_fetch", "index": ["monit_prod_sam3_enr_metric*"], "ignore_unavailable": true}
{"query": {"bool": {"filter": [{"range": {"metadata.timestamp": {"gte": "now-4h/h", "lte": "now", "format": "epoch_millis"}}}, {"query_string": {"analyze_wildcard": true, "query": "data.dst_experiment_site:@@thesite@@"}}]}}, "from": 0, "size": @@size@@, "sort": [{"@@unique_f@@": "desc"},{"@@tie_breakter_id@@": "asc"}]}
####### ENDIN sort_search_json
####### BEGIN sort_search_after_json
search_type": "query_then_fetch", "index": ["monit_prod_sam3_enr_metric*"], "ignore_unavailable": true}
{"query": {"bool": {"filter": [{"range": {"metadata.timestamp": {"gte": "@@gte@@", "lte": "@@lte@@", "format": "epoch_millis"}}}, {"query_string": {"analyze_wildcard": true, "query": "data.dst_experiment_site:@@thesite@@"}}]}}, "from": 0, "size": @@size@@, "search_after": [@@search_after@@], "sort": [{"@@unique_f@@": "desc"},{"@@tie_breakter_id@@": "asc"}]}
####### ENDIN sort_search_after_json
####### BEGIN token_txt
eyJrIjoieEZVYUtzcGkyVnVSaUlUOTRnd3RKWEtPdFRYUDdXQnQiLCJuIjoiY21zLWJvb2Nram9vMyIsImlkIjoxMX0=
####### ENDIN token_txt
####### BEGIN Functions 12345
# Functions
function readme_org__dot__cms__dot__WN__dash__analysis () {
   echo "[0] Go to the WN where the test failed"
   echo "ssh cmsuser@wn"
   echo ""
   echo "[1] Download SAM Test if not "
   echo "cd"
   echo "git clone https://gitlab.cern.ch/etf/cmssam.git"
   echo ""
   echo "[2] Setup and Run the test"
   echo source /cvmfs/oasis.opensciencegrid.org/osg-software/osg-wn-client/current/el7-x86_64/setup.sh
   echo export X509_CERT_DIR=/cvmfs/cms.cern.ch/grid/etc/grid-security/certificates
   echo export X509_USER_PROXY=\$X509_USER_PROXY # for example X509_USER_PROXY=/tmp/x509up_u11234567890
   echo export SAME_SENSOR_HOME=\$HOME/cmssam/SiteTests/testjob
   echo \$SAME_SENSOR_HOME/tests/CE-cms-analysis.sing
   echo ""
   echo "[3] References"
   echo "{1} <a href='https://gitlab.cern.ch/etf/cmssam/-/tree/master' target=_blank> SAM Test Scripts </a>"
   echo "{2} <a href='https://twiki.cern.ch/twiki/bin/view/CMSPublic/CompOpsSAMTests' target=_blank> CompOpsSAMTests </a>"
}

function readme_org__dot__cms__dot__WN__dash__basic () {
   echo "[0] Go to the WN where the test failed"
   echo "ssh cmsuser@wn"
   echo ""
   echo "[1] Download SAM Test if not "
   echo "cd"
   echo "git clone https://gitlab.cern.ch/etf/cmssam.git"
   echo ""
   echo "[2] Setup and Run the test"
   echo source /cvmfs/oasis.opensciencegrid.org/osg-software/osg-wn-client/current/el7-x86_64/setup.sh
   echo export X509_CERT_DIR=/cvmfs/cms.cern.ch/grid/etc/grid-security/certificates
   echo export X509_USER_PROXY=\$X509_USER_PROXY # for example X509_USER_PROXY=/tmp/x509up_u11234567890
   echo export SAME_SENSOR_HOME=\$HOME/cmssam/SiteTests/testjob
   echo \$SAME_SENSOR_HOME/tests/CE-cms-basic
   echo ""
   echo "[3] References"
   echo "{1} <a href='https://gitlab.cern.ch/etf/cmssam/-/tree/master' target=_blank> SAM Test Scripts </a>"
   echo "{2} <a href='https://twiki.cern.ch/twiki/bin/view/CMSPublic/CompOpsSAMTests' target=_blank> CompOpsSAMTests </a>"
}

function readme_org__dot__cms__dot__WN__dash__env () {
   echo "[0] Go to the WN where the test failed"
   echo "ssh cmsuser@wn"
   echo ""
   echo "[1] Download SAM Test if not "
   echo "cd"
   echo "git clone https://gitlab.cern.ch/etf/cmssam.git"
   echo ""
   echo "[2] Setup and Run the test"
   echo source /cvmfs/oasis.opensciencegrid.org/osg-software/osg-wn-client/current/el7-x86_64/setup.sh
   echo export X509_CERT_DIR=/cvmfs/cms.cern.ch/grid/etc/grid-security/certificates
   echo export X509_USER_PROXY=\$X509_USER_PROXY # for example X509_USER_PROXY=/tmp/x509up_u11234567890
   echo export SAME_SENSOR_HOME=\$HOME/cmssam/SiteTests/testjob
   echo \$SAME_SENSOR_HOME/tests/CE-cms-env
   echo ""
   echo "[3] References"
   echo "{1} <a href='https://gitlab.cern.ch/etf/cmssam/-/tree/master' target=_blank> SAM Test Scripts </a>"
   echo "{2} <a href='https://twiki.cern.ch/twiki/bin/view/CMSPublic/CompOpsSAMTests' target=_blank> CompOpsSAMTests </a>"
}

function readme_org__dot__cms__dot__WN__dash__isolation () { #10
   echo "[0] Go to the WN where the test failed"
   echo "ssh cmsuser@wn"
   echo ""
   echo "[1] Download SAM Test if not "
   echo "cd"
   
   echo "git clone https://gitlab.cern.ch/etf/cmssam.git"
   echo ""
   echo "[2] Setup and Run the test"
   echo source /cvmfs/oasis.opensciencegrid.org/osg-software/osg-wn-client/current/el7-x86_64/setup.sh
   echo export X509_CERT_DIR=/cvmfs/cms.cern.ch/grid/etc/grid-security/certificates
   echo export X509_USER_PROXY=\$X509_USER_PROXY # for example X509_USER_PROXY=/tmp/x509up_u11234567890
   echo export SAME_SENSOR_HOME=\$HOME/cmssam/SiteTests/testjob
   echo \$SAME_SENSOR_HOME/tests/CE-cms-isolation
   echo ""
   echo "[3] References"
   echo "{1} <a href='https://gitlab.cern.ch/etf/cmssam/-/tree/master' target=_blank> SAM Test Scripts </a>"
   echo "{2} <a href='https://twiki.cern.ch/twiki/bin/view/CMSPublic/CompOpsSAMTests' target=_blank> CompOpsSAMTests </a>"
}

function readme_org__dot__cms__dot__WN__dash__squid () { #1
   echo "[0] Go to the WN where the test failed"
   echo "ssh cmsuser@wn"
   echo ""
   echo "[1] Download SAM Test if not "
   echo "cd"
   echo "git clone https://gitlab.cern.ch/etf/cmssam.git"
   echo ""
   echo "[2] Setup and Run the test"
   echo source /cvmfs/oasis.opensciencegrid.org/osg-software/osg-wn-client/current/el7-x86_64/setup.sh
   echo export X509_CERT_DIR=/cvmfs/cms.cern.ch/grid/etc/grid-security/certificates
   echo export X509_USER_PROXY=\$X509_USER_PROXY # for example X509_USER_PROXY=/tmp/x509up_u11234567890
   echo export SAME_SENSOR_HOME=\$HOME/cmssam/SiteTests/testjob
   echo "[ -f \$SAME_SENSOR_HOME/tests/CE-cms-squid ] || cp -pR \$SAME_SENSOR_HOME/../FroNtier/tests/CE-cms-squid \$SAME_SENSOR_HOME/tests"
   echo "[ -f \$SAME_SENSOR_HOME/tests/test_frontier.py ] || cp -pR  \$SAME_SENSOR_HOME/../FroNtier/tests/test_frontier.py \$SAME_SENSOR_HOME/tests"
   echo \$SAME_SENSOR_HOME/../FroNtier/tests/CE-cms-squid.sing   
   echo ""
   echo "[3] References"
   echo "{1} <a href='https://gitlab.cern.ch/etf/cmssam/-/tree/master' target=_blank> SAM Test Scripts </a>"
   echo "{2} <a href='https://twiki.cern.ch/twiki/bin/view/CMSPublic/CompOpsSAMTests' target=_blank> CompOpsSAMTests </a>"
}

function readme_org__dot__cms__dot__WN__dash__frontier () { #2
   echo "[0] Go to the WN where the test failed"
   echo "ssh cmsuser@wn"
   echo ""
   echo "[1] Download SAM Test if not "
   echo "cd"
   echo "git clone https://gitlab.cern.ch/etf/cmssam.git"
   echo ""
   echo "[2] Setup and Run the test"
   echo source /cvmfs/oasis.opensciencegrid.org/osg-software/osg-wn-client/current/el7-x86_64/setup.sh
   echo export X509_CERT_DIR=/cvmfs/cms.cern.ch/grid/etc/grid-security/certificates
   echo export X509_USER_PROXY=\$X509_USER_PROXY # for example X509_USER_PROXY=/tmp/x509up_u11234567890
   echo export SAME_SENSOR_HOME=\$HOME/cmssam/SiteTests/testjob
   echo "[ -f \$SAME_SENSOR_HOME/tests/CE-cms-frontier ] || cp -pR \$SAME_SENSOR_HOME/../FroNtier/tests/CE-cms-frontier \$SAME_SENSOR_HOME/tests"
   echo "[ -f \$SAME_SENSOR_HOME/tests/CMSSW_frontier.sh ] || cp -pR  \$SAME_SENSOR_HOME/../FroNtier/tests/CMSSW_frontier.sh \$SAME_SENSOR_HOME/tests"
   echo \$SAME_SENSOR_HOME/../FroNtier/tests/CE-cms-frontier.sing   
   echo ""
   echo "[3] References"
   echo "{1} <a href='https://gitlab.cern.ch/etf/cmssam/-/tree/master' target=_blank> SAM Test Scripts </a>"
   echo "{2} <a href='https://twiki.cern.ch/twiki/bin/view/CMSPublic/CompOpsSAMTests' target=_blank> CompOpsSAMTests </a>"
}

function readme_org__dot__cms__dot__WN__dash__xrootd__dash__access () { #5
   echo "[0] Go to the WN where the test failed"
   echo "ssh cmsuser@wn"
   echo ""
   echo "[1] Download SAM Test if not "
   echo "cd"
   
   echo "git clone https://gitlab.cern.ch/etf/cmssam.git"
   echo ""
   echo "[2] Setup and Run the test"
   echo source /cvmfs/oasis.opensciencegrid.org/osg-software/osg-wn-client/current/el7-x86_64/setup.sh
   echo export X509_CERT_DIR=/cvmfs/cms.cern.ch/grid/etc/grid-security/certificates
   echo export X509_USER_PROXY=\$X509_USER_PROXY # for example X509_USER_PROXY=/tmp/x509up_u11234567890
   echo export SAME_SENSOR_HOME=\$HOME/cmssam/SiteTests/testjob
   echo \$SAME_SENSOR_HOME/tests/CE-cms-xrootd-access.sing
   echo ""
   echo "[3] References"
   echo "{1} <a href='https://gitlab.cern.ch/etf/cmssam/-/tree/master' target=_blank> SAM Test Scripts </a>"
   echo "{2} <a href='https://twiki.cern.ch/twiki/bin/view/CMSPublic/CompOpsSAMTests' target=_blank> CompOpsSAMTests </a>"
}

function readme_org__dot__cms__dot__WN__dash__xrootd__dash__fallback () { #7
   echo "[0] Go to the WN where the test failed"
   echo "ssh cmsuser@wn"
   echo ""
   echo "[1] Download SAM Test if not "
   echo "cd"
   
   echo "git clone https://gitlab.cern.ch/etf/cmssam.git"
   echo ""
   echo "[2] Setup and Run the test"
   echo source /cvmfs/oasis.opensciencegrid.org/osg-software/osg-wn-client/current/el7-x86_64/setup.sh
   echo export X509_CERT_DIR=/cvmfs/cms.cern.ch/grid/etc/grid-security/certificates
   echo export X509_USER_PROXY=\$X509_USER_PROXY # for example X509_USER_PROXY=/tmp/x509up_u11234567890
   echo export SAME_SENSOR_HOME=\$HOME/cmssam/SiteTests/testjob
   echo \$SAME_SENSOR_HOME/tests/CE-cms-xrootd-fallback.sing
   echo ""
   echo "[3] References"
   echo "{1} <a href='https://gitlab.cern.ch/etf/cmssam/-/tree/master' target=_blank> SAM Test Scripts </a>"
   echo "{2} <a href='https://twiki.cern.ch/twiki/bin/view/CMSPublic/CompOpsSAMTests' target=_blank> CompOpsSAMTests </a>"
}

function readme_org__dot__cms__dot__WN__dash__mc () { #8
   echo "[0] Go to the WN where the test failed"
   echo "ssh cmsuser@wn"
   echo ""
   echo "[1] Download SAM Test if not "
   echo "cd"
   echo "git clone https://gitlab.cern.ch/etf/cmssam.git"
   echo ""
   echo "[2] Setup and Run the test"
   echo source /cvmfs/oasis.opensciencegrid.org/osg-software/osg-wn-client/current/el7-x86_64/setup.sh
   echo export X509_CERT_DIR=/cvmfs/cms.cern.ch/grid/etc/grid-security/certificates
   echo export X509_USER_PROXY=\$X509_USER_PROXY # for example X509_USER_PROXY=/tmp/x509up_u11234567890
   echo export SAME_SENSOR_HOME=\$HOME/cmssam/SiteTests/testjob
   echo "[ -f \$SAME_SENSOR_HOME/tests/CE-cms-mc ] || cp -pR \$SAME_SENSOR_HOME/../MonteCarlo/tests/CE-cms-mc \$SAME_SENSOR_HOME/tests"
   echo "[ -d \$SAME_SENSOR_HOME/cms-MC-test ] || cp -pR \$SAME_SENSOR_HOME/../MonteCarlo/cms-MC-test \$SAME_SENSOR_HOME/"
   echo \$SAME_SENSOR_HOME/../MonteCarlo/tests/CE-cms-mc.sing   
   echo ""
   echo "[3] References"
   echo "{1} <a href='https://gitlab.cern.ch/etf/cmssam/-/tree/master' target=_blank> SAM Test Scripts </a>"
   echo "{2} <a href='https://twiki.cern.ch/twiki/bin/view/CMSPublic/CompOpsSAMTests' target=_blank> CompOpsSAMTests </a>"
}

function readme_org__dot__sam__dot__CONDOR__dash__JobSubmit () { #12
   echo "CASE: htcondor"
   echo "[0] Go to a condor-g submission machine"
   echo "[1] Creat a job submission file, e.g., nagrun.sub with the following content"
   cat $inputs/nagrun.sub
   echo 
   echo "[2] Prepare the executable and inputs"
   echo "cd"
   echo "mkdir JobSubmit/samjob"
   echo "cd JobSubmit/samjob"
   echo "for f in nagrun.sub nagrun.sh gridjob.tgz wnlogs.tgz ; do"
   echo "    gfal-copy -r -p gsiftp://cmsio.rc.ufl.edu/cmsuf/t2/operations/samjob/$f ./"
   echo "done"
   echo 
   echo cd ..
   echo source /cvmfs/oasis.opensciencegrid.org/osg-software/osg-wn-client/current/el7-x86_64/setup.sh
   echo export X509_CERT_DIR=/cvmfs/cms.cern.ch/grid/etc/grid-security/certificates
   echo export X509_USER_PROXY=\$X509_USER_PROXY # for example X509_USER_PROXY=/tmp/x509up_u11234567890
   echo "condor_submit nagrun.sub"
   echo "watch condor_q"
   echo "echo Check samjob/gridjob.{out,err,log} and wnlogs.tgz"
   echo "echo The content of samjob/gridjob.out should be same as the output from the actual SAM CONDOR-JobSubmit test"


}

function readme_org__dot__cms__dot__SRM__dash__GetPFNFromTFC () { #4
   echo "[0] Go to a SAM machine with a grid UI"
   echo "ssh cmsuser@wn"
   echo ""
   echo "[1] Download SAM Test if not "
   echo "cd"
   echo "git clone https://gitlab.cern.ch/etf/cmssam.git"
   echo ""
   echo "[2] Setup and Run the test"
   echo export X509_CERT_DIR=/cvmfs/cms.cern.ch/grid/etc/grid-security/certificates
   echo export X509_USER_PROXY=\$X509_USER_PROXY # for example X509_USER_PROXY=/tmp/x509up_u11234567890
   echo export SAME_SENSOR_HOME=\$HOME/cmssam/SiteTests/testjob
   echo "echo Download gridmon"
   echo cd \$SAME_SENSOR_HOME/../SRMv2/tests
   echo "[ -d python-GridMon ] || { echo Download gridmon ; git clone https://github.com/ARGOeu/python-GridMon.git ; } ;"
   echo "[ -d gridmon ] || ln -s python-GridMon/gridmon"
   echo "export PYTHONPATH=\$PYTHONPATH:\$SAME_SENSOR_HOME/../SRMv2/tests # to import simplejson and gridmon"
   echo "[ -w  /var/lib/gridprobes ] || sudo /bin/bash -c \"[ -d  /var/lib/gridprobes ] || mkdir /var/lib/gridprobes ; chown \$(id -un):\$(id -gn) /var/lib/gridprobes\""

   echo \$SAME_SENSOR_HOME/../SE/srmvometrics.py -H cmsio.rc.ufl.edu -m org.cms.SRM-GetPFNFromTFC
   echo ""
   echo "[3] References"
   echo "{1} <a href='https://gitlab.cern.ch/etf/cmssam/-/tree/master' target=_blank> SAM Test Scripts </a>"
   echo "{2} <a href='https://twiki.cern.ch/twiki/bin/view/CMSPublic/CompOpsSAMTests' target=_blank> CompOpsSAMTests </a>"
   echo "{3} <a href='https://github.com/ARGOeu/python-GridMon>python-GridMon</a>"
   echo "{4} <a href='https://gitlab.cern.ch/etf/cmssam/-/blob/master/nagios/grid-monitoring-probes-org.cms-etf.spec'>Packages List</a>"
}

function readme_org__dot__cms__dot__SRM__dash__VOPut () { #11
   echo "[0] Go to a SAM machine with a grid UI"
   echo "ssh cmsuser@wn"
   echo ""
   echo "[1] Download SAM Test if not "
   echo "cd"
   echo "git clone https://gitlab.cern.ch/etf/cmssam.git"
   echo ""
   echo "[2] Setup and Run the test"
   echo export X509_CERT_DIR=/cvmfs/cms.cern.ch/grid/etc/grid-security/certificates
   echo export X509_USER_PROXY=\$X509_USER_PROXY # for example X509_USER_PROXY=/tmp/x509up_u11234567890
   echo export SAME_SENSOR_HOME=\$HOME/cmssam/SiteTests/testjob
   echo "echo Download gridmon"
   echo cd \$SAME_SENSOR_HOME/../SRMv2/tests
   echo "[ -d python-GridMon ] || { echo Download gridmon ; git clone https://github.com/ARGOeu/python-GridMon.git ; } ;"
   echo "[ -d gridmon ] || ln -s python-GridMon/gridmon"
   echo "export PYTHONPATH=\$PYTHONPATH:\$SAME_SENSOR_HOME/../SRMv2/tests # to import simplejson and gridmon"
   echo "[ -w  /var/lib/gridprobes ] || sudo /bin/bash -c \"[ -d  /var/lib/gridprobes ] || mkdir /var/lib/gridprobes ; chown \$(id -un):\$(id -gn) /var/lib/gridprobes ; [ -f /var/lib/gridprobes/ops/org.cms/SRM/cmsio.rc.ufl.edu ] || mkdir -p /var/lib/gridprobes/ops/org.cms/SRM/cmsio.rc.ufl.edu ; touch /var/lib/gridprobes/ops/org.cms/SRM/cmsio.rc.ufl.edu/testFileIn.txt\""

   echo \$SAME_SENSOR_HOME/../SE/srmvometrics.py -H cmsio.rc.ufl.edu -m org.cms.SRM-VOPut
   echo ""
   echo "[3] References"
   echo "{1} <a href='https://gitlab.cern.ch/etf/cmssam/-/tree/master' target=_blank> SAM Test Scripts </a>"
   echo "{2} <a href='https://twiki.cern.ch/twiki/bin/view/CMSPublic/CompOpsSAMTests' target=_blank> CompOpsSAMTests </a>"
   echo "{3} <a href='https://github.com/ARGOeu/python-GridMon>python-GridMon</a>"
   echo "{4} <a href='https://gitlab.cern.ch/etf/cmssam/-/blob/master/nagios/grid-monitoring-probes-org.cms-etf.spec'>Packages List</a>"
}

function readme_org__dot__cms__dot__SRM__dash__VOGet () { #15
   echo "[0] Go to a SAM machine with a grid UI"
   echo "ssh cmsuser@wn"
   echo ""
   echo "[1] Download SAM Test if not "
   echo "cd"
   echo "git clone https://gitlab.cern.ch/etf/cmssam.git"
   echo ""
   echo "[2] Setup and Run the test"
   echo export X509_CERT_DIR=/cvmfs/cms.cern.ch/grid/etc/grid-security/certificates
   echo export X509_USER_PROXY=\$X509_USER_PROXY # for example X509_USER_PROXY=/tmp/x509up_u11234567890
   echo export SAME_SENSOR_HOME=\$HOME/cmssam/SiteTests/testjob
   echo "echo Download gridmon"
   echo cd \$SAME_SENSOR_HOME/../SRMv2/tests
   echo "[ -d python-GridMon ] || { echo Download gridmon ; git clone https://github.com/ARGOeu/python-GridMon.git ; } ;"
   echo "[ -d gridmon ] || ln -s python-GridMon/gridmon"
   echo "export PYTHONPATH=\$PYTHONPATH:\$SAME_SENSOR_HOME/../SRMv2/tests # to import simplejson and gridmon"
   echo "[ -w  /var/lib/gridprobes ] || sudo /bin/bash -c \"[ -d  /var/lib/gridprobes ] || mkdir /var/lib/gridprobes ; chown \$(id -un):\$(id -gn) /var/lib/gridprobes ; [ -f /var/lib/gridprobes/ops/org.cms/SRM/cmsio.rc.ufl.edu ] || mkdir -p /var/lib/gridprobes/ops/org.cms/SRM/cmsio.rc.ufl.edu ; touch /var/lib/gridprobes/ops/org.cms/SRM/cmsio.rc.ufl.edu/testFileIn.txt\""

   echo \$SAME_SENSOR_HOME/../SE/srmvometrics.py -H cmsio.rc.ufl.edu -m org.cms.SRM-VOGet
   echo ""
   echo "[3] References"
   echo "{1} <a href='https://gitlab.cern.ch/etf/cmssam/-/tree/master' target=_blank> SAM Test Scripts </a>"
   echo "{2} <a href='https://twiki.cern.ch/twiki/bin/view/CMSPublic/CompOpsSAMTests' target=_blank> CompOpsSAMTests </a>"
   echo "{3} <a href='https://github.com/ARGOeu/python-GridMon>python-GridMon</a>"
   echo "{4} <a href='https://gitlab.cern.ch/etf/cmssam/-/blob/master/nagios/grid-monitoring-probes-org.cms-etf.spec'>Packages List</a>"
}

function readme_org__dot__cms__dot__SE__dash__xrootd__dash__connection () { #6
   echo "[0] Go to a SAM machine with a grid UI (<FONT color='red'>an lxplus machine is better for this test</FONT>)"
   echo "ssh cmsuser@wn"
   echo ""
   echo "[1] Download SAM Test if not "
   echo "cd"
   echo "git clone https://gitlab.cern.ch/etf/cmssam.git"
   echo ""
   echo "[2] Setup and Run the test"
   echo "vi \$X509_USER_PROXY # as needed copy \$X509_USER_PROXY from local grid proxy generating machine and paste its content here."
   echo export X509_CERT_DIR=/cvmfs/cms.cern.ch/grid/etc/grid-security/certificates
   echo export X509_USER_PROXY=\$X509_USER_PROXY # for example X509_USER_PROXY=/tmp/x509up_u11234567890
   echo export SAME_SENSOR_HOME=\$HOME/cmssam/SiteTests/testjob
   echo "python -c 'from XRootD import client' 2>/dev/null || sudo /bin/bash -c \"yum install -y python-xrootd\""
   echo "export PYTHONPATH=\$PYTHONPATH:\$SAME_SENSOR_HOME/../SRMv2/tests/nap"
   echo "cd \$SAME_SENSOR_HOME/../SRMv2/tests/nap # the test python requires nap from https://gitlab.cern.ch:8443/etf/nap"
   echo \$SAME_SENSOR_HOME/../SE/cmssam_xrootd_endpnt.py -H cmsio5.rc.ufl.edu -P 1094 -S T2_US_Florida -4 -C /dev/null -d
   echo ""
   echo "[3] References"
   echo "{1} <a href='https://gitlab.cern.ch/etf/cmssam/-/tree/master' target=_blank> SAM Test Scripts </a>"
   echo "{2} <a href='https://twiki.cern.ch/twiki/bin/view/CMSPublic/CompOpsSAMTests' target=_blank> CompOpsSAMTests </a>"
   echo "{3} <a href='https://gitlab.cern.ch/etf/cmssam/-/blob/master/nagios/grid-monitoring-probes-org.cms-etf.spec'>Packages List</a>"
}

function readme_org__dot__cms__dot__SE__dash__xrootd__dash__contain () { #14
   echo "[0] Go to a SAM machine with a grid UI (<FONT color='red'>an lxplus machine is better for this test</FONT>)"
   echo "ssh cmsuser@wn"
   echo ""
   echo "[1] Download SAM Test if not "
   echo "cd"
   echo "git clone https://gitlab.cern.ch/etf/cmssam.git"
   echo ""
   echo "[2] Setup and Run the test"
   echo "vi \$X509_USER_PROXY # as needed copy \$X509_USER_PROXY from local grid proxy generating machine and paste its content here."
   echo export X509_CERT_DIR=/cvmfs/cms.cern.ch/grid/etc/grid-security/certificates
   echo export X509_USER_PROXY=\$X509_USER_PROXY # for example X509_USER_PROXY=/tmp/x509up_u11234567890
   echo export SAME_SENSOR_HOME=\$HOME/cmssam/SiteTests/testjob
   echo "python -c 'from XRootD import client' 2>/dev/null || sudo /bin/bash -c \"yum install -y python-xrootd\""
   echo "export PYTHONPATH=\$PYTHONPATH:\$SAME_SENSOR_HOME/../SRMv2/tests/nap"
   echo "cd \$SAME_SENSOR_HOME/../SRMv2/tests/nap # the test python requires nap from https://gitlab.cern.ch:8443/etf/nap"
   echo \$SAME_SENSOR_HOME/../SE/cmssam_xrootd_endpnt.py -H cmsio5.rc.ufl.edu -P 1094 -S T2_US_Florida -4 -C /dev/null -d
   echo ""
   echo "[3] References"
   echo "{1} <a href='https://gitlab.cern.ch/etf/cmssam/-/tree/master' target=_blank> SAM Test Scripts </a>"
   echo "{2} <a href='https://twiki.cern.ch/twiki/bin/view/CMSPublic/CompOpsSAMTests' target=_blank> CompOpsSAMTests </a>"
   echo "{3} <a href='https://gitlab.cern.ch/etf/cmssam/-/blob/master/nagios/grid-monitoring-probes-org.cms-etf.spec'>Packages List</a>"
}

function readme_org__dot__cms__dot__SE__dash__xrootd__dash__read () { #17
   echo "[0] Go to a SAM machine with a grid UI (<FONT color='red'>an lxplus machine is better for this test</FONT>)"
   echo "ssh cmsuser@wn"
   echo ""
   echo "[1] Download SAM Test if not "
   echo "cd"
   echo "git clone https://gitlab.cern.ch/etf/cmssam.git"
   echo ""
   echo "[2] Setup and Run the test"
   echo "vi \$X509_USER_PROXY # as needed copy \$X509_USER_PROXY from local grid proxy generating machine and paste its content here."
   echo export X509_CERT_DIR=/cvmfs/cms.cern.ch/grid/etc/grid-security/certificates
   echo export X509_USER_PROXY=\$X509_USER_PROXY # for example X509_USER_PROXY=/tmp/x509up_u11234567890
   echo export SAME_SENSOR_HOME=\$HOME/cmssam/SiteTests/testjob
   echo "python -c 'from XRootD import client' 2>/dev/null || sudo /bin/bash -c \"yum install -y python-xrootd\""
   echo "export PYTHONPATH=\$PYTHONPATH:\$SAME_SENSOR_HOME/../SRMv2/tests/nap"
   echo "cd \$SAME_SENSOR_HOME/../SRMv2/tests/nap # the test python requires nap from https://gitlab.cern.ch:8443/etf/nap"
   echo \$SAME_SENSOR_HOME/../SE/cmssam_xrootd_endpnt.py -H cmsio5.rc.ufl.edu -P 1094 -S T2_US_Florida -4 -C /dev/null -d
   echo ""
   echo "[3] References"
   echo "{1} <a href='https://gitlab.cern.ch/etf/cmssam/-/tree/master' target=_blank> SAM Test Scripts </a>"
   echo "{2} <a href='https://twiki.cern.ch/twiki/bin/view/CMSPublic/CompOpsSAMTests' target=_blank> CompOpsSAMTests </a>"
   echo "{3} <a href='https://gitlab.cern.ch/etf/cmssam/-/blob/master/nagios/grid-monitoring-probes-org.cms-etf.spec'>Packages List</a>"
}

function readme_org__dot__cms__dot__SE__dash__xrootd__dash__version () { #16
   echo "[0] Go to a SAM machine with a grid UI (<FONT color='red'>an lxplus machine is better for this test</FONT>)"
   echo "ssh cmsuser@wn"
   echo ""
   echo "[1] Download SAM Test if not "
   echo "cd"
   echo "git clone https://gitlab.cern.ch/etf/cmssam.git"
   echo ""
   echo "[2] Setup and Run the test"
   echo "vi \$X509_USER_PROXY # as needed copy \$X509_USER_PROXY from local grid proxy generating machine and paste its content here."
   echo export X509_CERT_DIR=/cvmfs/cms.cern.ch/grid/etc/grid-security/certificates
   echo export X509_USER_PROXY=\$X509_USER_PROXY # for example X509_USER_PROXY=/tmp/x509up_u11234567890
   echo export SAME_SENSOR_HOME=\$HOME/cmssam/SiteTests/testjob
   echo "python -c 'from XRootD import client' 2>/dev/null || sudo /bin/bash -c \"yum install -y python-xrootd\""
   echo "export PYTHONPATH=\$PYTHONPATH:\$SAME_SENSOR_HOME/../SRMv2/tests/nap"
   echo "cd \$SAME_SENSOR_HOME/../SRMv2/tests/nap # the test python requires nap from https://gitlab.cern.ch:8443/etf/nap"
   echo \$SAME_SENSOR_HOME/../SE/cmssam_xrootd_endpnt.py -H cmsio5.rc.ufl.edu -P 1094 -S T2_US_Florida -4 -C /dev/null -d
   echo ""
   echo "[3] References"
   echo "{1} <a href='https://gitlab.cern.ch/etf/cmssam/-/tree/master' target=_blank> SAM Test Scripts </a>"
   echo "{2} <a href='https://twiki.cern.ch/twiki/bin/view/CMSPublic/CompOpsSAMTests' target=_blank> CompOpsSAMTests </a>"
   echo "{3} <a href='https://gitlab.cern.ch/etf/cmssam/-/blob/master/nagios/grid-monitoring-probes-org.cms-etf.spec'>Packages List</a>"
}

function print_test_output () {
   id=$1
   thesite=$2
   now_is=$(date +%s)_${thesite}
   sed -e "s#@@thesite@@#$thesite#" -e "s#@@profile@@#$theprofile#" -e "s#@@size@@#$size#" -e "s#@@unique_f@@#$unique_f#" -e "s#@@tie_breakter_id@@#$tie_breaker_id#" -e "s|@@id@@|$id|" $inputs/${search_details}.in > ${search_details}_${now_is}
   echo "<html>"
   curl -H "Content-Type: application/x-ndjson" -H "Authorization: Bearer $(cat $inputs/token.txt)" -XGET https://monit-grafana.cern.ch/api/datasources/proxy/${DBID}/_msearch --data-binary "@${search_details}_${now_is}" 2>/dev/null | sed 's#"data":#\n"data":#g'  | sed 's#,"#,\n"#g' | grep ^\"details\" | cut -d\" -f4- | sed 's|",||'
   echo "</html>"
   rm -f ${search_details}_${now_is}
}

####### ENDIN Functions 12345
