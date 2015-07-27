# Transfer Team - Dashboard

http://transferteam.cern.ch

### Local Installation using VirtualBox
1) Install [Vagrant](https://www.vagrantup.com/) and [VirtualBox](https://www.virtualbox.org/)

2) Connect and run the application
```sh
vagrant ssh
cd /vagrant/monitoring/
python application.py
```

3) Check the page on your browser
http://localhost:8080


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
our ($errorList,@siteList);
our ($out_error,$out_tranfer);

$errorList = {
               'Missing_File'=>'%No%file%',
               'Checksum_Mismatch'=>'%checksums do not match%'
             };

@siteList = (
              'T1_DE_KIT_Disk',
              'T1_ES_PIC_Disk',
              'T1_FR_CCIN2P3_Disk',
              'T1_IT_CNAF_Disk',
              'T1_RU_JINR_Disk',
              'T1_UK_RAL_Disk',
              'T1_US_FNAL_Disk',
            );

$out_tranfer = '/afs/cern.ch/user/m/mtaze/Project/monitoring/static/data/transfers.json';
$out_error = '/afs/cern.ch/user/m/mtaze/Project/monitoring/static/data/errors.json';
```

#### Running the Collectors regularly
* You can use crontabs to run Collectors regularly
```sh
./DataCollector/TransferDataCollector.pl --db ~/param/DBParam:Prod/Meric
./DataCollector/ErrorDataCollector.pl --db ~/param/DBParam:Prod/Meric
```
* output will be written to ```$out_tranfer``` and ```out_error```, make sure that flask application reads these files


### API Endpoints
| Method | Endpoint                           | Description
|--------|------------------------------------|--------------------------------------------------------
| GET    | /                                  | Shows all current monitoring pages in the system
| GET    | /transfer/{node_name}              | Shows the transfers for the given node name
| GET    | /error/{error_text}                | Shows the errors with the given text
