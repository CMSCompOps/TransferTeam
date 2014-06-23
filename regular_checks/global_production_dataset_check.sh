#!/bin/bash 
echo "production datasets check  at `date`"
current_week=`date   +"%Y%m%d"`
five_weeks_ago=`date -d '5 week ago' +"%Y%m%d"`

# set dirs
SRC=/afs/cern.ch/user/m/mtaze/TransferTeam/regular_checks
OUT=/afs/cern.ch/user/m/mtaze/work/OUTPUT/RegularCheckResults/production_check/$current_week
mkdir -p $OUT

# set files
out_prod_datasets=$OUT/production_datasets.list
out_replica_location=$OUT/dataset_location.out
out_ds_without_replica=$OUT/dataset_without_replica.out
out_test_dataset=$OUT/test_dataset.out
tmp=$OUT/tmp.out

# get all production datasets created within last month
python $SRC/DBS3Utils.py --datasetProduction --maxcdate $five_weeks_ago | sort > $out_prod_datasets


# get replica site of datasets
awk -v script="$SRC/checkReplica.py" '{system("python "script" --dataset "$1)}' $out_prod_datasets > $out_replica_location
# get dataset without replica
cat $out_replica_location | grep "sites: $" | cut -d ' ' -f 2 > $out_ds_without_replica

[ -s $out_ds_without_replica ] && /bin/mail -s 'production datasets without replica' dmason@fnal.gov,andrew.lahiff@stfc.ac.uk,vincenzo.spinoso@ba.infn.it,ajit@hep.wisc.edu,jbadillo@cern.ch,gutsche@fnal.gov,Dirk.Hufnagel@cern.ch,meric.taze@cern.ch,aram.apyan@cern.ch,amlevin@mit.edu < $out_ds_without_replica


#remove the no replica sample
comm -23 $out_prod_datasets $out_ds_without_replica > $tmp
cat $tmp > $out_prod_datasets


#find Penguins, Test,Backfill 
cat $out_prod_datasets | egrep -i 'Test|Backfill|Penguins|PreScaleThingy' | egrep -v 'HeavyIonTest-Error|TestEnables' > $out_test_dataset

#cat $DIR/out/$current_week/Test_samples.tmp | sort | uniq > $DIR/out/$current_week/Test_samples_nonwhitelisted.txt
#cat $DIR/Test_whitelist.txt | sort | uniq > $DIR/out/$current_week/Test_whitelist.txt
#comm -23 $DIR/out/$current_week/Test_samples_nonwhitelisted.txt  $DIR/out/$current_week/Test_whitelist.txt >$DIR/out/$current_week/Test_samples.txt

[ -s $out_test_dataset ] && /bin/mail -s 'Test and Backfill production datasets older than one month' dmason@fnal.gov,andrew.lahiff@stfc.ac.uk,vincenzo.spinoso@ba.infn.it,ajit@hep.wisc.edu,jbadillo@cern.ch,gutsche@fnal.gov,Dirk.Hufnagel@cern.ch,meric.taze@cern.ch,aram.apyan@cern.ch,amlevin@mit.edu < $out_test_dataset

#remove the Test* datasets
comm -23 $out_prod_datasets $out_test_dataset > $tmp
cat $tmp > $out_prod_datasets


#for i in `cat $DIR/out/$current_week/$out_file`
#do 
#  grep $i $DIR/out/$current_week/$out_file.location >> $DIR/out/$current_week/$out_file.results
#done

[ -s $out_prod_datasets ] && /bin/mail -s 'datasets older than one month, but still in PRODUCTION status' dmason@fnal.gov,andrew.lahiff@stfc.ac.uk,vincenzo.spinoso@ba.infn.it,ajit@hep.wisc.edu,jbadillo@cern.ch,gutsche@fnal.gov,Dirk.Hufnagel@cern.ch,meric.taze@cern.ch,aram.apyan@cern.ch,amlevin@mit.edu < $out_prod_datasets
 

echo "end of production datasets check at `date`"
