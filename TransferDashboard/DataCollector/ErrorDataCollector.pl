#!/usr/bin/env perl
use strict;
use warnings;
use Getopt::Long;
use PHEDEX::Core::DB;
use JSON;

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
      LEFT JOIN t_dps_subs_dataset sd ON sd.dataset = bl.dataset 
      LEFT JOIN t_dps_subs_block sb ON sb.block = xf.inblock
    WHERE xe.log_detail like :error_text AND (sd.destination = xe.to_node OR sb.destination = xe.to_node)
    GROUP BY xf.id,xf.logical_name,ns.name,nd.name
};

# read the config file
do('config.cfg');
our ($errorList, $out_error);

for(keys %$errorList){
    # execute the query
    my %params = (":error_text" => $errorList->{$_});
    my $q = &dbexec($dbh, $sql, %params);

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
    
    
    $data{'errors'}{$_} = \@errorData;
}

# store the time when we collect the data
$data{'time_create'} = time;

my $json = encode_json \%data;
#print $json;

open(my $fh, '>', $out_error) or die "Could not open file";
print $fh $json;
close $fh;

&disconnectFromDatabase ($self, $dbh, 1);
