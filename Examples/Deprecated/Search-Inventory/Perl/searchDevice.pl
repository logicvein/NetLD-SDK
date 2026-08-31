use LWP::UserAgent;
use HTTP::Cookies;
use JSON::RPC::Client2;
use Data::Dumper;

### Initial authentication
my $cookie_jar = HTTP::Cookies->new( ignore_discard => 1 );
my $ua = LWP::UserAgent->new(
    cookie_jar => $cookie_jar,
    ssl_opts   => { SSL_use_cert => 0, verify_hostname => 0 }
);

### Create a JSON-RPC proxy for the inventory service
###
my $netld = JSON::RPC::Client2->new("https://localhost/rest?j_username=admin&j_password=password", $ua);

### Search the inventory
print "Enter an individual IP address or IP/CIDR (eg. 10.0.0.0/24): ";
my $query = <STDIN>;
chomp($query);

my $pageData = $netld->call("Inventory.search", {
        network  => 'Default',
        scheme   => 'ipAddress',
        query    => $query,
        pageData => {
            offset   => 0,
            pageSize => 500,
        },
        sortColumn => 'ipAddress',
        descending => 0
    }
);

print "Search found " . $pageData->{total} . " devices.\n";
print "----------------------------------------------\n";
foreach $device (@{$pageData->{devices}})
{
    print $device->{ipAddress} . "\t" . $device->{hostname} . "\n";
}

### Logout using the security service to be nice to the server
###

$netld->call("Security.logoutCurrentUser");
