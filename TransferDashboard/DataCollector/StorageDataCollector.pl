#!/usr/bin/env perl
use strict;
use Getopt::Long;
use PHEDEX::Core::DB;
use JSON;
use FindBin '$Bin';

my (%args,@h);

&GetOptions ("db=s" => \$args{DBCONFIG},
             "help|h" => sub { &usage() });

sub usage {
    print <<"EOF";
    ./StorageDataCollector.pl --db ~/param/DBParam:Prod/Reader
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
        select b.name block_name,
               b.id block_id,
               b.bytes block_bytes,
               n.id node_id,
               br.node_bytes replica_bytes,
               case when br.dest_files = 0
                    then 'n'
                    else 'y'
               end subscribed,
               br.is_custodial,
               ds.name dataset_name,
               g.name user_group
          from t_dps_block_replica br
            join t_dps_block b on b.id = br.block
            join t_dps_dataset ds on ds.id = b.dataset
            join t_adm_node n on n.id = br.node
            left join t_adm_group g on g.id = br.user_group
          where (br.node_files != 0 OR br.dest_files !=0) AND n.name = :node_name
};

# read the config file
do( $Bin.'/config.cfg');
our (@storageList, $out_storage);

foreach(@storageList){
    # execute the query
    my %params = (":node_name" => $_);
    my $q = &dbexec($dbh, $sql, %params);
    
    my %nodeData;
    
    # iterate over result set
    while(my $ref = $q->fetchrow_hashref) {
        if (not exists($nodeData{${$ref}{'DATASET_NAME'}})){
            $nodeData{${$ref}{'DATASET_NAME'}} = [];
        }
        my %dataset;

        $dataset{'name'} = ${$ref}{'DATASET_NAME'};
        $dataset{'bytes'} = ${$ref}{'BLOCK_BYTES'};
        $dataset{'node_bytes'} = ${$ref}{'REPLICA_BYTES'};
        $dataset{'custodial'} = ${$ref}{'IS_CUSTODIAL'};
        
		push (@{$nodeData{${$ref}{'DATASET_NAME'}}}, \%dataset);
    }
    
    
    $data{'storages'}{$_} = \%nodeData
}

# store the time when we collect the data
$data{'time_create'} = time;

my $json = encode_json \%data;
#print $json;

open(my $fh, '>', $out_storage) or die "Could not open file";
print $fh $json;
close $fh;

&disconnectFromDatabase ($self, $dbh, 1);
