###regular_checks
* global_dataset_replica_check.sh: checks all valid datasets and creates the following outputs:
 * datasets without replica
 * global Test and Backfill datasets
 * T0 test datasets
 * datasets without custodial location

* global_production_dataset_check.sh: checks all production datasets and creates the following outputs:
 * production datasets without replica
 * Test and Backfill production datasets older than one month
 * datasets older than one month, but still in PRODUCTION status

* global_GEN_T2_check.sh: checks all GEN datasets older than 6 months and creates dataset lists per T2 site


#### dataset without replica: set their DBS status to DELETED

```
# list should not contain RAW dataset
grep "/RAW$" mail_dataset_without_replica.out

# cross-check
awk '{system("python ~/TransferTeam/commons/checkReplica.py --dataset "$1)}' mail_dataset_without_replica.out | grep -v "sites: $"


awk '{system("~/dbs3-client/slc5_amd64_gcc461/cms/dbs3-client/3.1.8/examples/DBS3SetDatasetStatus.py --url=https://cmsweb.cern.ch/dbs/prod/global/DBSWriter --status=DELETED --recursive=False -d " $1 " || echo " $1)}' mail_dataset_without_replica.out | tee failed_files
```
