#!/usr/bin/perl
#
# This script updates a file with parameters specified as 
# param = value
# indentation is preserved
# the parameter will be updated in place or added to the end if not found
#

use Getopt::Std;

getopts('');

if (@ARGV < 3) {
  print "usage: set_option.pl <file> <parameter> <value>\n";
  print "options:\n";
  exit;
}

my $filename = $ARGV[0];
my $param = $ARGV[1];
my $value = $ARGV[2];

my @layers = split /,/, $layer;

if ($partial){
  #print "searching for layers named \".*$layer.*\"\n";
}

# read file to array
open(my $fh, "<$filename") or die $!;
my @lines = <$fh>;
close $fh;

# open for writing
open(my $fh, ">$filename") or die $!;

my $found = 0;
foreach my $line (@lines){
  
  # find the right layer by name
  #
  if ($line =~ m/^(\s*$param\s*=)/) {
    $line = "$1 $value\n";
    $found = 1;
  }

  print $fh "$line";
}

if ( not $found ){
  print $fh "$param = $value\n";
}

close $fh;


