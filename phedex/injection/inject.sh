#!/bin/bash

xml=`cat $1`
curl  --cert $X509_USER_PROXY --key $X509_USER_PROXY -k -d "node=T2_US_UCSD" -d "data=$xml" https://cmsweb.cern.ch/phedex/datasvc/xml/prod/inject
