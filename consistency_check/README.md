###Consistency Check

twiki: https://twiki.cern.ch/twiki/bin/view/CMSPublic/CompOpsTransferTeamConsistencyChecks

#### StorageConsistencyCheck(SCC)
```
~/TransferTeam/consistency_check/SCC/SCCHelper.sh --db ~/param/DBParam:Prod/Meric --node T2_CH_CERN --dump path/to/dump/file --round Nov14
```
#### BlockDownloadVerify(BDV)

* inject BDV size test for all blocks at a site
(use --expire 8640000 for sites with lots of file like T1_US_FNAL_Buffer)
```
~/TransferTeam/consistency_check/BDV/BlockDownloadVerify-injector.pl --db ~/param/DBParam:Prod/Meric --node T2_CH_CERN --block % --test size --force 
```

* parse BDV results
```
~/TransferTeam/consistency_check/BDV/BDVParser.sh --verbose --db ~/param/DBParam:Prod/Meric --node T2_CH_CERN --day 20 --round Nov14
```
