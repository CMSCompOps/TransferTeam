#!/bin/bash

PROD_hosts=/root/FederationInfo/in/prod.txt
TRANS_hosts=/root/FederationInfo/in/trans.txt
FED_json=/root/FederationInfo/out/federations.json
ALLOW_EU=/root/FederationInfo/out/list_eu.allow

export X509_USER_PROXY=/root/.globus/slsprobe.proxy

./FederationInfo/create_allow-list.sh

if [ ! -r $ALLOW_EU ]; then
	echo "We have a problem with creating allow list.\n"
	exit 1
fi

if [ ! -r $PROD_hosts ] || [ ! -r $TRANS_hosts ]; then
	echo "We have problems with input files. \n"	
	echo $CMS_topology "\t" $PROD_hosts "\t" $TRANS_prod
	exit 1
fi

python /root/FederationInfo/create_fedmaps_DEV.py

if [ ! -r $FED_json ]; then
	echo "We have a problem creating JSON file.\n"
	exit 1
fi
cp /root/FederationInfo/out/* /var/www/html/fedinfo/

exit 0;
