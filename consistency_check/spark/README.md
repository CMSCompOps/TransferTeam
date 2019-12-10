
# Spark code to run consistency between DBS and Phedex databases



## Basic lxplus7 setup


login to lxplus7.cern.ch


**sh setup.sh**



## run dbs and phedex consistency check on spark:

argument --dbs takes values : "invalid" , "deleted" , "valid"
argument --phedex takes values : "missing" , "present"
argument --output specify the user area on analytix cluster

Example : python dbs_phedex_consistency.py --dbs invalid --phedex present --output hdfs://analytix/user/username/


## It returns the list of file which are invalidated by the unified for bad workflows
Example : 
--timestamp argument for checking the list for last n number of days 

python filemismatch.py --timestamp 7
