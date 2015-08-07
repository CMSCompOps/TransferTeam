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
(cd monitoring; python freeze.py $base_url $out)
deactivate
