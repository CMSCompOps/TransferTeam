#!/bin/bash
if [ $# -lt 1 ] ; then
   echo ERROR: $(basename $0) TX__YY_ZZZZ
   exit 1
fi
sites=$1
THEPATH=/opt/TransferTeam/AAAOps/FedProbeSendAAAMetrics
export GRAFANA_VIEWER_TOKEN=$(echo $(cat $THEPATH/token.txt))
if [ $(echo $sites | grep -q T ; echo $?) -eq 0 ] ; then
   python /opt/TransferTeam/AAAOps/FedProbeSendAAAMetrics/siteLifeStatus.py $sites
else
   for site in $(echo /cvmfs/cms.cern.ch/SITECONF/T[1-2]* ) ; do
       s=$(echo $site | cut -d/ -f5)
       echo $s LifeStatus=$(python /opt/TransferTeam/AAAOps/FedProbeSendAAAMetrics/siteLifeStatus.py $s 2>/dev/null )
   done
fi
