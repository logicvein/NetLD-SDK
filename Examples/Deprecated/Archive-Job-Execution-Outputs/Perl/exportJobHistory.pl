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
	die "Usage:\n  exportTermLogs.pl [ <output file> ] [ <config file> ]\n";
}

sub main
{
	my ($output_file, $config_file);
	
	if ($#ARGV == -1)
	{
		$output_file = "JobHistory" . (strftime "%y%m%d-%H%M%S", localtime) . ".txt";
		$config_file = './config.ini';
	}
	elsif ($ARGV[1] eq '')
	{
		usage_and_exit();
	}
	else
	{
		$output_file = $ARGV[0];
		$config_file = $ARGV[1];
	}
	
	my ($host, $user, $password, $ini_last_end_time);

	my $config = Config::Tiny->read($config_file);

	foreach my $section (keys %{$config}) 
	{
		$host = $config->{$section}->{$HOST};
	    $user = $config->{$section}->{$USERNAME};
	    $password = $config->{$section}->{$PASSWORD};
	
	    if($config->{$section}->{$LAST_SESSION_END})
	    {
	    	$ini_last_end_time = $config->{$section}->{$LAST_SESSION_END};
	    }
	    else
	    {
	    	$ini_last_end_time = 0;
	    }
	    
	    try
	    {
	    	$ini_last_end_time = export_job_history($output_file, $host, $user, $password, $ini_last_end_time);
	    	$config->{$section}->{$LAST_SESSION_END} = $ini_last_end_time if ($ini_last_end_time);
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

sub make_job_list
{
	my $execution = shift;
    my $start_time = $execution->{'startTime'} / 1000;
    my $end_time = $execution->{'endTime'} / 1000;
    
    my $job_list = "\n[ ".$execution->{'status'}." / ".
            $execution->{'jobName'}." / ".
            $execution->{'managedNetwork'}." / ". 
            $execution->{'executor'}." / S:".
            strftime('%Y-%m-%d %H:%M:%S', gmtime($start_time))." / E:".
            strftime('%Y-%m-%d %H:%M:%S', gmtime($end_time)).
            " ]\n";
            
    return $job_list;
}

sub export_job_history
{
	my ($output_file, $host, $user, $password, $ini_last_end_time) = @_;
    my ($start_time, $end_time, $filename, $directory, $params);

    my $netld = JSON::RPC::Client2->new("https://".$host."/rest?j_username=".uri_escape_utf8($user)."&j_password=".uri_escape_utf8($password), $ua);

    my $pageData = $netld->call('Scheduler.getExecutionData', {
	       	pageData => {
	            offset   => 0,
	            pageSize => 1000
	        },
	        sortColumn => 'endTime',
	        descending => 1,
	    }
    );

    foreach my $execution (@{$pageData->{'executionData'}})
    {
        $start_time = millis_to_date($execution->{'startTime'});
        $last_end_time = $execution->{'endTime'};
        $end_time = millis_to_date($last_end_time);

        my $execution_id = $execution->{'id'};

        my $details = $netld->call('Plugins.getExecutionDetails', { 'executionId' => $execution_id });

        if ($details)
        {
			open my $fh, '>>', $output_file or die "$!";
            for my $detail (@$details)
            {
                if ($execution->{'jobType'} eq 'Script Tool Job')
                {
                    if ($last_end_time > $ini_last_end_time)
                    {
                    	my $job_list = make_job_list($execution);
                    	print $fh $job_list;
                        my $url = "https://" . $host . "/servlet/pluginDetail?executionId=" . $execution_id . "&recordId=" . $detail->{'id'};
				        my $request = HTTP::Request->new(GET => $url);
						my $response = $ua->request($request);
						
						if($response->is_success)
						{
							binmode $fh;
							print $fh $response->decoded_content;
						}
						else
						{
							die $response->status_line, "\n";
						}
				        
                    }
                }
            }
			close $fh;
        }
    }
    print "Wrote ".$output_file."\n";

	$netld->call("Security.logoutCurrentUser");

    return $last_end_time;
}

main();