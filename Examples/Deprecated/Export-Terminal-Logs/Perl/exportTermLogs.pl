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
my $LAST_SESSION_END = 'lastSessionEnd';
	
sub usage_and_exit
{
	die "Usage:\n  exportTermLogs.pl <output directory> <config file>\n";
}

sub main
{
    my @argv = shift;
    
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
	
	    if($config->{$section}->{$LAST_SESSION_END})
	    {
	    	$last_session_end = $config->{$section}->{$LAST_SESSION_END};
	    }
	    else
	    {
	    	$last_session_end = 0;
	    }
	    
	    try
	    {
	    	$last_session_end = export_termLogs($output, $host, $user, $password, $last_session_end);
	    	$config->{$section}->{$LAST_SESSION_END} = $last_session_end if ($last_session_end);
	    }
	    catch
	    {
	    	warn "caught error: $_";
	    }
	}
	
	$config->write($config_file);
}

sub create_filename
{
	my ($output, $session_start, $termlog) = @_;

	my $count = 0;

	my $filename = $output.filename_prefix($session_start, $termlog).strftime('%H-%M', gmtime($session_start/1000)).'.log';
    print $filename."\n";
    while (-e $filename)
    {
        $count = $count + 1;
        $filename = $output.filename_prefix($session_start, $termlog).strftime('%H-%M-%S', gmtime($session_start/1000)).'-'.$count.'.log';
    }

    return $filename;
}

sub filename_prefix
{
	my ($session_start, $termlog) = @_;
	
	return '/'.strftime('%Y-%m-%d', gmtime($session_start/1000)).'/'.$termlog->{'ipAddress'}.'_'.$termlog->{'hostname'}.'_';
}

sub millis_to_date
{
	my $millis = shift;
    my $tmp = strftime('%Y-%m-%d %H:%M:%S', gmtime($millis/1000));

    return $tmp;
}

sub export_termLogs
{
	my ($output, $host, $user, $password, $last_session_end) = @_;
    my ($session_start, $session_end, $filename, $directory,$params);
	
    my $netld = JSON::RPC::Client2->new("https://".$host."/rest?j_username=".uri_escape_utf8($user)."&j_password=".uri_escape_utf8($password), $ua);

    my $first_session_end = millis_to_date($last_session_end);
    my $scheme = 'since';
    my $data = strftime('%Y-%m-%d', gmtime($first_session_end));
	
    my $termlogs = $netld->call('TermLogs.search', {
		    scheme => $scheme, 
		    data => $data, 
		    sortColumn => "sessionEnd", 
		    descending => 1,
	    }
    );
    
    foreach my $termlog (@$termlogs)
    {
        $session_start = millis_to_date($termlog->{'sessionStart'});
        $last_session_end = $termlog->{'sessionEnd'};
        $session_end = millis_to_date($last_session_end);

        print $termlog->{'ipAddress'} . ': ' . strftime('%Y-%m-%dT%H:%M:%S', gmtime($last_session_end/1000))."\n";
        print " Last: ".$last_session_end."\n";

        $filename = create_filename($output, $termlog->{'sessionStart'}, $termlog);

        $directory = dirname $filename;
        unless (-d $directory)
        {
            mkpath($directory);
        }

        $params = "op=content"
                ."&sessionStart=".strftime('%Y-%m-%dT%H:%M:%S', gmtime($termlog->{'sessionStart'}/1000))
                ."&ipAddress=".$termlog->{'ipAddress'}
                ."&managedNetwork=".$termlog->{'managedNetwork'} #.encode('utf-8'),
                ."&stripXml=true"
                ."&j_username=".$user
                ."&j_password=".$password;

        my $url = 'https://'.$host.'/servlet/termlog?'.$params;
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

    return $last_session_end
}

main();