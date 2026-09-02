use LWP::UserAgent;
use HTTP::Cookies;
use JSON;
use JSON::RPC::Client2;
use URI::Escape;

my $cookie_jar = HTTP::Cookies->new( ignore_discard => 1 );
my $ua = LWP::UserAgent->new(
    cookie_jar => $cookie_jar,
    ssl_opts   => { SSL_use_cert => 0, verify_hostname => 0 },
);

my $output_file = shift(@ARGV);
my $host = shift(@ARGV);
my $user = shift(@ARGV);
my $password = shift(@ARGV);

my $netld = JSON::RPC::Client2->new("https://".$host."/rest?j_username=".uri_escape_utf8($user)."&j_password=".uri_escape_utf8($password), $ua);

print "** executing job **\n";

open(FH, ">$output_file") or die "$!";

my $network = 'Default';

my $job_metadata = $netld->call('Scheduler.getJobMetadataByGroup', {
		managedNetwork => $network
	}
);

my @jobs = ();
my $json = JSON->new->allow_nonref;
 
foreach my $job_metadatum (@$job_metadata)
{
	my $job = $netld->call("Scheduler.getJob",  { 
			managedNetwork => $job_metadatum->{managedNetwork},
		    jobName => $job_metadatum->{jobName},
		}
	);
	push (@jobs , $job);
}

print FH $json->encode(\@jobs);
close(FH);

print "** Job Export execution complete **\n";

$netld->call("Security.logoutCurrentUser");