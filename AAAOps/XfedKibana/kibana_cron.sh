#!/bin/bash

/root/XRDFED-kibana-probe.py >> /var/log/XRDFED-kibana-probe.log 2>&1

/usr/bin/curl -i -F file=@/var/www/html/aaa-probe/xrdfed_kibana/XRDFED_CMS-GLOBAL.xml xsls.cern.ch 2>&1 | /bin/awk '{ print strftime("%Y-%m-%d %H:%M:%S"), $0; }' >> /var/log/XRDFED-kibana-xml-push.log
/usr/bin/curl -i -F file=@/var/www/html/aaa-probe/xrdfed_kibana/XRDFED_CMS-US.xml xsls.cern.ch 2>&1 | /bin/awk '{ print strftime("%Y-%m-%d %H:%M:%S"), $0; }' >> /var/log/XRDFED-kibana-xml-push.log
/usr/bin/curl -i -F file=@/var/www/html/aaa-probe/xrdfed_kibana/XRDFED_CMS-EU.xml xsls.cern.ch 2>&1 | /bin/awk '{ print strftime("%Y-%m-%d %H:%M:%S"), $0; }' >> /var/log/XRDFED-kibana-xml-push.log

/usr/bin/curl -i -F file=@/var/www/html/aaa-probe/xrdfed_kibana/XRDFED_CMS-GLOBAL01.xml xsls.cern.ch 2>&1 | /bin/awk '{ print strftime("%Y-%m-%d %H:%M:%S"), $0; }' >> /var/log/XRDFED-kibana-xml-push.log
/usr/bin/curl -i -F file=@/var/www/html/aaa-probe/xrdfed_kibana/XRDFED_CMS-GLOBAL02.xml xsls.cern.ch 2>&1 | /bin/awk '{ print strftime("%Y-%m-%d %H:%M:%S"), $0; }' >> /var/log/XRDFED-kibana-xml-push.log
/usr/bin/curl -i -F file=@/var/www/html/aaa-probe/xrdfed_kibana/XRDFED_CMS-EU-LLR.xml xsls.cern.ch 2>&1 | /bin/awk '{ print strftime("%Y-%m-%d %H:%M:%S"), $0; }' >> /var/log/XRDFED-kibana-xml-push.log
/usr/bin/curl -i -F file=@/var/www/html/aaa-probe/xrdfed_kibana/XRDFED_CMS-EU-BARI.xml xsls.cern.ch 2>&1 | /bin/awk '{ print strftime("%Y-%m-%d %H:%M:%S"), $0; }' >> /var/log/XRDFED-kibana-xml-push.log
/usr/bin/curl -i -F file=@/var/www/html/aaa-probe/xrdfed_kibana/XRDFED_CMS-EU-PISA.xml xsls.cern.ch 2>&1 | /bin/awk '{ print strftime("%Y-%m-%d %H:%M:%S"), $0; }' >> /var/log/XRDFED-kibana-xml-push.log
/usr/bin/curl -i -F file=@/var/www/html/aaa-probe/xrdfed_kibana/XRDFED_CMS-US-FNAL.xml xsls.cern.ch 2>&1 | /bin/awk '{ print strftime("%Y-%m-%d %H:%M:%S"), $0; }' >> /var/log/XRDFED-kibana-xml-push.log
/usr/bin/curl -i -F file=@/var/www/html/aaa-probe/xrdfed_kibana/XRDFED_CMS-US-UNL.xml xsls.cern.ch 2>&1 | /bin/awk '{ print strftime("%Y-%m-%d %H:%M:%S"), $0; }' >> /var/log/XRDFED-kibana-xml-push.log
/usr/bin/curl -i -F file=@/var/www/html/aaa-probe/xrdfed_kibana/XRDFED_CMS-TRANSIT.xml xsls.cern.ch 2>&1 | /bin/awk '{ print strftime("%Y-%m-%d %H:%M:%S"), $0; }' >> /var/log/XRDFED-kibana-xml-push.log
/usr/bin/curl -i -F file=@/var/www/html/aaa-probe/xrdfed_kibana/XRDFED_CMS-TRANSIT01.xml xsls.cern.ch 2>&1 | /bin/awk '{ print strftime("%Y-%m-%d %H:%M:%S"), $0; }' >> /var/log/XRDFED-kibana-xml-push.log
/usr/bin/curl -i -F file=@/var/www/html/aaa-probe/xrdfed_kibana/XRDFED_CMS-TRANSIT02.xml xsls.cern.ch 2>&1 | /bin/awk '{ print strftime("%Y-%m-%d %H:%M:%S"), $0; }' >> /var/log/XRDFED-kibana-xml-push.log
/usr/bin/curl -i -F file=@/var/www/html/aaa-probe/xrdfed_kibana/XRDFED_CMS-EU-IPV6.xml xsls.cern.ch 2>&1 | /bin/awk '{ print strftime("%Y-%m-%d %H:%M:%S"), $0; }' >> /var/log/XRDFED-kibana-xml-push.log

/root/check_XMLs.sh >> /var/log/check_XMLs.log 2>&1

#/usr/bin/curl -i -F file=@/var/www/html/aaa-probe/xrdfed_kibana/XRDFED_CMS-GLOBAL.xml xsls.cern.ch 2>&1 | /root/timestamp.sh
exit 0;

