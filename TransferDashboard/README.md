# Transfer Team - Dashboard

http://transferteam.cern.ch

### Setup
* intall python packages and set the virtual environment
```sh
www=/afs/cern.ch/work/m/mtaze/www;
yum install python-pip
pip install virtualenv
cd $www
# init and activate the virtual env
virtualenv venv
source venv/bin/activate
# install the packages
pip install Flask Frozen-Flask Flask-FlatPages
```
* copy the project into www
```sh
cp -r ~/TransferTeam/TransferDashboard/monitoring $www/monitoring-src
cd monitoring-src
# python freeze.py BASE_URL DESTINATION
python freeze.py /transferteam/monitoring/ /afs/cern.ch/work/m/mtaze/www/monitoring

# deactivate the environment
deactivate
```
* if all are completed successfuly, set the acrontab
```sh
# collect the data
./DataCollector/TransferDataCollector.pl --db ~/param/DBParam:Prod/Reader
./DataCollector/ErrorDataCollector.pl --db ~/param/DBParam:Prod/Reader
cd /afs/cern.ch/work/m/mtaze/www
source venv/bin/activate
cd monitoring-src
python freeze.py /transferteam/monitoring/ /afs/cern.ch/work/m/mtaze/www/monitoring
deactivate
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

$out_tranfer = '/afs/cern.ch/user/m/mtaze/TransferTeam/TransferDashboard/monitoring/static/data/transfers.json';
$out_error = '/afs/cern.ch/user/m/mtaze/TransferTeam/TransferDashboard/monitoring/static/data/errors.json';
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
