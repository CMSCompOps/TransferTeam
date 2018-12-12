# Usage of Storage Backend 
  
With this script, you can print T1&T2&T3 sites' storage system and version.  

  * General usage, it prints all storage systems: 
  	`python checkVersion.py`
  * If you want to be specific, i.e you want to check sites which have DPM storage system, run like this: 
    `python checkVersion.py | grep DPM`
  * Typically, the following storage systems are supported:
	* dCache ---> `python checkVersion.py | grep dCache` or `python checkVersion.py | grep dcache`
	* DPM   ---> `python checkVersion.py | grep DPM`
	* HDFS  ---> `python checkVersion.py | grep HDFS`
	* StoRM ---> `python checkVersion.py | grep StoRM`
	* BeStMan (Hadoop, Lustre...?) ---> `python checkVersion.py | grep bestman`
