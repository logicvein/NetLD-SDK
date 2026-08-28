$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSScriptRoot '..' 'ExportDeviceInterfaces.psm1') -Force

function Assert-Equal($Expected, $Actual, [string]$Message) {
    if ($Expected -ne $Actual) { throw "$Message Expected '$Expected', got '$Actual'." }
}

$offsets = [Collections.Generic.List[int]]::new()
$fetchPage = {
    param($offset, $pageSize)
    $offsets.Add([int]$offset)
    if ($offset -eq 0) {
        return [pscustomobject]@{ pageSize = 2; total = 3; devices = @(
            [pscustomobject]@{ network = 'Default'; ipAddress = '192.0.2.1'; hostname = 'one' },
            [pscustomobject]@{ network = 'Lab'; ipAddress = '192.0.2.2'; hostname = 'two' }
        ) }
    }
    return [pscustomobject]@{ pageSize = 2; total = 0; devices = @(
        [pscustomobject]@{ network = 'Lab'; ipAddress = '192.0.2.3'; hostname = 'three' }
    ) }
}
$fetchInterfaces = {
    param($device)
    if ($device.ipAddress -eq '192.0.2.2') { throw 'simulated lookup failure' }
    if ($device.ipAddress -eq '192.0.2.3') { return @() }
    return @([pscustomobject]@{
        id = 7; index = 1; name = 'Ethernet1'; adminUp = $true
        ipAddresses = @(
            [pscustomobject]@{ ipAddress = '192.0.2.10'; cidrPrefix = 24 },
            [pscustomobject]@{ ipAddress = '2001:db8::10'; cidrPrefix = 64 }
        )
    })
}

$devices = @(Get-NetLDInventoryDevices $fetchPage 2)
Assert-Equal 3 $devices.Count 'Device count failed.'
Assert-Equal '0,2' ($offsets -join ',') 'Pagination offsets failed.'
$directory = Join-Path ([IO.Path]::GetTempPath()) "netld-interfaces-$([guid]::NewGuid())"
try {
    $output = Join-Path $directory 'interfaces.csv'
    $failure = Join-Path $directory 'failures.csv'
    $result = Export-NetLDInterfaceData $devices $fetchInterfaces $output $failure
    $rows = @(Import-Csv $output)
    $failures = @(Import-Csv $failure)
    Assert-Equal 3 $result.DeviceCount 'Processed device count failed.'
    Assert-Equal 1 $result.InterfaceCount 'Interface count failed.'
    Assert-Equal 1 $result.FailureCount 'Failure count failed.'
    Assert-Equal '192.0.2.10/24;2001:db8::10/64' $rows[0].ipAddresses 'IP flattening failed.'
    Assert-Equal 'true' $rows[0].adminUp 'Boolean formatting failed.'
    Assert-Equal '192.0.2.2' $failures[0].deviceIpAddress 'Failure identity failed.'
}
finally {
    Remove-Item -LiteralPath $directory -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Host 'PowerShell tests passed.'
