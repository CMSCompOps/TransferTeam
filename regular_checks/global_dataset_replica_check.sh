#!/bin/bash 
echo "global dataset replica check  at `date`"
current_week=`date +"%Y%m%d"`

# set dirs
SRC=/afs/cern.ch/user/m/mtaze/TransferTeam/regular_checks
OUT=/afs/cern.ch/user/m/mtaze/work/OUTPUT/RegularCheckResults/replica_check/$current_week
mkdir -p $OUT

# set files
out_valid_datasets=$OUT/valid_datasets.list
out_dataset_be_checked=$OUT/datasets_be_checked.list

out_custodial_location=$OUT/dataset_custodial_location.out
out_replica_location=$OUT/dataset_location.out
out_ds_without_custodial_location=$OUT/dataset_without_custodial_location.tmp
out_ds_without_custodial_location_final_list=$OUT/dataset_without_custodial_location.out
out_ds_without_replica=$OUT/dataset_without_replica.out

out_penguings_bunnies=$OUT/PenguinsBunnies.out
out_test_backfill=$OUT/TestBackfill.out
out_t0test=$OUT/T0Test.out
tmp=$OUT/tmp.out

# get all valid datasets
python $SRC/DBS3Utils.py --datasetValid | sort > $out_valid_datasets

# remove what we don't care
cat $out_valid_datasets | grep -vi "StoreResults" | grep -v "GEN$" | grep -v "Express" > $out_dataset_be_checked

# get custodial location of datasets
awk -v script="$SRC/checkReplica.py" '{system("python "script" --option custodial:y --dataset "$1)}' $out_dataset_be_checked > $out_custodial_location
# get dataset without custodial location
cat $out_custodial_location | grep "sites: $" | cut -d ' ' -f 2 > $out_ds_without_custodial_location

# get replica site of datasets
awk -v script="$SRC/checkReplica.py" '{system("python "script" --dataset "$1)}' $out_ds_without_custodial_location > $out_replica_location
# get dataset without replica
cat $out_replica_location | grep "sites: $" | cut -d ' ' -f 2 > $out_ds_without_replica


# exclude 2011 samples????
cat $out_ds_without_replica | grep -vi 2011 > $tmp
cat $tmp > $out_ds_without_replica

# meric.taze@cern.ch, Aram.Apyan@cern.ch
[ -s $out_ds_without_replica ] && /bin/mail -s 'datasets without replica' meric.taze@cern.ch,aram.apyan@cern.ch < $out_ds_without_replica

#remove from the list datasets without replica
comm -23 $out_ds_without_custodial_location $out_ds_without_replica > $tmp
cat $tmp > $out_ds_without_custodial_location

#searching for Penguins and Bunnies and send to Dave Mason
cat $out_ds_without_custodial_location | egrep -i "Penguins|Bunnies" > $out_penguings_bunnies
#remove Penguins and Bunnies
comm -23 $out_ds_without_custodial_location $out_penguings_bunnies > $tmp
cat $tmp > $out_ds_without_custodial_location


# search test datasets
cat $out_ds_without_custodial_location | egrep -i "Test|Backfill" | egrep -v 'HeavyIonTest-Error|TestEnables' | grep -v "/MultiJet1Parked/Run2012B-HcalLaserFilterTest_12Dec2012-v1/AOD" | grep -v "/MultiJet1Parked/Run2012C-HcalLaserFilterTest_12Dec2012-v1/AOD" > $out_test_backfill

#for ds in `cat $out_dir/$test_backfill`
#do
#     grep $ds $out_dir/EMPTY_MSS.out  >> $out_dir/$test_backfill.out
#done 

#cat  $out_dir/$test_backfill.out | grep -v "/MultiJet1Parked/Run2012B-HcalLaserFilterTest_12Dec2012-v1/AOD" | grep -v "/MultiJet1Parked/Run2012C-HcalLaserFilterTest_12Dec2012-v1/AOD" | awk '{print $2"      " $5}'  >> $out_dir/$test_backfill.result

[ -s $out_test_backfill ] && /bin/mail -s 'global Test and Backfill datasets' dmason@fnal.gov,andrew.lahiff@stfc.ac.uk,vincenzo.spinoso@cern.ch,ajit@hep.wisc.edu,jen_a@fnal.gov,jbadillo@cern.ch,Dirk.Hufnagel@cern.ch,gutsche@fnal.gov,meric.taze@cern.ch,amlevin@mit.edu,aram.apyan@cern.ch < $out_test_backfill

#remove test datasets
comm -23 $out_ds_without_custodial_location $out_test_backfill > $tmp
cat $tmp > $out_ds_without_custodial_location


# search test datasets at T0
cat $out_valid_datasets | egrep "T0TEST|WMAT0Commissioning|TEST_*_WMA" > $out_t0test

[ -s $out_t0test ] && /bin/mail -s 'T0 test datasets' dmason@fnal.gov,luis89@fnal.gov,Dirk.Hufnagel@cern.ch,gutsche@fnal.gov,meric.taze@cern.ch,aram.apyan@cern.ch < $out_t0test


#send email  datasets without custodial location
# the last 6 HIRun2013 datasets should be kept at Vanderbilt
cat $out_ds_without_custodial_location \
| grep -vi /QCD_Pt-80to120_MuPt5Enriched_TuneZ2_7TeV-pythia6/Fall10-START38_V12-v1/AODSIM \
| grep -vi /QCD_Pt-30to50_MuPt5Enriched_TuneZ2_7TeV-pythia6/Fall10-START38_V12-v1/AODSIM \
| grep -vi /HIHighPt/ComissioningHI-hiHighPtTrack-PromptSkim-v1/RECO \
| grep -vi /HIHighPt/ComissioningHI-hiHighPt-PromptSkim-v1/RECO \
| grep -vi /RelValProdTTbar/JobRobot-MC_3XY_V24_JobRobot-v1/GEN-SIM-DIGI-RECO \
| grep -vi /RelValProdTTbar/CMSSW_4_2_3-MC_42_V12_JobRobot-v1/GEN-SIM-RECO \
| grep -vi /QCD_2MuPEtaFilter_7TeV-pythia6/Summer11-PU_S4_START42_V11-v1/GEN-SIM-RECO \
| grep -vi /JPsiToMuMu_2MuPEtaFilter_7TeV-pythia6-evtgen/Summer11-PU_S4_START42_V11-v2/GEN-SIM-RECO \
| grep -vi /PAHighPt/HIRun2013-FlowCorrPA-PromptSkim-v1/RECO \
| grep -vi /PAHighPt/HIRun2013-HighPtPA-PromptSkim-v1/RECO \
| grep -vi /PAMuon/HIRun2013-HighPtPA-PromptSkim-v1/RECO \
| grep -vi /PAMuon/HIRun2013-PsiMuMuPA-PromptSkim-v1/RECO \
| grep -vi /PAMuon/HIRun2013-UpsMuMuPA-PromptSkim-v1/RECO \
| grep -vi /PAMuon/HIRun2013-ZMuMuPA-PromptSkim-v1/RECO > $out_ds_without_custodial_location_final_list

[ -s $out_ds_without_custodial_location_final_list ] && /bin/mail -s 'datasets without custodial location' dmason@fnal.gov,andrew.lahiff@stfc.ac.uk,ajit@hep.wisc.edu,vincenzo.spinoso@ba.infn.it,jbadillo@cern.ch,gutsche@fnal.gov,jen_a@fnal.gov,amlevin@mit.edu,meric.taze@cern.ch,aram.apyan@cern.ch < $out_ds_without_custodial_location_final_list
  
echo "end of global dataset replica check at `date`"
