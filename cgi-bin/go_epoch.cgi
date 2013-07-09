#!/usr/bin/env perl

use strict;
use warnings;

=head1 NAME

experiment_epoch.cgi - CGI script to view the functional domain combinations for a given experiment within a specific time epoch.

=head1 DESCRIPTION

This module has been released as part of the TraP Project code base.

Uses most of the Gene Ontology tables from TRAP.

=head1 AUTHOR

B<Matt Oates> - I<Matt.Oates@bristol.ac.uk>

=head1 NOTICE

B<Matt Oates> (2012) First features added.

=head1 LICENSE AND COPYRIGHT

B<Copyright 2011 Matt Oates, Owen Rackham, Adam Sardar>

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

use lib qw/lib/;

=head1 DEPENDANCY

=over 4

=item B<CGI> Used just for the CGI boiler plate.

=item B<Template> Everything else CGI content/rendering related.

=item B<CGI::Carp> Die/Warn messages go to the browser prettyafied.

=item B<JSON::XS> Deal with JSON efficiently.

=item B<Data::Dumper> Used for debug output.

=back

=cut
use CGI; #Use this for purely GET POST values, nothing more.
use Template; #Use this to render content NOT CGI.pm!!!
use CGI::Carp qw/fatalsToBrowser/; #Force error messages to be output as HTML
use JSON::XS;
use Data::Dumper; #Allow easy print dumps of datastructures for debugging
use HTML::Entities;
use TraP::SQL::ExperimentEpoch qw/:all/;

=head1 FUNCTIONS DEFINED

=over 4
=cut

=item * sanitize
Function to sanitize CGI input before assignment
=cut
sub sanitize {
    my $cgi = shift;
    my $ok = s/[^a-zA-Z0-9 ,-:>\t]//go; # allowed characters
    foreach my $param ( $cgi->param ) {
        my $sanitary = HTML::Entities::decode($cgi->param($param));
        $sanitary =~ $ok;
        $cgi->param($param, $sanitary);
    }
} 

=pod

=back

=cut

my $cgi = CGI->new;
sanitize($cgi);

#Things you should use CGI for!
my $experiment = $cgi->param('experiment');
my $epoch = $cgi->param('epoch');

#Some templating options
my $config = {
   INCLUDE_PATH => '../templates',  # or list ref
   INTERPOLATE  => 1,               #Expand "$var" in plain text
   POST_CHOMP   => 1,               #Cleanup whitespace
   EVAL_PERL    => 0,               #Evaluate Perl code blocks
};

#Create Template object
my $template = Template->new($config);
my $epoch_name = epoch_id_to_name($epoch);
my $experiment_name = experiment_id_to_name($experiment);

#Define template variables for replacement, notice it ca be a subref!
my $stash = {
    'title'  => "Innovations for <i>$experiment_name</i> from the <strong>$epoch_name</strong> epoch.",
    'experiment' => $experiment,
    'epoch'      => $epoch,
    'epoch_name' => $epoch_name,
    'functions'  => {
                      molecular      => [go_function_by_tfidf($experiment,$epoch,'m')],
                      cellcomponent  => [go_function_by_tfidf($experiment,$epoch,'c')],
                      bioprocess     => [go_function_by_tfidf($experiment,$epoch,'b')]
                    }
};
print $cgi->header();
# process input template, substituting variables
$template->process('experiment_epoch.tt', $stash) or die $template->error();

=head1 TODO

=over 4

=item Add feature here...

=back

=cut

1;
