#!/bin/bash


set -x 
export PYTHONPATH=$PYTHONPATH:/opt/TransferTeam/AAAOps/send_aaa_matrics/CMSMonitoring/src/python/
export PYTHONPATH=$PYTHONPATH:/opt/TransferTeam/AAAOps/send_aaa_matrics/stomp.py/stomp/
#source /cvmfs/sft.cern.ch/lcg/views/LCG_96python3/x86_64-centos7-gcc8-opt/setup.sh
rm fed.json
python3 /opt/TransferTeam/AAAOps/send_aaa_matrics/aaa_federation.py  --amq /opt/TransferTeam/AAAOps/send_aaa_matrics/credentials.json 
