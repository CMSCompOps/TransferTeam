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
    ErrorDataCollector.pl --db ~/param/DBParam:Prod/Reader
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

# read the config file
do($Bin.'/config.cfg');
our (@errorList, $out_error);

my $sql = qq{
    SELECT
      xf.id,
      xf.logical_name, 
      ns.name source,
      nd.name destination
    FROM
      t_xfer_error xe
      JOIN t_xfer_file xf ON xf.id = xe.fileid
      JOIN t_dps_block bl ON xf.inblock = bl.id  
      JOIN t_adm_node nd ON nd.id = xe.to_node
      JOIN t_adm_node ns ON ns.id = xe.from_node
      LEFT JOIN t_xfer_replica xr ON xr.fileid = xe.fileid AND xr.node = xe.to_node
      LEFT JOIN t_dps_subs_dataset sd ON sd.dataset = bl.dataset 
      LEFT JOIN t_dps_subs_block sb ON sb.block = xf.inblock
    WHERE xr.id IS NULL AND (sd.destination = xe.to_node OR sb.destination = xe.to_node) AND xe.{COLUMN} LIKE :error_text
    GROUP BY xf.id,xf.logical_name,ns.name,nd.name
};

my $sqlNew;
foreach(@errorList){
    # take care of where clause
    ($sqlNew = $sql) =~ s/{COLUMN}/log_xfer/ if($_->{'type'} eq 't');
    ($sqlNew = $sql) =~ s/{COLUMN}/log_detail/ if($_->{'type'} eq 'd');
    ($sqlNew = $sql) =~ s/{COLUMN}/log_validate/ if($_->{'type'} eq 'v');

    # execute the query    
    my %params = (":error_text" => $_->{'regex'});
    my $q = &dbexec($dbh, $sqlNew, %params);

    my @errorData;

    # iterate over result set
    while(my $ref = $q->fetchrow_hashref) {
    	my %error;
        $error{'fileid'} = ${$ref}{'ID'};
        $error{'lfn'} = ${$ref}{'LOGICAL_NAME'};
        $error{'source'} = ${$ref}{'SOURCE'};
        $error{'destination'} = ${$ref}{'DESTINATION'};
        
        push @errorData, \%error;
    }
    
    
    $data{'errors'}{$_->{'name'}} = \@errorData;
}

# store the time when we collect the data
$data{'time_create'} = time;

my $json = encode_json \%data;
#print $json;

open(my $fh, '>', $out_error) or die "Could not open file";
print $fh $json;
close $fh;

&disconnectFromDatabase ($self, $dbh, 1);
