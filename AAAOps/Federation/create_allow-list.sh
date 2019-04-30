#!/bin/bash

BASE=/root/
FEDINFO=/opt/TransferTeam/AAAOps/Federation/
export XRD_NETWORKSTACK=IPv4

declare -a redirectors=("xrdcmsglobal01.cern.ch:1094" "xrdcmsglobal02.cern.ch:1094" "cms-xrd-transit.cern.ch:1094")

for j in "${redirectors[@]}";do
	if [ "$j" == "xrdcmsglobal01.cern.ch:1094" ] || [ "$j" == "xrdcmsglobal02.cern.ch:1094" ]; then
		#query european reginal redirectors
		xrdmapc --list all "$j" | grep -E 'xrootd.ba.infn.it|xrootd-redic.pi.infn.it|llrxrd-redir.in2p3.fr:1094' | awk '{print $3}' | cut -d ':' -f1 > $BASE/tmp_euRED_$j	
		xrdmapc --list all "$j" | grep -E 'cmsxrootd2.fnal.gov|xrootd.unl.edu' | awk '{print $3}' | cut -d ':' -f1 > $BASE/tmp_usRED_$j
		for i in $(cat $BASE/tmp_euRED_$j);do
			xrdmapc --list all $i:1094 > $BASE/tmp_$i
			cat $BASE/tmp_$i | awk '{if($2=="Man") print $3; else print $2}' | tail -n +2 >> $BASE/tmp_total_eu_$j
		done
		
		for k in $(cat $BASE/tmp_usRED_$j);do
			xrdmapc --list all $k:1094 > $BASE/tmp_us_$k	
			cat $BASE/tmp_us_$k | awk '{if($2=="Man") print $3; else print $2}' | tail -n +2 >> $BASE/tmp_total_us_$j
		done
	

		cat $BASE/tmp_total_eu_$j | cut -d : -f1 | grep -v "\[" | sort -u > $FEDINFO/in/prod_$j.txt 
		cat $BASE/tmp_total_us_$j | cut -d : -f1 | grep -v "\[" | sort -u >> $FEDINFO/in/prod_$j.txt 
		cat $BASE/tmp_total_eu_$j | cut -d : -f1 | grep -v "\[" | sort -u | awk -F. '{print "*."$(NF-2)"."$(NF-1)"."$NF}' | sort -u > $FEDINFO/out/list_eu_$j.allow
		cat $BASE/tmp_total_us_$j | cut -d : -f1 | grep -v "\[" | sort -u | awk -F. '{print "*."$(NF-2)"."$(NF-1)"."$NF}' | sort -u > $FEDINFO/out/list_us_$j.allow
		rm hostIPv4.txt hostIPv6.txt
		for f in $(cat $FEDINFO/in/prod_$j.txt);do
			if [ "$f" != "${1#*[0-9].[0-9]}" ]; then
				echo $f >> hostIPv4.txt 
			elif [ "$f" != "${1#*:[0-9a-fA-F]}" ]; then
				echo $f >> hostIPv6.txt
			fi
		

		done	
	else
		xrdmapc --list all "$j" | tail -n +2 | awk '{if($2=="Man") print $3; else print $2}' > $BASE/tmp_total
		cat $BASE/tmp_total | cut -d : -f1 | sort -u > $FEDINFO/in/trans.txt
		
		rm transit-hostIPv4.txt transit-hostIPv6.txt
		for f in $(cat $FEDINFO/in/trans.txt);do
			if [ "$f" != "${1#*[0-9].[0-9]}" ]; then
				echo $f >> transit-hostIPv4.txt 
			elif [ "$f" != "${1#*:[0-9a-fA-F]}" ]; then
				echo $f >> transit-hostIPv6.txt
			fi
		done	
	fi	
	  

	rm $BASE/tmp_*

done

diff $FEDINFO/in/prod_xrdcmsglobal01.cern.ch\:1094.txt $FEDINFO/in/prod_xrdcmsglobal02.cern.ch\:1094.txt 
stat=$(echo $?)
if [ $stat == 1 ]; then
	cat $FEDINFO/in/prod_xrdcmsglobal01.cern.ch\:1094.txt $FEDINFO/in/prod_xrdcmsglobal02.cern.ch\:1094.txt | sort -u > $FEDINFO/in/prod.txt	
	cat $FEDINFO/out/list_eu_xrdcmsglobal01.cern.ch\:1094.allow $FEDINFO/out/list_eu_xrdcmsglobal02.cern.ch\:1094.allow | sort -u > $FEDINFO/out/list_eu.allow
	cat $FEDINFO/out/list_us_xrdcmsglobal01.cern.ch\:1094.allow $FEDINFO/out/list_us_xrdcmsglobal02.cern.ch\:1094.allow | sort -u > $FEDINFO/out/list_us.allow
 
else
	cp $FEDINFO/in/prod_xrdcmsglobal02.cern.ch\:1094.txt $FEDINFO/in/prod.txt
	cp $FEDINFO/out/list_us_xrdcmsglobal01.cern.ch\:1094.allow $FEDINFO/out/list_us.allow
	cp $FEDINFO/out/list_eu_xrdcmsglobal01.cern.ch\:1094.allow $FEDINFO/out/list_eu.allow
	
fi	


echo "    "  >> $FEDINFO/out/list_us.allow
echo "* redirect cms-xrd-transit.cern.ch+:1213" >> $FEDINFO/out/list_us.allow

echo "    "  >> $FEDINFO/out/list_eu.allow
echo "* redirect cms-xrd-transit.cern.ch+:1213" >> $FEDINFO/out/list_eu.allow



#cat $FEDINFO/in/prod.txt | cut -d : -f1 | sort -u | awk -F. '{if ($NF == "uk" || $NF == "fr" || $NF == "it" || $(NF-1) == "cern" ) print $(NF-2)"."$(NF-1)"."$NF; else if ( $(NF-1) == "vanderbilt" ) print $(NF-3)"."$(NF-2)"."$(NF-1)"."$NF; else if ( $(NF-1) == "mit" ) print $(NF-2)"."$(NF-1)"."$NF;  else print $(NF-1)"."$NF}' | sort -u > $FEDINFO/in/prod_domain.txt

#Quick fix for "[" character in prod.txt 
cat $FEDINFO/in/prod.txt | awk '{ if ($1 == "[2804") print "Unknown.Host"; else print $1;}' > $FEDINFO/in/tmp
cp $FEDINFO/in/tmp $FEDINFO/in/prod.txt
rm $FEDINFO/in/tmp



cat $FEDINFO/in/prod.txt |  sort -u | awk -F. '{if ($NF == "uk" && $(NF-2) != "rl" || $NF == "fr" || $(NF-1) == "cern" || $(NF-1) == "fnal" ) print $(NF-2)"."$(NF-1)"."$NF; else if ( $NF == "it" && $(NF-2) == "cnaf") print $(NF-4)"."$(NF-2); else if ( $NF == "it" && $(NF-2) != "cnaf" ) print $(NF-2)"."$(NF-1)"."$NF; else if ( $(NF-1) == "vanderbilt" ) print $(NF-3)"."$(NF-2)"."$(NF-1)"."$NF; else if ( $(NF-1) == "mit" ) print $(NF-2)"."$(NF-1)"."$NF; else if ( $NF == "uk" && $(NF-2) == "rl" ) print $(NF-3)"."$(NF-2)"."$(NF-1)"."$NF; else if ( $NF == "kr") print $(NF-2)"."$(NF-1)"."$NF; else if ( $NF == "be" ) print $(NF-2)"."$(NF-1)"."$NF; else print $(NF-1)"."$NF}' | sort -u > $FEDINFO/in/prod_domain.txt

cat $FEDINFO/in/trans.txt | cut -d : -f1 | sort -u | awk -F. '{if ($NF == "uk" || $NF == "fr" || $NF == "kr" || $NF == "it" || $NF == "ch" && $(NF-2) != "cnaf" ) print $(NF-2)"."$(NF-1)"."$NF; else if ($NF == "it" && $(NF-2) == "cnaf" ) print $(NF-4)"."$(NF-3)"."$(NF-2)"."$(NF-1)"."$NF; else print $(NF-1)"."$NF}' | sort -u > $FEDINFO/in/trans_domain.txt
