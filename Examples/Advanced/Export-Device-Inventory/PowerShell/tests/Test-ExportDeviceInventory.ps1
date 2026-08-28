$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSScriptRoot '..' 'ExportDeviceInventory.psm1') -Force

function Assert-Equal($Expected, $Actual, [string]$Message) {
    if ($Expected -ne $Actual) { throw "$Message Expected '$Expected', got '$Actual'." }
}

$offsets = [Collections.Generic.List[int]]::new()
$fetchPage = {
    param($offset, $pageSize)
    $offsets.Add([int]$offset)
    if ($offset -eq 0) {
        return [pscustomobject]@{
            offset = 0; pageSize = 2; total = 5
            devices = @(
                [pscustomobject]@{ network = 'Default'; ipAddress = '192.0.2.1'; hostname = 'core,one'; complianceState = 2 },
                [pscustomobject]@{ network = 'Lab'; ipAddress = '192.0.2.2'; memoSummary = "first`nsecond" }
            )
        }
    }
    if ($offset -eq 2) {
        return [pscustomobject]@{
            offset = 2; pageSize = 2; total = 0
            devices = @(
                [pscustomobject]@{ network = 'Lab'; ipAddress = '192.0.2.3' },
                [pscustomobject]@{ network = 'Lab'; ipAddress = '192.0.2.4' }
            )
        }
    }
    return [pscustomobject]@{
        offset = 4; pageSize = 2; total = 0
        devices = @([pscustomobject]@{ network = 'Lab'; ipAddress = '192.0.2.5' })
    }
}

$devices = @(Get-NetLDInventoryDevices -FetchPage $fetchPage -PageSize 2)
Assert-Equal 5 $devices.Count 'Device count failed.'
Assert-Equal '0,2,4' ($offsets -join ',') 'Pagination offsets failed.'
Assert-Equal 'Default,Lab' ((ConvertTo-ManagedNetworkList 'Default, Lab') -join ',') 'Network parsing failed.'

$directory = Join-Path ([IO.Path]::GetTempPath()) "netld-inventory-$([guid]::NewGuid())"
$output = Join-Path $directory 'inventory.csv'
try {
    Export-NetLDInventoryCsv -Devices $devices -OutputPath $output
    $rows = @(Import-Csv -LiteralPath $output)
    Assert-Equal 5 $rows.Count 'CSV row count failed.'
    Assert-Equal 'core,one' $rows[0].hostname 'CSV comma quoting failed.'
    Assert-Equal "first`nsecond" $rows[1].memoSummary 'CSV newline quoting failed.'
    $jsonOutput = Join-Path $directory 'inventory.json'
    Export-NetLDInventoryJson -Devices $devices -OutputPath $jsonOutput
    $jsonRows = @(Get-Content -LiteralPath $jsonOutput -Raw | ConvertFrom-Json)
    Assert-Equal 5 $jsonRows.Count 'JSON row count failed.'
    Assert-Equal 2 $jsonRows[0].complianceState 'JSON numeric type failed.'
    if ($null -ne $jsonRows[2].hostname) { throw 'JSON missing value was not null.' }
}
finally {
    Remove-Item -LiteralPath $directory -Recurse -Force -ErrorAction SilentlyContinue
}

$threw = $false
try { [void](ConvertTo-ManagedNetworkList ' , ') } catch { $threw = $true }
if (-not $threw) { throw 'Empty network list was not rejected.' }

Write-Host 'PowerShell tests passed.'
