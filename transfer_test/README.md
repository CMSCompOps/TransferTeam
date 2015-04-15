Run2 Trannsfer Test
===================

* twiki     : https://twiki.cern.ch/twiki/bin/view/CMSPublic/CompOpsRun2T0T1TransferTests
* monitoring: https://twiki.cern.ch/twiki/bin/view/CMSPublic/CompOpsRun2T0T1TransferTestsMonitoring

### Procedure
1) Increase the injection rates
```
~/TransferTeam/transfer_test/SetInjectionRate --db ~/param/DBParam:Debug/Meric --input rate_increase.inp
```

2) update the twiki and monitoring page accordingly

3) Decrease the rates once the test finishes
```
~/TransferTeam/transfer_test/SetInjectionRate --db ~/param/DBParam:Debug/Meric --input rate_decrease.inp
```
