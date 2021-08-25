#!/bin/bash
list1=$(grep ^T[0-9]_ create_fedmaps.log | awk '{print $1}' | sort -u)
list2=$(cat aaa_federation.log | sed "s#'siteName'#\nsiteName'#g" | grep ^siteName | awk '{print $2" "$13" "$15" "$17}'  | grep timeout  | cut -d\' -f2 | sort -u)

echo  "$(echo $list1)"
echo  "$(echo $list2)"

exit 0
