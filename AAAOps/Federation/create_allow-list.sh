#!/bin/bash

BASE=/root
FEDINFO=/root/FederationInfo
export XRD_NETWORKSTACK=IPv4

declare -a redirectors=("xrdcmsglobal01.cern.ch:1094" "xrdcmsglobal02.cern.ch:1094" "cms-xrd-transit.cern.ch:1094")

for j in "${redirectors[@]}";do
	if [ "$j" == "xrdcmsglobal01.cern.ch:1094" ] || [ "$j" == "xrdcmsglobal02.cern.ch:1094" ]; then
		xrdmapc --list all "$j" | grep -E 'xrootd.ba.infn.it|xrootd-redic.pi.infn.it|llrxrd-redir.in2p3.fr:1094' | awk '{print $3}' | cut -d ':' -f1 > $BASE/tmp_euRED_$j
		xrdmapc --list all "$j" | grep -E 'cmsxrootd1.fnal.gov|xrootd.unl.edu' | awk '{print $3}' | cut -d ':' -f1 > $BASE/tmp_usRED_$j
		for i in $(cat $BASE/tmp_euRED_$j);do
			xrdmapc --list all $i:1094 > $BASE/tmp_$i	
			cat $BASE/tmp_$i | awk '{if($2=="Man") print $3; else print $2}' | tail -n +2 >> $BASE/tmp_total_eu_$j
		done
		
		for k in $(cat $BASE/tmp_usRED_$j);do
			xrdmapc --list all $k:1094 > $BASE/tmp_us_$k	
			cat $BASE/tmp_us_$k | awk '{if($2=="Man") print $3; else print $2}' | tail -n +2 >> $BASE/tmp_total_us_$j
		done
	

		cat $BASE/tmp_total_eu_$j | cut -d : -f1 | sort -u > $FEDINFO/in/prod_$j.txt 
		cat $BASE/tmp_total_us_$j | cut -d : -f1 | sort -u >> $FEDINFO/in/prod_$j.txt 
		cat $BASE/tmp_total_eu_$j | cut -d : -f1 | sort -u | awk -F. '{print "cms.allow host " "*."$(NF-1)"."$NF}' | sort -u > $FEDINFO/out/list_eu_$j.allow
		cat $BASE/tmp_total_us_$j | cut -d : -f1 | sort -u | awk -F. '{print "cms.allow host " "*."$(NF-1)"."$NF}' | sort -u > $FEDINFO/out/list_us_$j.allow

	else
		xrdmapc --list all "$j" | tail -n +2 | awk '{if($2=="Man") print $3; else print $2}' > $BASE/tmp_total
		cat $BASE/tmp_total | cut -d : -f1 | sort -u > $FEDINFO/in/trans.txt
	fi	
	  

	rm $BASE/tmp_*

done

diff $FEDINFO/in/prod_xrdcmsglobal01.cern.ch\:1094.txt $FEDINFO/in/prod_xrdcmsglobal02.cern.ch\:1094.txt 
stat=$(echo $?)
if [ $stat == 1 ]; then
	cat $FEDINFO/in/prod_xrdcmsglobal01.cern.ch\:1094.txt $FEDINFO/in/prod_xrdcmsglobal02.cern.ch\:1094.txt | sort -u > $FEDINFO/in/prod.txt	
else
	cp $FEDINFO/in/prod_xrdcmsglobal02.cern.ch\:1094.txt $FEDINFO/in/prod.txt
fi	



#cat $FEDINFO/in/prod.txt | cut -d : -f1 | sort -u | awk -F. '{if ($NF == "uk" || $NF == "fr" || $NF == "it" || $(NF-1) == "cern" ) print $(NF-2)"."$(NF-1)"."$NF; else if ( $(NF-1) == "vanderbilt" ) print $(NF-3)"."$(NF-2)"."$(NF-1)"."$NF; else if ( $(NF-1) == "mit" ) print $(NF-2)"."$(NF-1)"."$NF;  else print $(NF-1)"."$NF}' | sort -u > $FEDINFO/in/prod_domain.txt

cat $FEDINFO/in/prod.txt |  sort -u | awk -F. '{if ($NF == "uk" && $(NF-2) != "rl" || $NF == "fr" || $(NF-1) == "cern" || $(NF-1) == "fnal" ) print $(NF-2)"."$(NF-1)"."$NF; else if ( $(NF-2) == "cnaf") print $(NF-4)"."$(NF-2); else if ( $NF == "it" && $(NF-2) != "cnaf" ) print $(NF-2)"."$(NF-1)"."$NF; else if ( $(NF-1) == "vanderbilt" ) print $(NF-3)"."$(NF-2)"."$(NF-1)"."$NF; else if ( $(NF-1) == "mit" ) print $(NF-2)"."$(NF-1)"."$NF; else if ( $(NF-2) == "rl" ) print $(NF-3)"."$(NF-2)"."$(NF-1)"."$NF; else if ( $NF == "kr") print $(NF-3)"."$(NF-2)"."$(NF-1)"."$NF; else if ( $NF == "be" ) print $(NF-2)"."$(NF-1)"."$NF; else print $(NF-1)"."$NF}' | sort -u > $FEDINFO/in/prod_domain.txt

cat $FEDINFO/in/trans.txt | cut -d : -f1 | sort -u | awk -F. '{if ($NF == "uk" || $NF == "fr" || $NF == "kr" ) print $(NF-2)"."$(NF-1)"."$NF; else if ($NF == "it" && $(NF-2) == "cnaf" ) print $(NF-4)"."$(NF-3)"."$(NF-2)"."$(NF-1)"."$NF; else if ( $(NF-2) == "ts" ) print $(NF-3)"."$(NF-2)"."$(NF-1)"."$NF; else print $(NF-1)"."$NF}' | sort -u > $FEDINFO/in/trans_domain.txt


exit 0;
