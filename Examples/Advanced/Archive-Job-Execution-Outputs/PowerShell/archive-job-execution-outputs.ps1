[CmdletBinding()]
param([string]$EnvPath = (Join-Path $PSScriptRoot '.env'))

$ErrorActionPreference = 'Stop'
if (Test-Path $EnvPath) {
    foreach ($raw in Get-Content $EnvPath) {
        if ($raw -match '^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)\s*$' -and -not $raw.TrimStart().StartsWith('#')) {
            $value = $Matches[2].Trim().Trim('"').Trim("'")
            [Environment]::SetEnvironmentVariable($Matches[1], $value)
        }
    }
}
if (-not $env:NETLD_BASE_URL -or -not $env:NETLD_API_KEY) {
    throw 'Set NETLD_BASE_URL and NETLD_API_KEY in the environment file.'
}

function Resolve-Output($Value, $Default) {
    if (-not $Value) { $Value = $Default }
    if ([IO.Path]::IsPathRooted($Value)) { return $Value }
    return Join-Path $PSScriptRoot $Value
}

$pageSize = if ($env:NETLD_PAGE_SIZE) { [int]$env:NETLD_PAGE_SIZE } else { 100 }
if ($pageSize -le 0) { throw 'NETLD_PAGE_SIZE must be a positive integer.' }
$initialMode = ($env:NETLD_INITIAL_MODE ?? 'latest').ToLowerInvariant()
if ($initialMode -notin @('latest', 'all')) { throw 'NETLD_INITIAL_MODE must be latest or all.' }
$config = [pscustomobject]@{
    BaseUrl = $env:NETLD_BASE_URL.TrimEnd('/')
    ApiKey = $env:NETLD_API_KEY
    OutputDir = Resolve-Output $env:NETLD_OUTPUT_DIR 'job-execution-outputs'
    StatePath = Resolve-Output $env:NETLD_STATE_FILE 'job-execution-output-state.json'
    ReportPath = Resolve-Output $env:NETLD_RUN_REPORT_FILE 'job-execution-output-run.json'
    PageSize = $pageSize
    InitialMode = $initialMode
    SearchScheme = $env:NETLD_SEARCH_SCHEME ?? ''
    SearchData = $env:NETLD_SEARCH_DATA ?? ''
    JobType = $env:NETLD_JOB_TYPE ?? 'Script Tool Job'
    JobName = $env:NETLD_JOB_NAME ?? ''
}

Import-Module (Join-Path $PSScriptRoot 'ArchiveJobExecutionOutputs.psm1') -Force
try {
    $report = Invoke-ArchiveJobExecutionOutputs $config
    if ($report.initialBaseline) {
        Write-Host 'Recorded the latest completed execution as the initial baseline.'
    }
    Write-Host "Archived $($report.archivedCount) executions and $($report.outputCount) outputs; recorded $($report.failureCount) failures in $($config.ReportPath)"
    if ($report.failureCount) { exit 2 }
}
catch {
    Write-Error $_
    exit 1
}
