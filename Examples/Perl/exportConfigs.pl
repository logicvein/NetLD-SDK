use LWP::UserAgent;
use HTTP::Cookies;
use JSON;
use JSON::RPC::Client2;
use URI::Escape;
use Data::Dumper;
use POSIX qw(strftime);
use Try::Tiny;
use Config::Tiny;
use DateTime;
use File::Basename 'basename', 'dirname';
use File::Path 'mkpath';

### Initial authentication
my $cookie_jar = HTTP::Cookies->new( ignore_discard => 1 );
my $ua = LWP::UserAgent->new(
    cookie_jar => $cookie_jar,
    ssl_opts   => { SSL_use_cert => 0, verify_hostname => 0 },
#    debug => 1 
);

my $HOST = 'host';
my $USERNAME = 'username';
my $PASSWORD = 'password';
my $LAST_TIMESTAMP = 'lastConfigTimestamp';

sub usage_and_exit
{
    die "Usage:\n  exportConfigs.pl <output directory> <settings file>\n";
}

sub main
{
    my @argv = @_;
    
    if ($#argv == -1)
    {
        usage_and_exit();
    }

	my $output = $argv[0];
	my $config_file = $argv[1];
	
    if ($output eq '')
    {
        usage_and_exit();
    }

    if($config_file eq '')
    {
        usage_and_exit();
    }

	my ($host, $user, $password, $last_session_end);

	my $config = Config::Tiny->read($config_file);

	foreach my $section (keys %{$config}) 
	{
		$host = $config->{$section}->{$HOST};
	    $user = $config->{$section}->{$USERNAME};
	    $password = $config->{$section}->{$PASSWORD};
	
	    if($config->{$section}->{$LAST_TIMESTAMP})
	    {
	    	$last_timestamp = $config->{$section}->{$LAST_TIMESTAMP};
	    }
	    else
	    {
	    	$last_timestamp = 0;
	    }
	    
	    try
	    {
	    	$last_timestamp = export_configs($output, $host, $user, $password, $last_timestamp);
	    	$config->{$section}->{$LAST_TIMESTAMP} = $last_timestamp if ($last_timestamp);
	    }
	    catch
	    {
	    	warn "caught error: $_";
	    }
	}
	
	$config->write($config_file);
}

sub millis_to_date
{
	my $millis = shift;
    my $tmp = strftime('%Y-%m-%d %H:%M:%S', gmtime($millis/1000));

    return $tmp;
}

sub create_filename
{
    my ($output, $network, $ip_address, $path, $timestamp) = @_;
    
    $local_path = $path;
    
    if (index $local_path, "/" == 0)
	{
		$local_path = substr($local_path, 1);
	}
    
    return $output . '/' . $network . '/' . $ip_address . '/' . strftime('%Y-%m-%d_%H-%M_', gmtime($timestamp/1000)) . $local_path;
}

sub export_configs
{
    my ($output, $host, $user, $password, $last_timestamp) = @_;
    my ($network, $ip_address, $path, $timestamp);
    
	my $netld = JSON::RPC::Client2->new("https://".$host."/rest?j_username=".uri_escape_utf8($user)."&j_password=".uri_escape_utf8($password), $ua);

    $configs = $netld->call('Configuration.retrieveConfigsSince', {'timestamp' =>$last_timestamp});

    foreach my $config (@$configs)
    {
        $last_timestamp = $config->{'lastChanged'};
        $timestamp = millis_to_date($last_timestamp);

        $network = $config->{'managedNetwork'};
        $ip_address = $config->{'ipAddress'};
        $path = $config->{'path'};
        
        $filename = create_filename($output, $network, $ip_address, $path, $last_timestamp);

        $directory = dirname $filename;
        unless (-d $directory)
        {
            mkpath($directory)
        }

        $params = "op=config"
                ."&ipAddress=".$ip_address
                ."&managedNetwork=".$network
                ."&configPath=".$path
                ."&timestamp=".strftime('%Y-%m-%dT%H:%M:%S', gmtime($config->{'lastChanged'}/1000))
                ."&j_username=".$user
                ."&j_password=".$password;

        my $url = 'https://'.$host.'/servlet/inventoryServlet?'.$params;
        my $request = HTTP::Request->new(GET => $url);
		my $response = $ua->request($request);
		
		if($response->is_success)
		{
			open my $fh, '>>', $filename or die "$!";
			binmode $fh;
			print $fh $response->decoded_content;
			close $fh;
		}
		else
		{
			die $response->status_line, "\n";
		}
        
        print "Wrote ".$filename."\n";
    }

	$netld->call("Security.logoutCurrentUser");

    return $last_timestamp;
}

main(@ARGV);
