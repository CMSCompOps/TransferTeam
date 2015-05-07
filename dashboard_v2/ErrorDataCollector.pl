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
      join t_xfer_file xf on xf.id = xe.fileid
      join t_adm_node nd on nd.id = xe.to_node
      join t_adm_node ns on ns.id = xe.from_node
    WHERE xe.log_detail like :error_text
    GROUP BY xf.id,xf.logical_name,ns.name,nd.name
};


my @errorList = ('%No%file%','%checksum%match');

foreach(@errorList){
    # execute the query
    my %params = (":error_text" => $_);
    my $q = &dbexec($dbh, $sql, %params);
    
    my @errorData;
    
    # iterate over result set
    while(my $ref = $q->fetchrow_hashref) {
    	my %error;
    	print join (", ", %{$ref}), "\n";
        $error{'fileid'} = ${$ref}{'ID'};
        $error{'lfn'} = ${$ref}{'LOGICAL_NAME'};
        $error{'source'} = ${$ref}{'SOURCE'};
        $error{'destination'} = ${$ref}{'DESTINATION'};
        
        push @errorData, \%error;
    }
    
    
    $data{$_} = \@errorData;
}

my $json = encode_json \%data;
print $json;

my $filename = 'error.json';
open(my $fh, '>', $filename) or die "Could not open file";
print $fh $json;
close $fh;

    
#while ( @h = $q->fetchrow() ) {
#    foreach ( @h ) {
#        $_ = '' unless defined $_;
#    }
#    print join("\n", @h);
#}
#while(my $ref = $q->fetchrow_arrayref) {
#    print join (", ", @{$ref}), "\n";
#}

&disconnectFromDatabase ($self, $dbh, 1);
