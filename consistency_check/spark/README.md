
# Spark code to run consistency between DBS and Phedex databases



## Basic setup


login to lxplus7.cern.ch


**sh setup.sh**



## run dbs and phedex consistency check on spark:

Example : python dbs_phedex_consistency.py --timestamp 2019-12-09 --dbs invalid --phedex present --output hdfs://analytix/user/pjasal/


## It returns the list of file which are invalidated by the unified for bad workflows
Example : 
--timestamp argument for checking the list for last n number of days 

python filemismatch.py --timestamp 7
