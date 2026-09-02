$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSScriptRoot '..' 'ExportThirdEyeViolations.psm1') -Force

function Assert-Equal($Expected, $Actual, [string]$Message) {
    if ($Expected -ne $Actual) { throw "$Message Expected '$Expected', got '$Actual'." }
}

function New-Event([long]$Id, [long]$Updated) {
    [pscustomobject]@{
        eventId = $Id; incidentId = 1; severity = 'ERROR'; clearState = 'ACTIVE'
        eventType = 'THRESHOLD'; network = 'Default'; ipAddress = '192.0.2.1'
        hostname = 'router'; deviceId = 7; hostUuid = 'host-7'; measurement = 'CPU'
        measurementIndex = $null; message = 'Test, with comma'; occurrences = 1
        triggerId = 'trigger-1'; created = $Updated - 1000; updated = $Updated
    }
}

$temporary = Join-Path ([IO.Path]::GetTempPath()) "violations-powershell-$([guid]::NewGuid())"
try {
    $config = [pscustomobject]@{
        BaseUrl = 'https://example'; ApiKey = 'key'; OutputDir = Join-Path $temporary 'output'
        OutputFormat = 'csv'; StatePath = Join-Path $temporary 'state.json'
        ReportPath = Join-Path $temporary 'run.json'; PageSize = 2
        InitialLookbackHours = 24; SearchQueries = @('incidentId=1')
    }
    $pages = @{
        0 = [pscustomobject]@{ offset = 0; pageSize = 2; total = 3; violations = @((New-Event 3 3000), (New-Event 2 2000)) }
        2 = [pscustomobject]@{ offset = 2; pageSize = 2; total = 0; violations = @((New-Event 1 2000)) }
    }
    $search = { param($queries, $offset, $pageSize) $pages[$offset] }
    $first = Export-ThirdEyeViolationData $config $search 4000 '1970-01-01T00:00:04Z'
    $csv = Import-Csv $first.outputFile
    $state = Get-Content $config.StatePath -Raw | ConvertFrom-Json
    Assert-Equal 2 $first.pageCount 'Page count failed.'
    Assert-Equal 3 $first.exportedCount 'Export count failed.'
    Assert-Equal 'Test, with comma' $csv[0].message 'CSV escaping failed.'
    Assert-Equal 3000 $state.lastUpdated 'State watermark failed.'

    $secondPages = @{
        0 = [pscustomobject]@{ offset = 0; pageSize = 2; total = 2; violations = @((New-Event 4 3000), (New-Event 3 3000)) }
    }
    $secondSearch = { param($queries, $offset, $pageSize) $secondPages[$offset] }
    $second = Export-ThirdEyeViolationData $config $secondSearch 5000 '1970-01-01T00:00:05Z'
    Assert-Equal 1 $second.exportedCount 'Watermark tie-breaker failed.'

    $config.OutputFormat = 'json'
    $config.StatePath = Join-Path $temporary 'json-state.json'
    $config.ReportPath = Join-Path $temporary 'json-run.json'
    $jsonPages = @{ 0 = [pscustomobject]@{ offset = 0; pageSize = 2; total = 1; violations = @((New-Event 1 2000)) } }
    $jsonSearch = { param($queries, $offset, $pageSize) $jsonPages[$offset] }
    $jsonReport = Export-ThirdEyeViolationData $config $jsonSearch 3000 '1970-01-01T00:00:03Z'
    $json = @(Get-Content $jsonReport.outputFile -Raw | ConvertFrom-Json)
    Assert-Equal 2000 $json[0].updated 'JSON timestamp preservation failed.'

    $queries = @(ConvertFrom-SearchQueries '["incidentId=1"]')
    Assert-Equal 'incidentId=1' $queries[0] 'Query parsing failed.'
    $rejected = $false
    try { ConvertFrom-SearchQueries '["start=2026-01-01T00:00:00Z"]' | Out-Null }
    catch { $rejected = $true }
    Assert-Equal $true $rejected 'Reserved query validation failed.'

    Write-Host 'PowerShell ThirdEye violation export tests passed.'
}
finally {
    if (Test-Path $temporary) { Remove-Item $temporary -Recurse -Force }
}
