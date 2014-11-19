#!/bin/bash
# without trailing slash
PHEDEX_DIR=~/phedex/PHEDEX-micro
CMSSW_DIR=~/CMSSW_5_3_0
DBS3_DIR=~/dbs3-client/slc5_amd64_gcc461/cms/dbs3-client/3.1.8

#voms-proxy-init -voms cms --valid 240:0
#export X509_USER_PROXY=/tmp/x509up_u$(id -u)
export X509_USER_PROXY=/afs/cern.ch/user/m/mtaze/private/vocms0242/proxy.cert

if [ "$1" == "dbs" ]
then
    source $DBS3_DIR/etc/profile.d/init.sh
elif [ "$1" == "phedex" ]
then
    source $PHEDEX_DIR/etc/profile.d/env.sh
elif [ "$1" == "cmssw" ]
then
    source /cvmfs/cms.cern.ch/cmsset_default.sh
    cd $CMSSW_DIR > /dev/null 2>&1 && eval `scramv1 runtime -sh` && cd - > /dev/null 2>&1
else
    source $PHEDEX_DIR/etc/profile.d/env.sh
    source /cvmfs/cms.cern.ch/cmsset_default.sh
    cd $CMSSW_DIR > /dev/null 2>&1 && eval `scramv1 runtime -sh` && cd - > /dev/null 2>&1
    source $DBS3_DIR/etc/profile.d/init.sh
fi
