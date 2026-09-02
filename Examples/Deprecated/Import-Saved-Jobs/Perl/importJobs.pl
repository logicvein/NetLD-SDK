use LWP::UserAgent;
use HTTP::Cookies;
use JSON;
use JSON::RPC::Client2;

my $cookie_jar = HTTP::Cookies->new( ignore_discard => 1 );
my $ua = LWP::UserAgent->new(
    cookie_jar => $cookie_jar,
    ssl_opts   => { SSL_use_cert => 0, verify_hostname => 0 },
);

my $input_file = shift(@ARGV);
my $network = shift(@ARGV) or die "no network specified";

my $netld = JSON::RPC::Client2->new("https://localhost/rest?j_username=admin&j_password=password", $ua);

print "** executing job **\n";

open(DF, "< $input_file") or die "$!";

my $job_metadata = '';
while (my $line = <DF>)
{
	$job_metadata .= $line;
}

my $json = JSON->new->allow_nonref;
my $jobs = $json->decode($job_metadata);

foreach my $job (@$jobs)
{
	$job->{managedNetwork} = $network;
	$netld->call('Scheduler.addJob', { 'jobData' => $job, 'replace' => 1 });
}

print "** Job Import execution complete **\n";

$netld->call("Security.logoutCurrentUser");
