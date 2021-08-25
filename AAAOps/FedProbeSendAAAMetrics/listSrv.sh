#!/bin/bash
for h in $( grep Srv out/xrdmapc_all_0.txt  | awk '{print $2}' | cut -d: -f1 | grep -v \\[ | sort -u ) ; do
   echo $h $(ping -c 1 $h | grep ^PING | cut -d\( -f2 | cut -d\) -f1)

done
