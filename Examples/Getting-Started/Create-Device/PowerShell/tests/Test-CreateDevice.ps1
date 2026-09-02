$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '..' 'NetLDExampleClient.ps1')

function Assert-Equal($Expected, $Actual, [string]$Message) {
    if ($Expected -ne $Actual) { throw "$Message Expected '$Expected', got '$Actual'." }
}

$parameters = New-CreateDeviceParameters -Network 'Default' -IpAddress '2001:0db8::10' -AdapterId 'Cisco::IOS'
Assert-Equal 'Default' $parameters.network 'Managed network failed.'
Assert-Equal '2001:db8::10' $parameters.ipAddress 'IP normalization failed.'
Assert-Equal 'Cisco::IOS' $parameters.adapterId 'Adapter ID failed.'

$threw = $false
try { [void](New-CreateDeviceParameters -Network 'Default' -IpAddress 'not-an-address' -AdapterId 'Cisco::IOS') } catch { $threw = $true }
if (-not $threw) { throw 'Invalid IP address was not rejected.' }

Write-Host 'PowerShell tests passed.'

