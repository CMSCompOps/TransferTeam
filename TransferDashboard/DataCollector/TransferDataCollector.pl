#!/usr/bin/env perl
use strict;
use warnings;
use Getopt::Long;
use PHEDEX::Core::DB;
use JSON;
use FindBin '$Bin';

my (%args,@h);

&GetOptions ("db=s" => \$args{DBCONFIG},
             "help|h" => sub { &usage() });

sub usage {
    print <<"EOF";
    ./TransferDataCollector.pl --db ~/param/DBParam:Prod/Reader
EOF
}

# check arguments
if (!$args{DBCONFIG}) {
    die "Insuficient parameters, use -h for help.\n";
}

my %data;

my $self = { DBCONFIG => $args{DBCONFIG} };
my $dbh = &connectToDatabase ($self);
$dbh->{LongReadLen} = 100000;

my $sql = qq{
    SELECT 
      sp.request,sp.time_create, sp.priority, 
      nd.name as destination,
      d.name,
      reps.basis, reps.time_arrive,
      ds_stat.bytes, ds_stat.files,
      ds_rep.replica,
      reps.node_bytes, reps.node_files, reps.latest_replica,
      reps.source, reps.route_files, reps.xfer_files
    FROM
      t_dps_subs_dataset sd
      join t_dps_dataset d on d.id = sd.dataset
      join t_dps_subs_param sp on sp.id = sd.param
      join t_adm_node nd on nd.id = sd.destination
      left join
        (select
          br.node,
          b.dataset,
          coalesce(MAX(ba.time_arrive),0) time_arrive,
          wm_concat(distinct ba.basis) basis,
          wm_concat(distinct ns.name) source,
          sum(bp.route_files) route_files,
          sum(br.node_bytes) node_bytes,
          sum(br.node_files) node_files,
          sum(br.xfer_files) xfer_files,
          max(l.latest_replica) latest_replica
        from
          t_dps_block_replica br
          join t_dps_block b on br.block = b.id
          left join t_status_block_arrive ba on br.block = ba.block AND br.node = ba.destination
          left join t_status_block_path bp on br.block = bp.block AND br.node = bp.destination AND is_valid=1
          left join t_adm_node ns on ns.id = bp.src_node
          left join t_dps_block_latency l on l.block = b.id AND br.node = l.destination
        group by br.node, b.dataset
        ) reps on reps.node = sd.destination and reps.dataset = d.id
      left join
        (select
          d.id id,
          sum(b.files) files,
          sum(b.bytes) bytes
         from
          t_dps_dataset d
          join t_dps_block b on b.dataset = d.id 
         group by d.id
        ) ds_stat on ds_stat.id = d.id
      left join
        (select 
          b.dataset,
          wm_concat(distinct nr.name) replica
         from 
          t_dps_block b
          join t_dps_block_replica br on br.block = b.id 
          join t_adm_node nr on nr.id = br.node 
         group by b.dataset
        ) ds_rep on ds_rep.dataset = ds_stat.id
    WHERE
      nd.name = :node_name AND
      ds_stat.files != reps.node_files
};

# read the config file
do( $Bin.'/config.cfg');
our (@siteList, $out_tranfer);

foreach(@siteList){
    # execute the query
    my %params = (":node_name" => $_);
    my $q = &dbexec($dbh, $sql, %params);
    
    my %nodeData;
    
    # iterate over result set
    while(my $ref = $q->fetchrow_hashref) {
        if (not exists($nodeData{${$ref}{'REQUEST'}})){
            $nodeData{${$ref}{'REQUEST'}} = [];
        }
        my %dataset;

        $dataset{'name'} = ${$ref}{'NAME'};
        @{$dataset{'basis'}} = split(',', int(${$ref}{'BASIS'}));
        @{$dataset{'source'}} = split(',', ${$ref}{'SOURCE'});
        @{$dataset{'replica'}} = split(',', ${$ref}{'REPLICA'});
        $dataset{'priority'} = ${$ref}{'PRIORITY'};
        $dataset{'time_create'} = int(${$ref}{'TIME_CREATE'}) || 0;
        $dataset{'time_arrive'} = int(${$ref}{'TIME_ARRIVE'}) || 0;
        $dataset{'bytes'} = int(${$ref}{'BYTES'}) || 0;
        $dataset{'files'} = int(${$ref}{'FILES'}) || 0;
        $dataset{'node_bytes'} = int(${$ref}{'NODE_BYTES'}) || 0;
        $dataset{'node_files'} = int(${$ref}{'NODE_FILES'}) || 0;
        $dataset{'route_files'} = int(${$ref}{'ROUTE_FILES'}) || 0;
        $dataset{'xfer_files'} = int(${$ref}{'XFER_FILES'}) || 0;
        $dataset{'latest_replica'} = int(${$ref}{'LATEST_REPLICA'}) || 0;
        
        push (@{$nodeData{${$ref}{'REQUEST'}}}, \%dataset);
    }
    
    
    $data{'transfers'}{$_} = \%nodeData
}

# store the time when we collect the data
$data{'time_create'} = time;

my $json = encode_json \%data;
#print $json;

open(my $fh, '>', $out_tranfer) or die "Could not open file";
print $fh $json;
close $fh;

&disconnectFromDatabase ($self, $dbh, 1);
