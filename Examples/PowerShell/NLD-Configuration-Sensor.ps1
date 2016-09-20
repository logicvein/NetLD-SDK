Param (
    [string] $server = (&{Get-ChildItem Env:prtg_host}).Value,
    [int] $port = 443,
    [string] $username = 'admin',
    [string] $password = 'password',
    [string] $networks = '',
    [string] $report   = 'PRTG Realtime Changes'
 )

. "$PSScriptRoot\NLDService.ps1"

$gmt   = [TimeZoneInfo]::FindSystemTimeZoneById('Greenwich Standard Time')

# Read previous execution time
$confPath = ('NLD-Config-Sensor.json')
$confFile = Get-Content -ErrorAction Ignore $confPath | ConvertFrom-Json

if ($confFile -eq $null) {
   $now = (Get-Date).ToUniversalTime().ToString('s')
   $confFile = (New-Object PSObject | Add-Member -PassThru NoteProperty lastRun ($now))
   $confFile | ConvertTo-Json | Set-Content $confPath
}

$start = ([DateTime]::ParseExact($confFile.lastRun, 'yyyy-MM-ddTHH:mm:ss', $null)).ToString('s') + '-00:00'
$netld = [NLDService]::new($username, $password, $server, $port)
$changes = $netld.call('Configuration.retrieveConfigsSince', @($start))

$netFilter = @{}
if ($networks.Length -gt 0) {
   $networks -split ',' | % {$netFilter.Add($_, $true)}
}

$addresses = @{}
$earliest = [int64]::MaxValue
$latest   = [int64]::MinValue
foreach ($change in $changes) {
   $earliest = [math]::Min($earliest, $change.lastChanged)
   $latest   = [math]::Max($latest, $change.lastChanged)

   $network = $change.managedNetwork
   if ($netFilter.Count -gt -0 -and -not $netFilter.ContainsKey($network)) {
      continue;
   }

   if ($addresses.ContainsKey($network)) {
      $tmp = $addresses.Item($network)
      if (-not $tmp.ContainsKey($change.ipAddress)) {
         $tmp.Add($change.ipAddress, $change.ipAddress);
      }
   }
   else {
      $tmp = @{$change.ipAddress = $change.ipAddress}
      $addresses.Add($network, $tmp)
   }
}

$changedDevices  = 0
$changedNetworks = $addresses.Keys.Count
if ($changedNetworks -gt 0) {
   # Calculate report interval
   #
   $start = [TimeZoneInfo]::ConvertTimeToUtc('1970-01-01 00:00:00', $gmt)
   $end   = [TimeZoneInfo]::ConvertTimeToUtc('1970-01-01 00:00:00', $gmt)

   $start = $start.AddSeconds($earliest / 1000).AddSeconds(-1).ToString('s') + '-00:00'
   $end   = $end.AddSeconds($latest / 1000).AddSeconds(1).ToString('s') + '-00:00'

   $job = $netld.call('Scheduler.getJob', @('Default', $report))

   foreach ($network in $addresses.Keys) {
      $changedDevices += $addresses.Item($network).Count

      $job.managedNetwork = $network
      $job.jobParameters.managedNetwork = $network
      $job.jobParameters.'input.start_date' = $start
      $job.jobParameters.'input.end_date' = $end
      $job.jobParameters.ipResolutionData = (($addresses.Item($network).Values | % {"$_@$network"}) -join ',')

      $netld.call('Scheduler.runNow', @($job))
   }

   # Save the last change timestamp
   $lastRun = [TimeZoneInfo]::ConvertTimeToUtc('1970-01-01 00:00:00', $gmt)
   $lastRun = $lastRun.AddSeconds($latest / 1000).ToString('s')

   $confFile.lastRun = $lastRun
   $confFile | ConvertTo-Json | Set-Content $confPath
}

$netld.close()

# Report sensor result to PRTG as XML
#
$deviceWord = (&{ if ($changedDevices -eq 1) {"device"} else {"devices"} })

$data = "<prtg>
    <text>$(&{ if ($changedDevices -gt 0) {"Configuration changes on $changedDevices $deviceWord."} else {"Ok"} })</text>
    <result>
        <channel>Changes</channel>
        <value>$changedDevices</value>
        $(&{if ($changedDevices -gt 0) {'<NotifyChanged/>'} else {''}})
    </result>
</prtg>"

$data.ToString()

exit 0
