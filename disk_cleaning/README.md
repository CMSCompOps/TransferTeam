###Consistency Check

twiki: 

#### Get storage overview
```
python ~/TransferTeam/disk_cleaning/getSamples.py --node T1_UK_RAL_Disk
```
#### Create GEN-SIM suggestion list
```
python ~/TransferTeam/disk_cleaning/diskCleaning_GEN-SIM.py --node T1_UK_RAL_Disk --monthlimit 6 | tee output.txt
```
creates list of dataset with their WorkFlow info, it prints only dataset which are not used by any ongoing workflow, and produced before MONTHLIMIT
if you specify "--debug" option, it prints debug info into stderr
