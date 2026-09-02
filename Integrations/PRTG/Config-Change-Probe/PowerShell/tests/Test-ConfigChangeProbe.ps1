$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSScriptRoot '..' 'ConfigChangeProbe.psm1') -Force

function Assert-Equal($Expected, $Actual, [string]$Message) {
    if ($Expected -ne $Actual) { throw "$Message Expected '$Expected', got '$Actual'." }
}

$changes = @(
    [pscustomobject]@{ managedNetwork = 'East'; ipAddress = '192.0.2.2'; lastChanged = 2000 },
    [pscustomobject]@{ managedNetwork = 'East'; ipAddress = '192.0.2.1'; lastChanged = 1000 },
    [pscustomobject]@{ managedNetwork = 'East'; ipAddress = '192.0.2.1'; lastChanged = 1500 },
    [pscustomobject]@{ managedNetwork = 'West'; ipAddress = '198.51.100.1'; lastChanged = 3000 }
)
$summary = Get-ChangeSummary -Changes $changes -Networks @('East')
Assert-Equal 2 $summary.DeviceCount 'Filtered unique-device count failed.'
Assert-Equal 1000 $summary.Earliest 'Earliest timestamp failed.'
Assert-Equal 2000 $summary.Latest 'Latest timestamp failed.'

$job = [pscustomobject]@{
    managedNetwork = 'Default'
    jobParameters = [pscustomobject]@{
        managedNetwork = 'Default'
        'input.start_date' = ''
        'input.end_date' = ''
        ipResolutionData = ''
    }
}
$prepared = New-PreparedReportJob -JobData $job -Network 'East' `
    -Addresses @('192.0.2.2', '192.0.2.1', '192.0.2.1') -Earliest 1000 -Latest 2000
Assert-Equal 'East' $prepared.managedNetwork 'Top-level managed network failed.'
Assert-Equal '192.0.2.1@East,192.0.2.2@East' $prepared.jobParameters.ipResolutionData 'IP resolution data failed.'

$xml = ConvertTo-PrtgXmlResult -DeviceCount 2
if ($xml -notmatch '<NotifyChanged\s*/>') { throw 'Change output lacks NotifyChanged.' }
$errorXml = ConvertTo-PrtgXmlError -Message 'A < B & C'
if ($errorXml -notmatch 'A &lt; B &amp; C') { throw 'Error XML is not escaped.' }

$statePath = Join-Path ([IO.Path]::GetTempPath()) "config-change-probe-$([guid]::NewGuid()).json"
try {
    Write-ProbeState -Path $statePath -LastRun '2026-01-01T00:00:00-00:00'
    Assert-Equal '2026-01-01T00:00:00-00:00' (Read-ProbeState -Path $statePath).lastRun 'State round trip failed.'
}
finally {
    Remove-Item -LiteralPath $statePath -Force -ErrorAction SilentlyContinue
}

Write-Host 'PowerShell tests passed.'

