#!/bin/bash


set -x 
export PYTHONPATH=$PYTHONPATH:/root/pradeep/send_aaa_matrics/CMSMonitoring/src/python/
python $PWD/test.py --amq /root/pradeep/send_aaa_matrics/credentials.json --data $PWD/aaa_schema.json 
