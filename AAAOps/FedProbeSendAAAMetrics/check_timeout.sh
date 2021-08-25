#!/bin/bash
endpoints=$(grep ^T[0-9]_ create_fedmaps.log    | awk '{print $2}' | sort -u)
for e in $endpoints ; do
    #echo $e
    log=tmp/$(echo $e | sed 's#:##g').log
    xrdfs $e query config version > $log 2>&1 &
    theps=$!
    i=0
    while [ $i -lt 30 ] ; do
          
         ps auxww | grep -v grep | grep $theps | awk '{print "+"$2"+"}' | grep -q "+"$theps"+"
        
         [ $? -ne 0 ] && break
         i=$(expr $i + 1)
         sleep 1
    done
    echo $i $e $(cat $log)
done
