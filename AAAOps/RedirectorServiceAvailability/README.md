# Service Availabilty Probe and Uploader for Xrootd Redirectors

Introduction
---

- This directory contains the xrootd redirector probe and the metric uploader.
- Currently the probe and the uploader run  on one of the AAA vocms machines
- Details can be viewed from https://twiki.cern.ch/twiki/bin/view/CMSPublic/CompOpsCentralServicesXrootd and https://twiki.cern.ch/twiki/bin/view/CMSPublic/CompOpsAAAOperationsGuide#Monitoring

Deploying the probe, the uploader, and the cron
---
In the VM machine, as the root user, the github repository can be checked out under /opt/TransferTeam.
The crontab is managed by the puppet: https://gitlab.cern.ch/ai/it-puppet-hostgroup-vocms/-/blob/qa/code/manifests/xrootd/monitor.pp

Operations
---

The probe and the uploader are executed every 15 minute by cron. 
The uploaded metric is visualized in the Grafana dashboard: https://monit-grafana.cern.ch/goto/Q2CH71M7z
