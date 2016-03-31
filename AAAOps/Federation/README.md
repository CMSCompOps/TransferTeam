# FederationInfo

Cron:
----
Cronjob is done via "create-fedfiles.sh" script. From that script, we are calling "create_allow-list.sh" and "create_fedmaps.py" 

 **create_allow-list.sh**:
	
	-Input : 
		Redirector names -> cms-xrd-global.cern.ch:1094 and cms-xrd-transit.cern.ch:1094
 
	-Purpose : 
		Query gloabal redirectors above and get the sites and regional redirectors who are subscribed to these global redirectors. 
	
	-Output : 
		Allow list of both US and EU regions are produced. 
		Host names are produced for both production and transational federation. (prod.txt and trans.txt)

  **create_fedmaps.py** :
	
	-Input : 
		1. Hostnames in in/prod.txt and in/trans.txt
		2. http://dashb-cms-vo-feed.cern.ch/dashboard/request.py/cmssitemapbdii
	-Purpose :	
		We want to convert hostnames to "cms sitenames", e.g t2-cms-xrootd01.desy.de ---> T2_DE_DESY. 
	-Output :
		JSON file which consists of 3 categories :
			1. Production Federation
			2. Transitional Federation
			3. Nowhere Sites. (Sites which are not subscribed to any redirector.)
