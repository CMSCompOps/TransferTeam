#!/bin/bash
#
# Checks all xrootd endpoint in vofeed https://cmssst.web.cern.ch/cmssst/vofeed/vofeed.xml is found from xrdmapcall
#
FedProbeSendAAAMetrics=/opt/TransferTeam/AAAOps/FedProbeSendAAAMetrics
FedProbeSendAAAMetrics=/opt/TransferTeam/AAAOps/FedProbeSendAAAMetrics
#xredirs=$(cat $FedProbeSendAAAMetrics/fed.json  | cut -d, -f6 | sort -u | cut -d\" -f4 | cut -d: -f1)
#xredirs=$(grep " Man " $FedProbeSendAAAMetrics/out/xrdmapc_all_0.txt $FedProbeSendAAAMetrics/out/xrdmapc_all_1.txt | awk '{print $NF}' | cut -d: -f1 | sort -u)
xredirs=$(grep " Man " $FedProbeSendAAAMetrics/out/xrdmapc_all_0.txt $FedProbeSendAAAMetrics/out/xrdmapc_all_1.txt | cut -d: -f2- | awk '{print $3}' | sort -u)
output=$(printf "%5s %60s %5s\n" Found Xredirtor MLevel)
for xredir in $xredirs ; do
   MLevel=$(echo $(grep $xredir $FedProbeSendAAAMetrics/out/xrdmapc_all_0.txt $FedProbeSendAAAMetrics/out/xrdmapc_all_1.txt | cut -d: -f2- | awk '{print $1}' | sort -u) | sed 's# #+#g')
   Found=$(grep -q $xredir $FedProbeSendAAAMetrics/fed.json ; echo $?)
   output="$output\n"$(printf "%5s %60s %5s\n" $Found $xredir $MLevel)
   #
   # Analyze the outcome
   #
   # 1 Found=1 MLevel!=1 -> 1 $xredir can be one of Found=1 MLevel=1
   #                        2 $xredir could be found from the alias in vofeed

done
printf "$output\n"
exit 0

Found                                                    Xredirtor MLevel
    0                       cms-aaa-manager01.gridpp.rl.ac.uk:1094   2+3
    0                                       cmsio7.rc.ufl.edu:1094     2
    1                                     cmsxrootd2.fnal.gov:1094     1
    1                                    cmsxrootd.ihep.ac.cn:1094     2
    0                                cmsxrootd-site1.fnal.gov:1094     2
    0                                cmsxrootd-site2.fnal.gov:1094     2
    0                                cmsxrootd-site3.fnal.gov:1094     2
    1                                    dmsdcatst03.fnal.gov:1094     2
    1                                   llrxrd-redir.in2p3.fr:1094     1
    1                                   llrxrd-redir.in2p3.fr:1194     2
    1                                   llrxrd-redir.in2p3.fr:1294     2
    0                                    osg-se.sprace.org.br:1094     2
    0                                  pubxrootd.hep.wisc.edu:1094     2
    0                                  redirector.t2.ucsd.edu:1094     2
    0                                   xroot02.ncg.ingrid.pt:1094     2
    1                           xrootd01.grid.hep.ph.ic.ac.uk:1094     1
    1                                       xrootd.ba.infn.it:1094     1
    1                                       xrootd.ba.infn.it:1194     2
    1                                       xrootd.ba.infn.it:1294     2
    1                              xrootd-cms-01.cr.cnaf.infn.it:0     3
    0                           xrootd-cms-01.cr.cnaf.infn.it:1094     3
    0                           xrootd-cms-02.cr.cnaf.infn.it:1094     3
    0                                    xrootd.cmsaf.mit.edu:1094     2
    1                    xrootd-cms-redir-int.cr.cnaf.infn.it:1094     1
    1                    xrootd-cms-redir-int.cr.cnaf.infn.it:1194     2
    1                    xrootd-cms-redir-int.cr.cnaf.infn.it:1294     2
    1                           xrootd-cms-uk.gridpp.rl.ac.uk:1094     2 https://ggus.eu/index.php?mode=ticket_info&ticket_id=153496&come_from=submit
    1                                 xrootd-es-cie.ciemat.es:1096     2
    1                                    xrootd-es-pic.pic.es:1096     2
    0                                  xrootd.hepgrid.uerj.br:1094     2
    0                                      xrootd.hep.kbfi.ee:1094     2
    0                                    xrootd-local.unl.edu:1094     2
    0                                  xrootd.rcac.purdue.edu:1094     2
    1                                 xrootd-redic.pi.infn.it:1094     1
    1                                 xrootd-redic.pi.infn.it:1194     2
    1                                 xrootd-redic.pi.infn.it:1294     2
    1      xrootd-redir1-vanderbilt.sites.opensciencegrid.org:1094     2
    1      xrootd-redir2-vanderbilt.sites.opensciencegrid.org:1094     2
    0                             xrootd-redir.ultralight.org:1094     2
