#!/bin/bash
for h in $( grep Srv out/xrdmapc_all_0.txt  | awk '{print $2}' | cut -d: -f1 | grep -v \\[ | sort -u ) ; do
   python findSitename.py $h
   break
done
