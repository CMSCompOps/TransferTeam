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
