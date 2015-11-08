#!/usr/bin/perl
#

use Getopt::Std;
use POSIX qw(strftime);
use Scalar::Util qw(looks_like_number);

sub my_system;

my $timestamp = strftime "%F-%H-%M", localtime;

getopts('rtnh');
my $rerun = $opt_r;
my $test = $opt_t;
my $norun = $opt_n;
my $help = $opt_h;

if ($help) {
  print <<END_HELP;
launches caffe jobs on condor
options:

  -t
      test: prints commands instead of executing them

  -n
      norun: does everything but launch the job

  -r
      rerun: rerun any failed runs
END_HELP
exit;
}

my $launchDir = "/localhome/juddpatr/cnvlutin/MIsim";
my $resultDir = "/aenao-99/juddpatr/MIsim";
my $traceDir  = "/aenao-99/juddpatr/net_traces";

my $run = "$launchDir/run.sh";

#-------------------------------------------------------------------------------------------

@skelFiles = glob("*.py");

$batchTitle = "test";

$param = "ZF";
@values = (0,1);

#---------------------------------------------------------------------------------------------

$batchName = "$batchTitle";
$batchDir = "$resultDir/$batchName";

# create common batch-job.submit for all jobs in this batch
open($fh, ">batch-job.submit") or die "could not open batch-job.submit for writing\n";
print $fh <<'END_MSG';
Universe = vanilla
Getenv = True
Requirements = (Activity == "Idle") && ( Arch == "X86_64" ) && regexp( ".*fc16.*", TARGET.CheckpointPlatform )
Executable = run.sh
Output = stdout
Error = stderr
Log = condor.log
Rank = (TARGET.Memory*1000 + Target.Mips) + ((TARGET.Activity =?= "Idle") * 100000000) - ((TARGET.Activity =?= "Retiring" ) * 100000000 )
Notification = error
Copy_To_Spool = False
Should_Transfer_Files = no
#When_To_Transfer_Output = ON_EXIT
END_MSG

#print $fh "+AccountingGroup = \"long_jobs.juddpatr\"\n";
print $fh "request_memory = 2048\n";


# create batch dir and skeleton dir
if ($rerun) {
  die "$batchDir does not exists\n" unless ( -d $batchDir );
} else {
  if (-d $batchDir and not $test){
    print "$batchDir exists, clobber (y/n)?";
    my $in = <>;
    exit if ( $in !~ /^\s*[yY]\s*$/ );
    my_system("rm -rf $batchDir");
  }
  my_system("mkdir $batchDir");

  # make skeleton dir
  my_system("mkdir $batchDir/.skel");
  foreach (@skelFiles){
    my_system ("cp $_ $batchDir/.skel/.");
  }

  # turn off debug messages and fast mode when running on the cluster 
  my_system ("./set_option.pl $batchDir/.skel/options.py verboseUnit       0");
  my_system ("./set_option.pl $batchDir/.skel/options.py verboseCluster    0");
  my_system ("./set_option.pl $batchDir/.skel/options.py verboseDirector   0");
  my_system ("./set_option.pl $batchDir/.skel/options.py verboseMemory     0");
  my_system ("./set_option.pl $batchDir/.skel/options.py fast 0");

}

# update this if we rerun
my_system("cp batch-job.submit $batchDir/.skel/.") ;

my $first = 1;

print "Preparing $batchDir\n" unless $rerun;

# create individual submit script
my_system("cp batch-job.submit job.submit");
open($fh, ">>job.submit") or die "could not open submit for append\n";

# for each configuration: param = value
for $value (@values) {
  print "$param=$value" if not $test and not $rerun;
  $config = sprintf("%s-%s",$param,$value);

  for $net ("alexnet","nin_imagenet","googlenet","vgg_cnn_s","vgg_cnn_m_2048","vgg_19layers") {
    print "\n\t$net";

    # get layers from trace param file 
    open (TRACE_STATS, "<$traceDir/$net/${net}_trace_params.csv") or die "$! $traceDir/$net/${net}_trace_params.csv\n";
    @layers = ();
    while (<TRACE_STATS>){
      /^([^,]+),/; # get first value 
      push @layers, $1;
    }

    # for each layer 
    foreach $layer (@layers){

      # strip '/'s from layer name when to create runDir
      $layer_dir = "";
      if (looks_like_number($layer)){
        $layer_dir .= sprintf("%02d",$layer);
      } else {
        $layer_dir .= $layer;
      }
      $layer_dir =~ s/\//_/g;

      #printf("%s-%s", $layer_dir, $param) if not $test and not $rerun;

      # define directory structure here:
      my $runDir = "$batchDir/$config/$net/$layer";


      if ($rerun and -d $runDir) {
        # did this run succeed?
        $ret = system("grep \"Total cycles:\" $runDir/stdout >/dev/null");
        if ($ret == 0){
          next; # if so, skip
        } else {
          print "Rerunning $runDir\n";
        }
      } else { 
        # setup runDir
        build_dir($runDir);

        # copy files to runDir
        my_system("cp $run $runDir/run.sh");

        # link script files into dir:
        foreach my $file (glob "$batchDir/.skel/*.py"){
          my_system("ln -s $file $runDir/.");
        }

        my_system("rm $runDir/options.py");
        my_system("cp $batchDir/.skel/options.py $runDir/.");
        # set parameters in model 
        if ("$param" ne "") {
          my_system("./set_option.pl $runDir/options.py $param $value");
        }
      }
 
      # arguments for run.sh 
      $args = "$net $layer";
      my_system("echo \"$args\" > $runDir/args"); # so we can run locally: ./run.sh `cat args`

      # append job details to submit script
      print $fh "InitialDir =  $runDir\n";
      print $fh "Args = $args\n";
      print $fh "Queue\n\n";
      last if ($batchTitle =~ m/baseline/);

    print "." if not $test and not $rerun;
    } # foreach layer
  }# foreach net
  print "\n" if not $test and not $rerun;
} # foreach value

  close $fh;
  my_system("condor_submit job.submit") unless $norun;


#--subroutines--------------------------------------------------------------------------------

# build the given dir structure
# executes mkdir for each dir that doesn't exist
# arguments:
#   path  e.g. "/these/dirs/exist/these/dirs/dont/exist"
sub build_dir {
  $runDir = shift;
  @dirs = split /\//, $runDir;
  $base = "";
  foreach (@dirs){
    $base .= "/$_";
    if (not -d $base){
      my_system("mkdir $base");
    }
  }
}

# system call wrapper for testing
sub my_system {
  my $cmd = shift(@_);
  if ($test) {
    print "$cmd\n";
  } else {
    system ("$cmd") and die "failed to run $cmd";
  }
}

