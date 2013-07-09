#!/usr/bin/env perl
package TraP::SQL::GoEpoch;

use strict;
use warnings;
our $VERSION = '1.00';
use base 'Exporter';

our %EXPORT_TAGS = (
'all' => [ qw/
go_freq_by_epoch
epoch_id_to_name
experiment_id_to_name
/ ],
);
our @EXPORT_OK = ( @{ $EXPORT_TAGS{'all'} } );
our @EXPORT = qw//;

=head1 NAME

TraP::SQL::ExperimentEpoch v1.0 - Deals with functional annotation of experiments at a given time epoch.

=head1 DESCRIPTION

This module has been released as part of the TraP Project code base.

=head1 EXAMPLES

=head1 AUTHOR

B<Matt Oates> - I<Matt.Oates@bristol.ac.uk>

=head1 NOTICE

B<Matt Oates> (2012) First features added.

=head1 LICENSE AND COPYRIGHT

B<Copyright 2012 Matt Oates, Owen Rackham, Adam Sardar>

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

=cut

=head1 DEPENDANCY

B<Data::Dumper> Used for debug output.

=cut

use lib qw'../../';
use Utils::SQL::Connect qw/:all/;
use Supfam::Utils qw(:all);
use Data::Dumper; #Allow easy print dumps of datastructures for debugging


=head1 FUNCTIONS DEFINED

=over 4
=cut

=item * function_by_tfidf
Function to get all the human cell type experiment ids
biological_process,molecular_function,cellular_componenty
=cut
sub go_function_by_tfidf {
    my ($experiment_id, $epoch, $namespace, $limit) = @_;
    my %namespaces = (b => 'biological_process',m => 'molecular_function',c => 'cellular_component');
    $namespace = 'm' unless $namespace;
    $limit = 10 unless $limit;
    my @functions;
    my $dbh = dbConnect('trap');
    my $sth = $dbh->prepare("SELECT distinct go_id, name, tfidf 
                             FROM go_num_experiment_epoch, superfamily.GO_info, superfamily.GO_ic
                             WHERE go_num_experiment_epoch.experiment_id = ?
                             AND go_num_experiment_epoch.taxon_id = ?
                             AND superfamily.GO_info.namespace = ?
                             AND go_num_experiment_epoch.go_id = superfamily.GO_info.go 
                             AND go_num_experiment_epoch.go_id = superfamily.GO_ic.go
                             AND superfamily.GO_ic.include >= 3
                             ORDER BY go_num_experiment_epoch.tfidf DESC
                             LIMIT ?;");

    $sth->execute($experiment_id,$epoch,$namespaces{$namespace},$limit);

    while ( my ($go_id, $name, $tfidf) = $sth->fetchrow_array() ) {
        #$name =~ s/ /&nbsp;/g;
        push @functions, {go_id => $go_id, name => ucfirst($name), tfidf => int $tfidf};
    }
    dbDisconnect($dbh);
    return @functions;
}

=item * epoch_id_to_name
Function to get the human friendly name for this epoch
=cut
sub epoch_id_to_name {
    my ($epoch) = @_;
    my $dbh = dbConnect('trap');
    my ($name) = $dbh->selectrow_array("SELECT name FROM common_taxa_names WHERE genome = '' AND taxon_id = ?;",undef,$epoch);
    dbDisconnect($dbh);
    return $name;
}

=item * experiment_id_to_name
Function to get the human friendly name for this experiment
=cut
sub experiment_id_to_name {
    my ($experiment) = @_;
    my $dbh = dbConnect('trap');
    my ($name) = $dbh->selectrow_array("SELECT sample_name FROM experiment WHERE experiment_id = ?;",undef,$experiment);
    dbDisconnect($dbh);
    return $name;
}
 
=pod
=back
=cut

1;
__END__

