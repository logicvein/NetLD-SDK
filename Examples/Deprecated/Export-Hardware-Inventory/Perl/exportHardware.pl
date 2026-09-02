use LWP::UserAgent;
use HTTP::Cookies;
use JSON::RPC::Client2;
use Data::Dumper;
use POSIX qw(strftime);
use Text::CSV;
use Getopt::Long;
#use Compress::Zlib;

### Initial authentication
my $cookie_jar = HTTP::Cookies->new( ignore_discard => 1 );
my $ua = LWP::UserAgent->new(
    cookie_jar => $cookie_jar,
    ssl_opts   => { SSL_use_cert => 0, verify_hostname => 0 },
#    debug => 1 
);

my $output_file = ($#ARGV == -1) ? "HardwareReport" . (strftime "%y%m%d-%H%M%S", localtime) . ".csv" : $ARGV[0];

my $netld = JSON::RPC::Client2->new("https://localhost/rest?j_username=admin&j_password=password", $ua);

my $network = 'Default';
my $job_name = 'Hardware Report';

my $execution = $netld->call("Scheduler.runNow",  {'jobData' => {
		managedNetwork => $network,
	    jobName => $job_name,
	    jobType => 'Report',
	    description => '',
	    jobParameters => {
	        tool => 'ziptie.reports.hardware',
	        ipResolutionScheme => 'ipAddress',
	        ipResolutionData => '',
	        managedNetwork => $network,
	        format => 'csv',
	    },
	}
}
);

print "** executing job **\n";
my $execution_id = $execution->{id};

until ($execution->{endTime})
{
	if($execution->{completionState} == 1 || $execution->{completionState} == 2)
	{
    	print "** execution canceled **\n";
        last;
	}
    sleep(1); 
    $execution = $netld->call('Scheduler.getExecutionDataById', {'executionId' => $execution_id});
}

my $url = "https://localhost/servlet/pluginDetail?executionId=" . $execution_id;  

my $request = HTTP::Request->new(GET => $url);
my $response = $ua->request($request);

if($response->is_success)
{
	open my $fh, '>>', $output_file or die "$!";
	binmode $fh;
	print $fh $response->decoded_content;
	close $fh;
}
else
{
	die $response->status_line, "\n";
}

print "** Hardware Report Export execution complete **\n";

$netld->call("Security.logoutCurrentUser");