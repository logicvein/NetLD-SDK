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

### use the inventory service to create a device
my $error = $netld->call("Inventory.createDevice", {
        network   => 'Default',
        ipAddress => '10.10.10.10',
        adapterId => 'Cisco::IOS'
    }
);

print "Create device result: " . (defined($error) ? $error : "Created" ) . "\n";

### get the device we just created and print it's address from the returned object
my $device = $netld->call("Inventory.getDevice", {network => 'Default', ipAddress => '10.10.10.10'});

if (defined($device))
{
    print "Retrieved device: " . $device->{ipAddress} . "\n";
}
else
{
    print "Device does not exist!\n";
    exit(0);
}

### now delete the device
$netld->call("Inventory.deleteDevice", {network => 'Default', ipAddress => '10.10.10.10'});
print "Device deleted.\n";

### Logout using the security service to be nice to the server
###

$netld->call("Security.logoutCurrentUser");
