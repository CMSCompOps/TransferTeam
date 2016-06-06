cwd=$PWD
source ~/phedex/PHEDEX/etc/profile.d/env.sh
cd ~/work/public/CMSSW_7_4_15/src
cmsenv
source /cvmfs/cms.cern.ch/crab/crab.sh
voms-proxy-init -voms cms
cd $cwd
