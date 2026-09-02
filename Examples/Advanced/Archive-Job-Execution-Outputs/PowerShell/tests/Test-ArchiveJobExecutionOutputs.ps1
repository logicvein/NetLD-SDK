$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSScriptRoot '..' 'ArchiveJobExecutionOutputs.psm1') -Force

function Assert-Equal($Expected, $Actual, [string]$Message) {
    if ($Expected -ne $Actual) { throw "$Message expected '$Expected', got '$Actual'" }
}

function New-Execution($Id, $EndTime, $JobType = 'Script Tool Job') {
    [pscustomobject]@{
        id = $Id
        endTime = $EndTime
        startTime = $EndTime - 100
        jobName = "Job $Id"
        jobType = $JobType
    }
}

function New-Config($Base, $InitialMode = 'all') {
    [pscustomobject]@{
        OutputDir = Join-Path $Base 'outputs'
        StatePath = Join-Path $Base 'state.json'
        ReportPath = Join-Path $Base 'report.json'
        PageSize = 2
        InitialMode = $InitialMode
        JobType = 'Script Tool Job'
        JobName = ''
    }
}

$base = Join-Path ([IO.Path]::GetTempPath()) "netld-job-output-$([guid]::NewGuid())"
try {
    $records = @((New-Execution 3 3000), (New-Execution 2 2000 'Report Job'), (New-Execution 1 1000))
    $offsets = [Collections.Generic.List[int]]::new()
    $search = {
        param($offset, $pageSize)
        $offsets.Add($offset)
        [pscustomobject]@{
            offset = $offset
            pageSize = $pageSize
            total = if ($offset -eq 0) { $records.Count } else { 0 }
            executionData = @($records | Select-Object -Skip $offset -First $pageSize)
        }
    }
    $details = { param($executionId) @([pscustomobject]@{ id = $executionId * 10; managedNetwork = 'Default'; ipAddress = '192.0.2.10' }) }
    $download = { param($executionId, $detailId) [Text.Encoding]::UTF8.GetBytes("output $executionId") }
    $report = Export-JobExecutionOutputData (New-Config $base) $search $details $download '2026-09-02T00:00:00Z'

    Assert-Equal '0,2' ($offsets -join ',') 'Paging offsets'
    Assert-Equal 2 $report.archivedCount 'Archived executions'
    Assert-Equal 2 $report.outputCount 'Archived outputs'
    Assert-Equal 3000 (Get-Content (Join-Path $base 'state.json') -Raw | ConvertFrom-Json).lastEndTime 'Watermark'
}
finally {
    Remove-Item $base -Recurse -Force -ErrorAction SilentlyContinue
}

$base = Join-Path ([IO.Path]::GetTempPath()) "netld-job-output-$([guid]::NewGuid())"
try {
    $config = New-Config $base 'latest'
    $records = @((New-Execution 1 1000))
    $search = { param($offset, $pageSize) [pscustomobject]@{ offset = 0; pageSize = $pageSize; total = $records.Count; executionData = $records } }
    $details = { param($executionId) @([pscustomobject]@{ id = $executionId * 10; managedNetwork = 'Default'; ipAddress = '192.0.2.10' }) }
    $download = { param($executionId, $detailId) [Text.Encoding]::UTF8.GetBytes("output $executionId") }
    $first = Export-JobExecutionOutputData $config $search $details $download '2026-09-02T00:00:00Z'
    $records = @((New-Execution 2 2000), (New-Execution 1 1000))
    $second = Export-JobExecutionOutputData $config $search $details $download '2026-09-02T00:01:00Z'

    Assert-Equal $true $first.initialBaseline 'Initial baseline'
    Assert-Equal 0 $first.archivedCount 'Initial archive count'
    Assert-Equal 1 $second.archivedCount 'Incremental archive count'
}
finally {
    Remove-Item $base -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Host 'PowerShell job-execution-output tests passed.'
