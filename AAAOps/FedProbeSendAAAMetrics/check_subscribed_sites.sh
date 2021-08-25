#!/bin/bash
what=Production
[ $# -gt 0 ] && what=$1
sites=$(grep "$what" /opt/TransferTeam/AAAOps/FedProbeSendAAAMetrics/fed.json  | awk '{print $3}' | sort -u)
printf "$sites\n"
echo "Count: $(echo $sites | wc -w)"

