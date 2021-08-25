#!/bin/bash
#
# Checks all xrootd endpoint in vofeed https://cmssst.web.cern.ch/cmssst/vofeed/vofeed.xml is found from xrdmapcall
#
FedProbeSendAAAMetrics=/opt/TransferTeam/AAAOps/FedProbeSendAAAMetrics
FedProbeSendAAAMetrics=/opt/TransferTeam/AAAOps/FedProbeSendAAAMetrics
xredirs=$(cat $FedProbeSendAAAMetrics/fed.json  | cut -d, -f6 | sort -u | cut -d\" -f4 | cut -d: -f1)
output=$(printf "%5s %50s %3s\n" Found Xredirtor Tier)
for xredir in $xredirs ; do
   Tier=$(echo $(grep $xredir $FedProbeSendAAAMetrics/fed.json | cut -d\" -f4 | cut -d_ -f1 | sed 's#T##g' | sort -u) | sed 's# #+#g')
   Found=$(grep -q $xredir $FedProbeSendAAAMetrics/out/xrdmapc_all_0.txt $FedProbeSendAAAMetrics/out/xrdmapc_all_1.txt ; echo $?)
   output="$output\n"$(printf "%5s %50s %3s\n" $Found $xredir $Tier)
done
printf "$output\n"
exit 0
Found                                          Xredirtor Tier
    1                                  bonner04.rice.edu   3
    1                               brux11.hep.brown.edu   3
    0                                   ccsrm.ihep.ac.cn   2
    1                                  ccxrdcms.in2p3.fr   1
    0                          ceph-gw10.gridpp.rl.ac.uk   1
    0                          ceph-gw11.gridpp.rl.ac.uk   1
    1                               cluster142.knu.ac.kr   3
    0                                  cms03.lcg.cscs.ch   2
    0                  cms-aaa-manager01.gridpp.rl.ac.uk   1
    0                               cmsdata.phys.cmu.edu   3
    0                                  cmsio7.rc.ufl.edu   2
    0                       cmsrm-xrootd01.roma1.infn.it   2
    0                       cmsrm-xrootd02.roma1.infn.it   2
    0                            cms-se0.kipt.kharkov.ua   2
    1                                cms-se.hep.uprm.edu   3
    0                              cms-t2-se01.sdfarm.kr   2
    1                                  cmsxrd.ts.infn.it   3
    1                    cmsxrootd-redirectors.gridka.de   1
    0                           cmsxrootd-site1.fnal.gov   1
    0                           cmsxrootd-site2.fnal.gov   1
    0                           cmsxrootd-site3.fnal.gov   1
    0                           dc2-grid-64.brunel.ac.uk   2
    1                          dcache-cms-xrootd.desy.de   2
    1                                 eos.grid.vbc.ac.at   2
    0                             eymir.grid.metu.edu.tr   2
    0                               gaexroot01.ciemat.es   2
    0                         gfe02.grid.hep.ph.ic.ac.uk   2
    0                              grid02.physics.uoi.gr   2
    0                                    grid143.kfki.hu   2
    1                              grid71.phy.ncu.edu.tw   3
    0                  grid-dcache.physik.rwth-aachen.de   2
    0                             grse001.inr.troitsk.ru   2
    0                                        hask.csc.fi   2
    1                                   hepcms-0.umd.edu   3
    0                              heplnx228.pp.rl.ac.uk   2
    0                              heplnx229.pp.rl.ac.uk   2
    1                              hepxrd01.colorado.edu   3
    1                         ingrid-se03.cism.ucl.ac.be   2
    0                         ingrid-se04.cism.ucl.ac.be   2
    1                         ingrid-se05.cism.ucl.ac.be   2
    0                         ingrid-se06.cism.ucl.ac.be   2
    1                               kodiak-se.baylor.edu   3
    0                             lcgse01.phy.bris.ac.uk   2
    0                                   lcgsexrd.jinr.ru   2
    1                                   llrpp01.in2p3.fr   2
    1                                    lyoeos.in2p3.fr   3
    1                                 lyogrid06.in2p3.fr   3
    0                                   maite.iihe.ac.be   2
    0                             node12.datagrid.cea.fr   2
    0                                        nute.csc.fi   2
    0                               osg-se.sprace.org.br   2
    1                                 pcncp22.ncp.edu.pk   2
    0                                  polgrid4.in2p3.fr   2
    0                                     pool01.ifca.es   2
    0                                     pool02.ifca.es   2
    0                                     pool03.ifca.es   2
    0                                     pool04.ifca.es   2
    0                                     pool05.ifca.es   2
    0                                     pool06.ifca.es   2
    0                                     pool07.ifca.es   2
    0                                     pool08.ifca.es   2
    0                             pubxrootd.hep.wisc.edu   2
    0                             redirector.t2.ucsd.edu   2
    0                                    sbgse1.in2p3.fr   2
    0                              se01.grid.nchc.org.tw   2
    0                                        se3.itep.ru   2
    0                                      se.cis.gov.pl   2
    0                                se-xrd01.jinr-t1.ru   1
    0                             ss-01.recas.ba.infn.it   2
    0                             ss-02.recas.ba.infn.it   2
    0                             ss-03.recas.ba.infn.it   2
    0                                stormgf1.pi.infn.it   2
    1                                stormgf2.pi.infn.it   2
    1                                stormgf3.pi.infn.it   2
    1                                  storm.mib.infn.it   3
    0                            t2-cms-xrootd01.desy.de   2
    0                            t2-cms-xrootd02.desy.de   2
    0                            t2-cms-xrootd03.desy.de   2
    0                              t2-xrdcms.lnl.infn.it   2
    1                                      t3se01.psi.ch   3
    0                              vobox0002.m45.ihep.su   2
    0                              xroot02.ncg.ingrid.pt   2
    0                              xrootd01-cmst1.pic.es   1
    0                              xrootd02-cmst1.pic.es   1
    0                      xrootd-cms-01.cr.cnaf.infn.it   1
    0                      xrootd-cms-02.cr.cnaf.infn.it   1
    0                               xrootd.cmsaf.mit.edu   2
    0                            xrootd-es-cie.ciemat.es   2
    0                             xrootd.hepgrid.uerj.br   2
    0                                 xrootd.hep.kbfi.ee   2
    0                               xrootd-local.unl.edu   2
    0                             xrootd.rcac.purdue.edu   2
    0                        xrootd-redir.ultralight.org   2
    1        xrootd-vanderbilt.sites.opensciencegrid.org   2
    1                                  xroot.pp.rl.ac.uk   2

