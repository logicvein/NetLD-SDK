[CmdletBinding()]
param([string]$EnvPath = (Join-Path $PSScriptRoot '.env'))

$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSScriptRoot 'ExportThirdEyeViolations.psm1') -Force

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

function Get-PositiveInteger($Value, [string]$Name, [int]$Default) {
    if (-not $Value) { return $Default }
    $parsed = 0
    if (-not [int]::TryParse($Value, [ref]$parsed) -or $parsed -le 0) {
        throw "$Name must be a positive integer."
    }
    return $parsed
}

$outputFormat = ($env:NETLD_OUTPUT_FORMAT ?? 'csv').Trim().ToLowerInvariant()
if ($outputFormat -notin @('csv', 'json')) { throw 'NETLD_OUTPUT_FORMAT must be csv or json.' }
$config = [pscustomobject]@{
    BaseUrl = $env:NETLD_BASE_URL.TrimEnd('/')
    ApiKey = $env:NETLD_API_KEY
    OutputDir = Resolve-Output $env:NETLD_OUTPUT_DIR 'violation-exports'
    OutputFormat = $outputFormat
    StatePath = Resolve-Output $env:NETLD_STATE_FILE 'violation-export-state.json'
    ReportPath = Resolve-Output $env:NETLD_RUN_REPORT_FILE 'violation-export-run.json'
    PageSize = Get-PositiveInteger $env:NETLD_PAGE_SIZE 'NETLD_PAGE_SIZE' 100
    InitialLookbackHours = Get-PositiveInteger $env:NETLD_INITIAL_LOOKBACK_HOURS 'NETLD_INITIAL_LOOKBACK_HOURS' 24
    SearchQueries = @(ConvertFrom-SearchQueries ($env:NETLD_SEARCH_QUERIES ?? '[]'))
}

try {
    $report = Invoke-ExportThirdEyeViolations $config
    Write-Host "Found $($report.resultCount) violations and exported $($report.exportedCount)."
    Write-Host "Run report: $($config.ReportPath)"
}
catch {
    Write-Error $_
    exit 1
}
