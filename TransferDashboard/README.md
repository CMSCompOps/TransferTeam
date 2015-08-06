# Transfer Team - Dashboard
https://cmsmonitoring.web.cern.ch/cmsmonitoring/

### Setup
* install python packages and set the virtual environment
```sh
# directory structure
www=/afs/cern.ch/work/m/mtaze/cmsmonitoring;
src=$www/monitoring-src

out=$www
base_url=/cmsmonitoring

# copy the project into www
cp -r ~/TransferTeam/TransferDashboard/monitoring $src
cp -r ~/TransferTeam/TransferDashboard/DataCollector $src/

# install packages
yum install python-pip
pip install virtualenv

# init and activate the virtual env
cd $src
virtualenv venv
source venv/bin/activate
# install the packages in the virtual env
pip install Flask Frozen-Flask Flask-FlatPages
```
* build the static content using flask application
```sh
python freeze.py $base_url $out

# deactivate the environment
deactivate
```
* if all are completed successfuly, set the acrontab
  * Update the DataCollector output dir

    ```
    vim $src/DataCollector/config.cfg
    # update the following lines
    # $src -> /afs/cern.ch/work/m/mtaze/cmsmonitoring/monitoring-src
    $out_tranfer = '/afs/cern.ch/work/m/mtaze/cmsmonitoring/monitoring-src/static/data/transfers.json';
    $out_error = '/afs/cern.ch/work/m/mtaze/cmsmonitoring/monitoring-src/static/data/errors.json';
    ```
  * save the following in a script called ```monitoring_crontab.sh``` in $src folder and make it executable

    ```sh
    # variables
    www=/afs/cern.ch/work/m/mtaze/cmsmonitoring;
    src=$www/monitoring-src
    out=$www
    base_url=/cmsmonitoring
    
    # set phedex environment before runnning the collectors
    source ~/phedex/PHEDEX-micro/etc/profile.d/env.sh
    
    # collect the data
    $src/DataCollector/TransferDataCollector.pl --db ~/param/DBParam:Prod/Reader
    $src/DataCollector/ErrorDataCollector.pl --db ~/param/DBParam:Prod/Reader
    
    # produce the static page
    cd $src
    source venv/bin/activate
    python freeze.py $base_url $out
    deactivate
    ```

### Local Installation for test purposes
```
src=~/TransferTeam/TransferDashboard/monitoring
# install packages
yum install python-pip
pip install virtualenv

# init and activate the virtual env
cd $src
virtualenv venv
source venv/bin/activate
# install the packages in the virtual env
pip install Flask 
python application.py
# check localhost:8080 in your browser
```

### Configuration

#### Data Collectors
* Collects data from TMDB, and puts the output to the directory defined in the config file in JSON format
* Requires a DBParam file to fetch data from TMDB
* Current Collectors
  * ./DataCollector/TransferDataCollector.pl
  * ./DataCollector/ErrorDataCollector.pl

#### Config file
* Located at ./DataCollector/config.cfg
* As application reads the JSON files produced by Collectors, do not forget to update output directories accordingly
* New sites or error regex can easily be added
```perl
our (@errorList,@siteList);
our ($out_error,$out_tranfer);

@errorList = (
               {name=>'Missing_File', regex=>'%No%file%', type=>'d'},
               {name=>'Checksum_Mismatch', regex=>'%checksums do not match%', type=>'d'},
               {name=>'Expired_Proxy', regex=>'%expired % minutes ago%', type=>'t'}
             );

@siteList = (
              'T1_DE_KIT_Disk',
              'T1_ES_PIC_Disk',
              'T1_FR_CCIN2P3_Disk',
              'T1_IT_CNAF_Disk',
              'T1_RU_JINR_Disk',
              'T1_UK_RAL_Disk',
              'T1_US_FNAL_Disk',
            );

$out_tranfer = '/afs/cern.ch/work/m/mtaze/cmsmonitoring/monitoring-src/static/data/transfers.json';
$out_error = '/afs/cern.ch/work/m/mtaze/cmsmonitoring/monitoring-src/static/data/errors.json';
```

#### Running the Collectors regularly
* You can use crontabs to run Collectors regularly
```sh
./DataCollector/TransferDataCollector.pl --db ~/param/DBParam:Prod/Reader
./DataCollector/ErrorDataCollector.pl --db ~/param/DBParam:Prod/Reader
```
* output will be written to ```$out_tranfer``` and ```out_error```, make sure that flask application reads these files


### API Endpoints
| Method | Endpoint                           | Description
|--------|------------------------------------|--------------------------------------------------------
| GET    | /                                  | Shows all current monitoring pages in the system
| GET    | /transfer/{node_name}              | Shows the transfers for the given node name
| GET    | /error/{error_text}                | Shows the errors with the given text
