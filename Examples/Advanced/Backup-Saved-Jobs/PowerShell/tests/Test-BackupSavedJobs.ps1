$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSScriptRoot '..' 'BackupSavedJobs.psm1') -Force

function Assert-Equal($Expected, $Actual, [string]$Message) {
    if ($Expected -ne $Actual) { throw "$Message Expected '$Expected', got '$Actual'." }
}

$offsets = [Collections.Generic.List[int]]::new()
$fetchPage = {
    param($offset, $pageSize)
    $offsets.Add([int]$offset)
    if ($offset -eq 0) {
        return [pscustomobject]@{ pageSize = 2; total = 3; jobData = @(
            [pscustomobject]@{ jobId = 3; jobName = 'Three' },
            [pscustomobject]@{ jobId = 1; jobName = 'One' }
        ) }
    }
    return [pscustomobject]@{ pageSize = 2; total = 0; jobData = @(
        [pscustomobject]@{ jobId = 2; jobName = 'Two' }
    ) }
}
$fetchJob = {
    param($jobId)
    if ($jobId -eq 2) { throw 'simulated retrieval failure' }
    return [pscustomobject]@{ jobId = $jobId; jobName = [string]$jobId; jobParameters = @{ z = 'last'; a = 'first' } }
}
$directory = Join-Path ([IO.Path]::GetTempPath()) "netld-jobs-$([guid]::NewGuid())"
try {
    $output = Join-Path $directory 'jobs.json'
    $failure = Join-Path $directory 'failures.json'
    $result = Backup-NetLDSavedJobs $fetchPage $fetchJob @('Lab', 'Default') 2 $output $failure '2026-08-28T12:00:00Z'
    $backup = Get-Content $output -Raw | ConvertFrom-Json
    $failures = Get-Content $failure -Raw | ConvertFrom-Json
    Assert-Equal 2 $result.JobCount 'Job count failed.'
    Assert-Equal 1 $result.FailureCount 'Failure count failed.'
    Assert-Equal '0,2' ($offsets -join ',') 'Pagination offsets failed.'
    Assert-Equal '1,3' (@($backup.jobs.jobId) -join ',') 'Job sort failed.'
    Assert-Equal 'Default,Lab' (@($backup.networks) -join ',') 'Network sort failed.'
    Assert-Equal $false $backup.complete 'Completeness flag failed.'
    Assert-Equal 2 $failures.failures[0].jobId 'Failure identity failed.'
}
finally { Remove-Item -LiteralPath $directory -Recurse -Force -ErrorAction SilentlyContinue }

Write-Host 'PowerShell tests passed.'
