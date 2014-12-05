### Create dataset list for deletion per tape tier
1) Get replica
```
awk '{system("python ~/TransferTeam/commons/checkReplica.py --dataset "$1)}' dataset.list | tee dataset.loc
```

2) Create lists

echo -e "T0_CH_CERN\nT1_DE_KIT\nT1_ES_PIC\nT1_FR_CCIN2P3\nT1_IT_CNAF\nT1_UK_RAL\nT1_US_FNAL" | awk '{system("cat dataset.loc | grep -E "$1"_[MBE] | cut -d \" \" -f 2 > "$1".txt")}'
