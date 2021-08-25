#!/bin/bash
n=1000 ; xrdmapc --list all cms-xrd-global01.cern.ch:1094 2>/dev/null |  grep -A $n ^1  | grep -B $n kr | grep "^1\|cms-t2-se01.sdfarm.kr"
n=1000 ; xrdmapc --list all cms-xrd-global.cern.ch:1094 2>/dev/null |  grep -A $n ^1  | grep -B $n xrootd-cms-01.cr.cnaf.infn.it:0 | grep "^1\|xrootd-cms-01.cr.cnaf.infn.it:0"
n=1000 ; xrdmapc --list all cms-xrd-global.cern.ch:1094 2>/dev/null |  grep -A $n ^2  | grep -B $n xrootd-cms-01.cr.cnaf.infn.it:0 | grep "^2\|xrootd-cms-01.cr.cnaf.infn.it:0"
n=1000 ; xrdmapc --list all cms-xrd-global.cern.ch:1094 2>/dev/null |  grep -A $n ^2  | grep -B $n xrootd-cms-01.cr.cnaf.infn.it:0 | grep -B 1 "^2\|xrootd-cms-01.cr.cnaf.infn.it:0" 

