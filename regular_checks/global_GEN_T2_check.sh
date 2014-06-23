#!/bin/bash 
echo "Check for /GEN datasets older than 6 months at the T2 at `date`"
current_week=`date +"%Y%m%d"`
six_months_ago=`date -d '6 months ago' +"%Y%m%d"`

# set dirs
SRC=/afs/cern.ch/user/m/mtaze/scripts/regular_checks
OUT=/afs/cern.ch/user/m/mtaze/work/OUTPUT/RegularCheckResults/GEN_check/$current_week
mkdir -p $OUT

# set files
out_GEN_datasets=$OUT/GEN_dataset.list
out_nodes=$OUT/T2node.list
out_replica=$OUT/GEN_dataset_replica.list

# find all 6-months old /GEN datasets
python $SRC/DBS3Utils.py --datasetGEN --maxcdate $six_months_ago | sort > $out_GEN_datasets

# get T2 sites
wget -q --no-check-certificate "https://cmsweb.cern.ch/phedex/datasvc/xml/prod/nodes?node=T2_*" -O - | xmllint --format -| grep "^  <node" | cut -d '"' -f8 | tr '"' ' ' > $out_nodes

# get replica site of GEN datasets
awk -v script="$SRC/checkReplica.py" '{system("python "script" --dataset "$1)}' $out_GEN_datasets > $out_replica

# generate lists per T2
for node in `cat $out_nodes`
do
    if grep -F "$node" $out_replica > /dev/null
    then
        grep $node $out_replica | cut -d ' ' -f 2 > $OUT/GEN_$node.out; 
    fi
done

/bin/mail -s '/GEN datasets at the T2s older than 6 months' meric.taze@cern.ch <<< "The current lists of /GEN datasets older than 6 months at the T2s are now available at: `hostname`:$OUT"

echo "end of Check for /GEN datasets older than 6 months at the T2 at `date`"
