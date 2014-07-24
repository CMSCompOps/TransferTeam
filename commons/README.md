###commons

**checkReplica.py:** get replicas of a file/block/dataset

```
* Get replica for a dataset/block/file
    python ./commons/checkReplica.py --dataset /Cosmics/CRUZET09-PromptReco-v1/RAW
    python ./commons/checkReplica.py --block /Cosmics/CRUZET09-PromptReco-v1/RECO#4766d98e-7d7b-11e0-891f-00163e010039
    python ./commons/checkReplica.py --lfn /store/data/Run2011A/Photon/AOD/16Jan2012-v1/0001/42474CCE-A843-E111-82EE-002590200B68.root

* Get custodial replica for a dataset
    python ./commons/checkReplica.py --option custodial:y --dataset /Cosmics/CRUZET09-PromptReco-v1/RAW 

* Get completed replica for a dataset
    python ./commons/checkReplica.py --option complete:y --dataset /Cosmics/CRUZET09-PromptReco-v1/RAW

* Get file replica in Debug instance
    python ./commons/checkReplica.py --instance debug --lfn /store/PhEDEx_LoadTest07/LoadTest07_Debug_ES_CIEMAT/US_Wisconsin/6/LoadTest07_Spain_CIEMAT_C8_amUNw6NuOxlQOKsM_6

```


**datasvc.py:** parse PhEDEx data service
```
* Get file name and file bytes in a dataset
    python ./commons/datasvc.py --service filereplicas --options "dataset=/TT_FullLept_noCorr_mass169_5_8TeV-mcatnlo/Summer12-START53_V7C-v1/GEN-SIM" --path /phedex/block/file:name,bytes

* Get missing files in a specific PhEDEx node
    python ./commons/datasvc.py --service missingfiles --options "block=/QCD_Pt-5to10_Tune4C_13TeV_pythia8/Fall13-POSTLS162_V1_castor-v1/GEN-SIM%23*&node=T1_ES_PIC_Disk" --path /phedex/block/file:name
```
