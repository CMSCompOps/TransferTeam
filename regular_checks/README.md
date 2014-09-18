### dataset without replica: set their DBS status to DELETED

```
# list should not contain RAW dataset
grep "/RAW$" mail_dataset_without_replica.out

# cross-check
awk '{system("python ~/TransferTeam/commons/checkReplica.py --dataset "$1)}' mail_dataset_without_replica.out | grep -v "sites: $"


awk '{system("~/dbs3-client/slc5_amd64_gcc461/cms/dbs3-client/3.1.8/examples/DBS3SetDatasetStatus.py --url=https://cmsweb.cern.ch/dbs/prod/global/DBSWriter --status=DELETED --recursive=False -d " $1 " || echo " $1)}' mail_dataset_without_replica.out | tee failed_files
```
