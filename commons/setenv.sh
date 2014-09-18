#!/bin/bash
# without trailing slash
PHEDEX_DIR=~/phedex/PHEDEX-micro
CMSSW_DIR=~/CMSSW_6_2_3
DBS3_DIR=~/dbs3-client/slc5_amd64_gcc461/cms/dbs3-client/3.1.8

voms-proxy-init -voms cms --valid 240:0
export X509_USER_PROXY=/tmp/x509up_u$(id -u)

source $PHEDEX_DIR/etc/profile.d/env.sh
cd $CMSSW_DIR > /dev/null 2>&1 && cmsenv && cd - > /dev/null 2>&1
source $DBS3_DIR/etc/profile.d/init.sh
