use LWP::UserAgent;
use HTTP::Cookies;
use JSON::RPC::Client2;
use Data::Dumper;
use POSIX qw(strftime);
use Text::CSV;

### Initial authentication
my $cookie_jar = HTTP::Cookies->new( ignore_discard => 1 );
my $ua = LWP::UserAgent->new(
    cookie_jar => $cookie_jar,
    ssl_opts   => { SSL_use_cert => 0, verify_hostname => 0 }
);

my $output_file = ($#ARGV == -1) ? "InventoryReport" . (strftime "%y%m%d-%H%M%S", localtime) . ".csv" : $ARGV[0];

my $netld = JSON::RPC::Client2->new("https://localhost/rest?j_username=admin&j_password=password", $ua);

my $pageData = $netld->call("Inventory.search", {
        network  => 'Default',
        scheme   => 'ipAddress',
        query    => '',
        pageData => {
            offset   => 0,
            pageSize => 500,
        },
        sortColumn => 'ipAddress',
        descending => 0
    }
);

do {
	my $csv = Text::CSV->new ({binary => 1, eol => "\n"}) or die "Cannoot use CSV: " .Text::CSV->error_diag(); 
	open $fh, ">>", $output_file or die "$output_file: $!"; 
	foreach $device (@{$pageData->{devices}})
	{
		$csv->print ($fh, [$device->{backupStatus}, $device->{ipAddress}, 
						$device->{hostname}, $device->{hardwareVendor},              
						$device->{model}, $device->{deviceType}, 
						$device->{serialNumber}, $device->{adapterId}, 
						$device->{osVersion}, $device->{softwareVendor}, 
						$device->{backupElapsed}, $device->{memoSummary},     
						$device->{custom1}, $device->{custom2}, $device->{custom3}, 
						$device->{custom4}, $device->{custom5}]);
	}
	close $fh;
	
	$pageData->{offset} += $pageData->{pageSize}
}
until ($pageData->{total} <= $pageData->{offset} + $pageData->{pageSize});

$netld->call("Security.logoutCurrentUser");

1;