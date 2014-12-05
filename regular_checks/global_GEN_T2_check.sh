#!/bin/bash 
echo "Check for /GEN datasets older than 6 months at the T2 at `date`"
current_week=`date +"%Y%m%d"`
six_months_ago=`date -d '6 months ago' +"%Y%m%d"`

# set dirs
SRC=/afs/cern.ch/user/m/mtaze/TransferTeam/regular_checks
OUT=/afs/cern.ch/user/m/mtaze/work/public/OUTPUT/RegularCheckResults/GEN_check/$current_week
mkdir -p $OUT

# set files
out_GEN_datasets=$OUT/GEN_dataset.list
out_nodes=$OUT/T2node.list
out_replica=$OUT/GEN_dataset_replica.list
out_custodial_replica=$OUT/GEN_dataset_custodial_replica.list
out_ds_without_custodial_location=$OUT/GEN_dataset_without_custodial_location.list
tmp=$OUT/tmp.out

# find all 6-months old /GEN datasets
python $SRC/DBS3Utils.py --datasetGEN --maxcdate $six_months_ago | sort > $out_GEN_datasets

# get T2 sites
wget -q --no-check-certificate "https://cmsweb.cern.ch/phedex/datasvc/xml/prod/nodes?node=T2_*" -O - | xmllint --format -| grep "^  <node" | cut -d '"' -f8 | tr '"' ' ' > $out_nodes

# get custodial replica and remove the ones without custodial location
awk -v script="$SRC/checkReplica.py" '{system("python "script" --option custodial:y --dataset "$1)}' $out_GEN_datasets > $out_custodial_replica
cat $out_custodial_replica | grep "sites: $" | cut -d ' ' -f 2 > $out_ds_without_custodial_location

comm -23 $out_GEN_datasets $out_ds_without_custodial_location > $tmp
cat $tmp > $out_GEN_datasets

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

text="Hi All,\n\nThe current lists of /GEN datasets older than 6 months at the T2s are now available at:\n\n$OUT\n\nPlease review them and submit PhEDEx deletion requests if necessary.\n\nRegards,\nTransferTeam\n"

echo -e $text | /bin/mail -s '/GEN datasets at the T2s older than 6 months' meric.taze@cern.ch

echo "end of Check for /GEN datasets older than 6 months at the T2 at `date`"
