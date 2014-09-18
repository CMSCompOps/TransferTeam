TransferTeam
============


###Invalidation
1) Check replica
```
awk '{system("python ~/TransferTeam/commons/checkReplica.py --lfn "$1)}' file.txt
```

2a) Local invalidation
```
~/TransferTeam/phedex/FileDeleteTMDB -db ~/param/DBParam:Prod/Meric -list [file] -node [site]
```

2b) Global invalidation
```
-TMDB
~/TransferTeam/phedex/FileDeleteTMDB -db ~/param/DBParam:Prod/Meric -list [file] -invalidate

-DBS

~/TransferTeam/dbs/DBS3SetFileStatus.py --url=https://cmsweb.cern.ch/dbs/prod/global/DBSWriter --status=invalid --recursive=False --files=[files]
OR
awk '{system("~/TransferTeam/dbs/DBS3SetFileStatus.py --url=https://cmsweb.cern.ch/dbs/prod/global/DBSWriter --status=invalid --recursive=False --files="$1)}' [file]
```

###PhEDEx Admin - new site

1) Create PhEDEx nodes

```
(optional: -capacity 200T)
~/TransferTeam/phedex/NodeNew -db ~/param/DBParam:Dev/Meric -name T3_HU_Debrecen -kind Disk -technology DPM -se-name dpm.grid.atomki.hu -capacity 200T
~/TransferTeam/phedex/NodeNew -db ~/param/DBParam:Debug/Meric -name T3_HU_Debrecen -kind Disk -technology DPM -se-name dpm.grid.atomki.hu -capacity 200T
~/TransferTeam/phedex/NodeNew -db ~/param/DBParam:Prod/Meric -name T3_HU_Debrecen -kind Disk -technology DPM -se-name dpm.grid.atomki.hu -capacity 200T
```

2) Create PhEDEx links

Link weights: https://twiki.cern.ch/twiki/bin/view/CMSPublic/CompOpsTransferTeamLinkWeights
```
~/TransferTeam/phedex/LinkNew -db ~/param/DBParam:Dev/Meric T1_US_FNAL_Disk T3_KR_KISTI:R/1
~/TransferTeam/phedex/LinkNew -db ~/param/DBParam:Debug/Meric T1_US_FNAL_Disk T3_KR_KISTI:R/1
~/TransferTeam/phedex/LinkNew -db ~/param/DBParam:Prod/Meric T1_US_FNAL_Disk T3_KR_KISTI:R/1
```

or use awk to create all at once
```
awk '{system("~/TransferTeam/phedex/LinkNew -db ~/param/DBParam:Prod/Meric "$1" "$2":R/"$3";~/TransferTeam/phedex/LinkNew -db ~/param/DBParam:Debug/Meric "$1" "$2":R/"$3";~/TransferTeam/phedex/LinkNew -db ~/param/DBParam:Dev/Meric "$1" "$2":R/"$3)}'

$cat list.txt
T1_US_FNAL_Disk T3_KR_KISTI 1
T1_US_FNAL_Buffer T3_KR_KISTI 4
T1_IT_CNAF_Disk T3_KR_KISTI 1
```

3) Disable Prod links, they should be commissioned, and enabled automatically
```
~/TransferTeam/phedex/DDTLinksManage -db ~/param/DBParam:Prod/Meric file

$cat file
T1_US_FNAL_Disk T3_KR_KISTI disable
T1_IT_CNAF_Disk T3_KR_KISTI disable
```
###Check Replica

```
awk '{system("python ~/TransferTeam/commons/checkReplica.py --lfn "$1)}' file.txt

awk '{system("python ~/TransferTeam/commons/checkReplica.py --option custodial:y --dataset "$1)}' file.txt
```


###Parse PhEDEx data service

```
~/TransferTeam/commons/datasvc.py --service errorlog --options "from=T1_FR_CCIN2P3_Disk&to=T1_DE_KIT_Disk" --path /phedex/link/block/file:name/transfer_error:detail_log

awk '{system("~/TransferTeam/commons/datasvc.py --service missingfiles --options \"block="$1"\" --path /phedex/block/replica:node")}' block_list.txt
```

###Submit transfer to FTS server

```
glite-transfer-submit -s FTS_SERVER SOURCE_FILE DEST_FILE
glite-transfer-status -l -s FTS_SERVER JOB_ID

glite-transfer-submit -s https://fts3.cern.ch:8443 srm://grse001.inr.troitsk.ru:8446/srm/managerv2?SFN=/dpm/inr.troitsk.ru/home/cms/store/PhEDEx_LoadTest07/LoadTest07New10/LoadTest07_RU_INR_75 srm://cmsrm-se01.roma1.infn.it:8443/srm/managerv2?SFN=/pnfs/roma1.infn.it/data/cms/store/PhEDEx_LoadTest07/LoadTest07_Debug_RU_INR/IT_Rome/28/meric_test.tmp

it will return job id: 38bdb1c4-0827-11e4-a830-ff460c4532c8

glite-transfer-status -l -s https://fts3.cern.ch:8443 38bdb1c4-0827-11e4-a830-ff460c4532c8
```
###Others
* Connect TMDB 
```
sqlplus $(~/phedex/PHEDEX-micro/Utilities/OracleConnectId -db ~/param/DBParam:Prod/Meric)

-if you'll update something, you should also set the role after connecting
SQL> set role phedex_opsmeric_prod identified by XXXXXXXXXXX;
```

* create EOS dump (all files older than one month)
```
for f in `/afs/cern.ch/project/eos/installation/0.3.15/bin/eos.select ls /eos/cms/store | egrep "mc|data|generator|results|hidata|himc|lumi|relval"`; do /afs/cern.ch/project/eos/installation/0.3.15/bin/eos.select find -f -mtime +30 --ctime --mtime --checksum --size /eos/cms/store/$f; done | gzip -9 > eos_dump_`date +%s`.gz
```


###Frequently used linux commands

* **awk:** run the command or print for the each line in the input file
```
awk '{print "first and third column in the file: " $1 " " $3 )}' input_file.txt
awk '{system("cat " $1 " | grep test" )}' input_file.txt
```

* **sed:** find and replace a string in a file
```
sed -i 's/find/replace/g' file.txt
-i : inplace
g  : all
```

* **split** file into subfiles
```
split (-l rowcound) (-b maxbyte) (-d numeric suffix) filename
```

* **join** two file based on a column
```
join -1 1 -2 1 file1 file2
```

* **sort** a file
```
sort -t. -k 2,2n -k 4,4n
-t.     : separator '.'
-k 2,2n : Do a sort by column (-k), start at the beginning of column 2 and go to the end of column 2 (2,2).
        : n, numeric sort
```

* **comm:** get differences or intersection of two file -files should be sorted-
```
comm -23 file1 file2
-23 : get unique lines in file1
-13 : get unique lines in file2
-12 : get common lines
```

* **sort** on the fly
```
cat <(sort file1)
```

* get files or directories
```
-get dirs
ls -d -1 $PWD/**
-get files
ls -d -1 $PWD/*.*
-get everything
ls -d -1 $PWD/**/*
```

* convert seconds to date
```
date -d @1361234760.790
```


