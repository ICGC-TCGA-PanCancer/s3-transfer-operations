#!/usr/bin/perl -w

# By Christina Yung
# Simple count of files in directories

use strict;

my @dir = qw(backlog-jobs queued-jobs verifying-jobs downloading-jobs uploading-jobs completed-jobs failed-jobs);
system('git pull');
print "\n##################\n";
print "s3-transfer-jobs\n";
print "##################\n";
foreach my $dir (@dir) {
  my @json = glob("../s3-transfer-jobs/$dir/*.json");
  print join("\t", scalar @json, $dir), "\n";
} 

print "\n##################\n";
print "s3-transfer-jobs-2\n";
print "##################\n";
foreach my $dir (@dir) {
  my @json = glob("../s3-transfer-jobs-2/$dir/*.json");
  print join("\t", scalar @json, $dir), "\n";
} 

