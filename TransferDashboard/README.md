# Transfer Team - Dashboard
https://cmsmonitoring.web.cern.ch/cmsmonitoring/

### Setup
* set the variables
  ```sh
  # directory structure
  www=/afs/cern.ch/work/m/mtaze/cmsmonitoring
  src=$www/monitoring-src

  # variables for freeze script
  out=$www
  base_url=/cmsmonitoring
* copy the project or clone the repo with sparse-checkout
  ```sh
  mkdir $src
  cp -r ~/TransferTeam/TransferDashboard/* $src
  ```
* install the packages and set the virtual environment
  ```sh
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
  (cd monitoring; python freeze.py $base_url $out)

  # deactivate the environment
  deactivate
  ```
* if all are completed successfuly, set the acrontab
  * Update the DataCollector output dir

    ```
    $src -> /afs/cern.ch/work/m/mtaze/cmsmonitoring/monitoring-src
    vim $src/DataCollector/config.cfg
    # update the output directories
    $out_tranfer = '/afs/cern.ch/work/m/mtaze/cmsmonitoring/monitoring-src/monitoring/static/data/transfers.json';
    $out_error = '/afs/cern.ch/work/m/mtaze/cmsmonitoring/monitoring-src/monitoring/static/data/errors.json';
    $out_storage = '/afs/cern.ch/work/m/mtaze/cmsmonitoring/monitoring-src/monitoring/static/data/storages.json';
    ```
  * make ```monitoring_crontab.sh``` script executable and set the acrontab (do not forget to update the paths)

    ```sh
    # variables
    www=/afs/cern.ch/work/m/mtaze/cmsmonitoring;
    src=$www/monitoring-src
    out=$www
    base_url=/cmsmonitoring

    # run in the local scope to prevenent environment collision
    (
      # set phedex environment before runnning the collectors
      source ~/phedex/PHEDEX-micro/etc/profile.d/env.sh;

      # collect the data
      $src/DataCollector/TransferDataCollector.pl --db ~/param/DBParam:Prod/Reader;
      $src/DataCollector/ErrorDataCollector.pl --db ~/param/DBParam:Prod/Reader;
      $src/DataCollector/StorageDataCollector.pl --db ~/param/DBParam:Prod/Reader;
    )

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
  * ./DataCollector/StorageDataCollector.pl

#### Config file
* Located at ./DataCollector/config.cfg
* As application reads the JSON files produced by Collectors, do not forget to update output directories accordingly
* New sites or error regex can easily be added

```perl
our (@errorList,@siteList,@storageList);
our ($out_error,$out_tranfer,$out_storage);

# used in ErrorDataCollector
# error type which will be used to query corresponding column
# t: transfer log
# d: detail Log
# v: validate Log
@errorList = (
               {name=>'Missing_File', regex=>'%No%file%', type=>'d'},
               {name=>'Checksum_Mismatch', regex=>'%checksums do not match%', type=>'d'},
               {name=>'Expired_Proxy', regex=>'%expired % minutes ago%', type=>'t'}
             );

# used in TransferDataCollector
@siteList = (
              'T1_ES_PIC_MSS',
              'T1_FR_CCIN2P3_MSS',
              'T1_DE_KIT_Disk',
              'T2_CH_CERN'
            );

# used in StorageDataCollector
@storageList = (
              'T0_CH_CERN_MSS',
              'T1_UK_RAL_MSS',
              'T1_US_FNAL_MSS',
            );

# output JSON files will be written to the following paths
$out_tranfer = '/afs/cern.ch/work/m/mtaze/cmsmonitoring/monitoring-src/monitoring/static/data/transfers.json';
$out_error = '/afs/cern.ch/work/m/mtaze/cmsmonitoring/monitoring-src/monitoring/static/data/errors.json';
$out_storage = '/afs/cern.ch/work/m/mtaze/cmsmonitoring/monitoring-src/monitoring/static/data/storages.json';
```

### API Endpoints
| Method | Endpoint                           | Description
|--------|------------------------------------|--------------------------------------------------------
| GET    | /                                  | Shows all current monitoring pages in the system
| GET    | /transfer/{site_name}              | Shows the transfers for the given site
| GET    | /error/{error_text}                | Shows the errors with the given text
| GET    | /storage/{site_name}               | Shows the storage usage for the given site
