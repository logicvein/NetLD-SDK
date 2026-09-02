# Import the PsIni module.
# If necessary, install it first, for all users.
$ErrorActionPreference = 'Stop' # Abort, if something unexpectedly goes wrong.
try {
  Import-Module PsIni
} catch {
  Write-Host "Installing module PsIni"
  Install-Module -Scope AllUsers PsIni
  Import-Module PsIni
}

$IniContent = Get-IniContent "$PSScriptRoot\settings.ini"

$user = $IniContent['Server']['user']
$pass = $IniContent['Server']['pass']
$server = $IniContent['Server']['host']
$timeZone = $IniContent['Server']['timezone']
$outDir = $IniContent['Server']['outDir']

if ($null -eq $outDir) {
  $outDir = '.'
}

if ($null -eq $IniContent['State'] || $null -eq $IniContent['State']['lastRun']) {
  $lastRun = (Get-Date).ToUniversalTime().AddSeconds(60 * 60 * -24).ToString('s')
}
else {
  $lastRun = $IniContent['State']['lastRun']
}

$now = (Get-Date).ToUniversalTime()
$start = ([DateTime]::ParseExact($lastRun, 'yyyy-MM-ddTHH:mm:ss', $null)).ToString('s') + '-00:00'
$end   = ([DateTime]::ParseExact($now.ToString('s'), 'yyyy-MM-ddTHH:mm:ss', $null)).ToString('s') + '-00:00'

$timestamp = [TimeZoneInfo]::ConvertTimeBySystemTimeZoneId($now, $timeZone).toString('yyyyMMdd-HHmmss')

$Parameters = [System.Web.HttpUtility]::ParseQueryString([String]::Empty)
$Parameters.Add('j_username', $user)
$Parameters.Add('j_password', $pass)
$Parameters.Add('time_zone', $timeZone)
$Parameters.Add('queries', "start=$start")
$Parameters.Add('queries', "end=$end")

$Request = [System.UriBuilder]"https://${server}/servlet/triggerEvent"
$Request.Query = $Parameters.ToString()

Invoke-WebRequest -Uri $Request.Uri -Method GET -SkipCertificateCheck -OutFile "${outDir}\violations-${timestamp}.csv"

$IniContent['State'] = @{'lastRun' = $now.ToString('s')}
Out-IniFile -InputObject $IniContent -FilePath "$PSScriptRoot\settings.ini" -Force
