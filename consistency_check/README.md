###Consistency Check

twiki: https://twiki.cern.ch/twiki/bin/view/CMSPublic/CompOpsTransferTeamConsistencyChecks

#### StorageConsistencyCheck(SCC)
```
~/TransferTeam/consistency_check/SCC/SCCHelper.sh --db ~/param/DBParam:Prod/Meric --node T2_CH_CERN --dump path/to/dump/file --output output_dir
```
#### BlockDownloadVerify(BDV)

* inject BDV size test for all blocks at a site
(use --expire 8640000 for sites with lots of file like T1_US_FNAL_Buffer)
```
~/TransferTeam/consistency_check/BDV/BlockDownloadVerify-injector.pl --db ~/param/DBParam:Prod/Meric --node T2_CH_CERN --block % --test size --force 
```

* parse BDV results
```
~/TransferTeam/consistency_check/BDV/BDVParser.sh --verbose --db ~/param/DBParam:Prod/Meric --node T2_CH_CERN --day 20 --output output_dir
```
#### How to run File_mismatch_WS.py

* Log in lxplus7 vm as usual and create a proxy (See https://github.com/CMSCompOps/TransferTeam/blob/master/scripts/setup.sh).
* Create and activate a python3 environment. Update the pandas library and then run the script:
```
$ python3 -m venv env
$ source ./env/bin/activate
$ pip3 install update pandas
$ python3 File_mismatch_WS.py
```

* You will get four files: invalidate_in_dbs.txt, invalidate_in_phedex.txt, dataset_empty_dbs.txt and dataset_empty_phedex.txt. Proceed as necessary. 
