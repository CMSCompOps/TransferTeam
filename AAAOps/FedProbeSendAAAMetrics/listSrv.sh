#!/bin/bash
ipv= ; ipos=2
[ $# -gt 0 ] && { ipv=6 ; ipos=3 ; } ;
[ -f out/xrdmapc_all_0.txt ] || exit 1
for h in $( grep Srv out/xrdmapc_all_0.txt  | awk '{print $2}' | cut -d: -f1 | grep -v \\[ | sort -u ) ; do

   echo $h $(ping${ipv} -c 1 $h | grep ^PING | cut -d\( -f${ipos} | cut -d\) -f1)
   #sleep 1
done
