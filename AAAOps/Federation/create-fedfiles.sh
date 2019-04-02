#!/bin/bash

PROD_hosts=/opt/TransferTeam/AAAOps/Federation/in/prod.txt
TRANS_hosts=/opt/TransferTeam/AAAOps/Federation/in/trans.txt
FED_json=/opt/TransferTeam/AAAOps/Federation/out/federations.json
ALLOW_EU=/opt/TransferTeam/AAAOps/Federation/out/list_eu.allow

export X509_USER_PROXY=/root/.globus/slsprobe.proxy

. /opt/TransferTeam/AAAOps/Federation/create_allow-list.sh

if [ ! -r $ALLOW_EU ]; then
	echo "We have a problem with creating allow list.\n"
	exit 1
fi

if [ ! -r $PROD_hosts ] || [ ! -r $TRANS_hosts ]; then
	echo "We have problems with input files. \n"	
	echo $CMS_topology "\t" $PROD_hosts "\t" $TRANS_prod
	exit 1
fi

python /opt/TransferTeam/AAAOps/Federation/create_fedmaps_DEV.py

if [ ! -r $FED_json ]; then
	echo "We have a problem creating JSON file.\n"
	exit 1
fi
cp /opt/TransferTeam/AAAOps/Federation/out/* /var/www/html/aaa-fedinfo/

exit 0;
