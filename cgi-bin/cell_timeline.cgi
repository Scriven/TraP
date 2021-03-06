#!/usr/bin/env perl

use warnings;
use strict;

=head1 NAME

B<cell_timeline.cgi> - Display the disordered architecture for a specified SUPERFAMILY protein.

=head1 DESCRIPTION

Outputs an SVG rendering of the given proteins structual and disordered architecture. Weaker hits are included with their e-values specified as 'hanging' blocks.

An example use of this script is as follows:

To emulate SUPERFAMILY genome page style figures as closely as possible include something similar to the following in the page:

<div width="100%" style="overflow:scroll;">
	<object width="100%" height="100%" data="/cgi-bin/cell_timeline.cgi?proteins=3385949&genome=at&supfam=1&ruler=0" type="image/svg+xml"></object>
</div>

To have super duper Matt style figures do something like:

<div width="100%" style="overflow:scroll;">
	<object width="100%" height="100%" data="/cgi-bin/cell_timeline.cgi?proteins=3385949,26711867&callouts=1&ruler=1&disorder=1" type="image/svg+xml"></object>
</div>


=head1 TODO

B<HANDLE PARTIAL HITS!>

I<SANITIZE INPUT MORE!>

	* Specify lists of proteins, along with other search terms like comb string, required by SUPERFAMILY.

=head1 AUTHOR

B<Matt Oates> - I<Matt.Oates@bristol.ac.uk>

=head1 NOTICE

B<Matt Oates> (Jan 2012) First features added.

=head1 LICENSE AND COPYRIGHT

B<Copyright 2012 Matt Oates>

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.

=head1 FUNCTIONS

=over 4

=cut

use POSIX qw/ceil floor/;
use CGI;
use CGI::Carp qw(fatalsToBrowser); #Force error messages to be output as HTML
use Data::Dumper;
use DBI;
use lib 'lib';
use Utils::SQL::Connect qw/:all/;
use Supfam::Utils qw(:all);


#Deal with the CGI parameters here
my $cgi = CGI->new;

my $lim = $cgi->param('lim');
unless(defined($lim)){
        $lim =20;
}

my $cluster = $cgi->param('cluster');
my $unit = $cgi->param('unit');
my $genome = $cgi->param('genome');
unless(defined($genome)){
        $genome = 'hs';
}

my $exp = $cgi->param('exp');
unless(defined($exp)){
        $exp = 2622;
}
my $sort = $cgi->param('sort');
unless(defined($sort)){
        $sort = 'desc';
}
my @exps;
my $like = $cgi->param('like');
my $order = $cgi->param('order');
if(defined($like)){
	my $dbh = dbConnect('trap');
    #TODO need to use sample_index here to avoid sample names that have now changed!
	my $sth = $dbh->prepare("select sample_name from experiment where sample_name like '%"."$like"."%' and update_number = 7;");
	$sth->execute();
	while( my ($exp_id)=  $sth->fetchrow_array()){ 
		push (@exps,$exp_id);
	}
}elsif(defined($order)){
	if(defined($sort)){
	my $dbh = dbConnect('trap');
	my $sth = $dbh->prepare("select sample_name from snapshot_evolution_collapsed order by abs($sort);");
	$sth->execute();
	while( my ($exp_id)=  $sth->fetchrow_array()){ 
		push (@exps,$exp_id);
	}
	}
}elsif(defined($cluster)){
my $dbh = dbConnect('trap');
        my $sth = $dbh->prepare("select sample_name from experiment_cluster where cluster_id = ? order by unit_id desc;");
        $sth->execute($cluster);
        while( my ($exp_id)=  $sth->fetchrow_array()){
                push (@exps,$exp_id);
        }
}elsif(defined($unit)){
	my $dbh = dbConnect('trap');
	my $sth = $dbh->prepare("select sample_name from experiment_cluster where unit_id = ?;");
        $sth->execute($unit);
        while( my ($exp_id)=  $sth->fetchrow_array()){
                push (@exps,$exp_id);
        }
}else{
	@exps = split(/,/,$exp);
}

=item B<get_exp_name>
=cut
sub get_exp_name {
	my $exp = shift;
	my $dbh = dbConnect('trap');
	my $sth = $dbh->prepare('select sample_name from experiment where sample_name = ? ;');
	$sth->execute($exp);
	my $name;
	while( my @temp =  $sth->fetchrow_array()){ 
		$name = $temp[0];
	}
	return $name;
}

=item B<get_cluster_info>
=cut
sub get_cluster_info {
        my $exp = shift;
        my $dbh = dbConnect('trap');
        my $sth = $dbh->prepare('select unit_id,cluster_id from experiment_cluster where sample_name = ?;');
        $sth->execute($exp);
        my @name;
        while( my @temp =  $sth->fetchrow_array()){
                @name = @temp;
        }
        return \@name;
}


=item B<get_timeline>
=cut
sub get_times {
	my $exp = shift;
	my @exps = @{$exp};
	my %times;
	foreach $exp (@exps){
	my $dbh = dbConnect('trap');
	my $sth = $dbh->prepare('select collapsed_taxon_details.distance,common_taxa_names.name,snapshot_evolution_collapsed.z_score,snapshot_evolution_collapsed.taxon_id 
	from snapshot_evolution_collapsed,common_taxa_names,collapsed_taxon_details,sample_index 
	where sample_index.sample_id = snapshot_evolution_collapsed.sample_id  
	and sample_index.sample_name = ? 
	and snapshot_evolution_collapsed.taxon_id = common_taxa_names.taxon_id 
	and snapshot_evolution_collapsed.taxon_id = collapsed_taxon_details.taxon_id 
	and common_taxa_names.genome = \'\' ORDER BY collapsed_taxon_details.distance ASC;');
	$sth->execute($exp);
	
	my $results=[];	
	while(my ($distance,$label,$proportion,$taxon_id)=  $sth->fetchrow_array()){
		$times{$exp}{$distance}{'label'} = $label;
		$times{$exp}{$distance}{'size'} = $proportion;
		$times{$exp}{$distance}{'taxon_id'} = $taxon_id;
	}
	}
	return \%times;
}

sub get_norm_times {
	my $dbh = dbConnect('trap');
	my $sth = $dbh->prepare('select max(z_score),min(z_score),std(z_score) from snapshot_evolution_collapsed,collapsed_taxon_details where snapshot_evolution_collapsed.taxon_id = collapsed_taxon_details.taxon_id; ');
	$sth->execute();
	my %norm_times;
	while(my ($max,$min,$std)=  $sth->fetchrow_array()){
		$norm_times{'max'} = 4;
		$norm_times{'min'} = 4;
		$norm_times{'std'} = $std;
	}
	return \%norm_times;
}

=item B<draw_timeline>
=cut
sub draw_timeline {
	my ($width,$height,$times,$norms) = @_;
	my $diagram = '';
	my $points = 12;
	my $inc = $width/($points+2);
	my $no_samples = scalar(keys %{$times});
	my $timeline_y = $height-(6*$inc);
	
	my $tick_height = 10;

	my $scale_y = $height-(5*$inc);
	#Draw header
	$diagram .= <<EOF
<?xml version="1.0" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" 
	 "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<svg xmlns="http://www.w3.org/2000/svg"
     xmlns:xlink="http://www.w3.org/1999/xlink"
     width="$width" height="$height"
     viewBox="0 0 $width $height">
EOF
    ;
	
	#Draw the time and scale lines
	my $w = $width -100;
        my $w2 = $width -200;
	$diagram .= <<EOF
	<line x1="0" y1="$scale_y" x2="$width" y2="$scale_y" style="stroke: #333; stroke-width: 1;" />
EOF
	;

my %times = %{$times};
my $done = 0;
foreach my $exp (keys %times)	{
	my $name = get_exp_name($exp);
		#Draw the time and scale lines
	my $cluster_info=get_cluster_info($exp);
	my @cluster_info=@{$cluster_info};
	my $up = $timeline_y+($inc/2);
	my $down = $timeline_y-($inc/2);
	my $up_half = $timeline_y+($inc/4);
	my $down_half = $timeline_y-($inc/4);
	my $up_text = $timeline_y+($inc/2)+5;
	my $down_text = $timeline_y-($inc/2)+5;
	my $up_text_half = $timeline_y+($inc/4)+5;
	        my $down_text_half = $timeline_y-($inc/4)+5;
	
	$diagram .= <<EOF
	
	<line x1="15" y1="$down" x2="15" y2="$up" style="stroke: #333; stroke-width: 2;" />
	<line x1="15" y1="$timeline_y" x2="$width" y2="$timeline_y" style="stroke: #333; stroke-width: 2;" />
	<line x1="15" y1="$up" x2="$width" y2="$up" style="stroke-opacity: 0.2;stroke: #333; stroke-width: 1;" />
	<line x1="15" y1="$down" x2="$width" y2="$down" style="stroke-opacity: 0.2;stroke: #333; stroke-width: 1;" />
	 <text x="17" y="$down_text" text-anchor="right" style="font-size:14px">4</text>
	  <text x="17" y="$up_text" text-anchor="right" style="font-size:14px">-4</text>
	   <text x="17" y="$down_text_half" text-anchor="right" style="font-size:14px">2</text>
	   <text x="17" y="$up_text_half" text-anchor="right" style="font-size:14px">-2</text>
	<line x1="15" y1="$down_half" x2="$width" y2="$down_half" style="stroke-opacity: 0.1;stroke: #333; stroke-width: 1;" />
	<line x1="15" y1="$up_half" x2="$width" y2="$up_half" style="stroke-opacity: 0.1;stroke: #333; stroke-width: 1;" />
	<text x="3" y="$down_half" text-anchor="right" style="font-size:12px" transform="rotate(90 3,$down_half)">z-value</text>
	
EOF
	;
	
	    
		#Draw the labels
		my $max;
		my $downbit = $down - 15;
		$diagram .= <<EOF
		<a xlink:href="cell_timeline.cgi?exp=$exp">
		<text x="10" y="$downbit" text-anchor="right" style="font-size:25px">$name</text>
		</a>
		<a xlink:href="cell_timeline.cgi?cluster=$cluster_info[1]">                                                   
		<text x="$w" y="$down" text-anchor="right" style="font-size:15px">unit:$cluster_info[1]</text>
                </a>
		<a xlink:href="cell_timeline.cgi?unit=$cluster_info[0]">
                <text x="$w2" y="$down" text-anchor="right" style="font-size:15px">cluster:$cluster_info[0]</text>
                </a>
EOF
		;
	
	#Foreach point in time draw the tickmark/label on the scale and the circle on the timeline
	my $dx = 0;
	
	foreach my $time (sort {$a <=> $b} keys %{$times{$exp}}) {
		$dx = $dx + $inc;
		my $dy = $scale_y + $tick_height;
		if($done == 0){
		#Draw scalebar tick marks
		$diagram .= <<EOF
	<line x1="$dx" y1="$scale_y" x2="$dx" y2="$dy" style="stroke: #333; stroke-width: 1;" />
	<line x1="$dx" y1="$scale_y" x2="$dx" y2="$inc" style="stroke: #333; stroke-width: 1; opacity: 0.01" />
EOF
		;
		
		my $label =  $times{$exp}{$time}{'label'};
		#Draw the labels
		my $font = 10;
		my $rotate = $dy - ($font/2);
		$diagram .= <<EOF
		<a xlink:href="cell_timeline.cgi?order=$label">
		<text x="$dx" y="$dy" text-anchor="right" style="font-size:15px" transform="rotate(90 $dx,$rotate)">$label</text>
		</a>
EOF
		;
		
		}

			
		
		my $color;
		my $size;
		my $barw =20;
		my $bar_y = $timeline_y;
		if($times->{$exp}{$time}{'size'} > 0){
			if(($norms->{'max'} == 0)||($times{$exp}{$time}{'size'} == 0)){
				$size = 0;
			}else{
			$size = (abs(($times{$exp}{$time}{'size'}/$norms->{'max'})*($inc/2)));
			}
			$color = 'cyan';
			$bar_y = $bar_y - $size;
		}else{
			$color = 'red';
			if(($norms->{'min'} == 0)||($times{$exp}{$time}{'size'} == 0)){
				$size = 0;
			}else{
			$size = abs($times{$exp}{$time}{'size'}/$norms->{'min'})*($inc/2);
			}
		}
		#Draw the circles
		my $l = $times{$exp}{$time}{'label'};
		my $t = $times{$exp}{$time}{'taxon_id'};
		
		my $barx = $dx-($barw/2);
		$diagram .= <<EOF
		<a xlink:href="experiment_epoch.cgi?epoch=$t&amp;experiment=$exp">
		<rect x="$barx" y="$bar_y" height="$size" width="20" fill="$color" opacity="0.6"/>
		</a>
EOF
	}
	$done = 1;
	$timeline_y = $timeline_y - (2*$inc)
}
	
	$diagram .= "\n</svg>";

	return $diagram;
}

my $times = get_times(\@exps);
my $norm_times = get_norm_times();

my $points = 12;
my $no_samples = scalar(keys %{$times});
my $width = 1500;
my $inc = $width/($points+2);
my $height = ($no_samples*$inc*2)+(6*$inc);
print $cgi->header("image/svg+xml");
print draw_timeline($width,$height,$times,$norm_times);

=back
=cut

1;
