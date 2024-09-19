#!/bin/bash
if [ $# -lt 1 ] ; then
   echo ERROR: $(basename $0) TX__YY_ZZZZ
   exit 1
fi
site=$1
THEPATH=/opt/TransferTeam/AAAOps/FedProbeSendAAAMetrics
export GRAFANA_VIEWER_TOKEN=$(echo $(cat $THEPATH/token.txt))
python /opt/TransferTeam/AAAOps/FedProbeSendAAAMetrics/siteLifeStatus.py $site
