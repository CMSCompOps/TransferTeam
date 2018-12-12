#!/bin/sh

if [ $# -lt 1 ]
then
        echo "Usage : $0 <list of cms_site_name>"
        echo "Example: $0 \"T2_AT_Vienna T2_IT_Legnaro T2_UA_KIPT\" "
        exit
fi

for site in $1;
do

    cms_site_name=$site
    #echo $cms_site_name

    se_name=`curl -ks "https://cmsweb.cern.ch/phedex/datasvc/perl/prod/lfn2pfn?node=${cms_site_name}&lfn=/store/datA&protocol=srmv2" | grep PFN | awk -F "/" '{print $3}' | awk -F ":" '{print $1}'`

    #echo $se_name

    #ldapsearch -LLL -x -H ldap://lcg-bdii.cern.ch:2170 -b mds-vo-name=LOCAL,o=grid "(&(GlueSEImplementationName=*)(GlueSEImplementationVersion=*)(GlueSEUniqueID=${se_name}))" | grep "GlueSEImplementationName:"
    #ldapsearch -LLL -x -H ldap://lcg-bdii.cern.ch:2170 -b mds-vo-name=LOCAL,o=grid "(&(GlueSEImplementationName=*)(GlueSEImplementationVersion=*)(GlueSEUniqueID=${se_name}))" | grep Implementation
    storage=$(ldapsearch -LLL -x -H ldap://lcg-bdii.cern.ch:2170 -b mds-vo-name=LOCAL,o=grid "(&(GlueSEImplementationName=*)(GlueSEImplementationVersion=*)(GlueSEUniqueID=${se_name}))" | grep GlueSEImplementationName | cut -d ":" -f2)
    storageVer=$(ldapsearch -LLL -x -H ldap://lcg-bdii.cern.ch:2170 -b mds-vo-name=LOCAL,o=grid "(&(GlueSEImplementationName=*)(GlueSEImplementationVersion=*)(GlueSEUniqueID=${se_name}))" | grep GlueSEImplementationVersion | cut -d ":" -f2)
    echo $cms_site_name $storage $storageVer	

done

