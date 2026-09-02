[CmdletBinding()] param([string]$EnvFile=(Join-Path $PSScriptRoot '.env'))
$ErrorActionPreference='Stop'
if (Test-Path -LiteralPath $EnvFile) { foreach($line in Get-Content -LiteralPath $EnvFile){if($line -match '^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)\s*$' -and -not $line.TrimStart().StartsWith('#')){$value=$Matches[2].Trim();if(($value.StartsWith('"')-and$value.EndsWith('"'))-or($value.StartsWith("'")-and$value.EndsWith("'"))){$value=$value.Substring(1,$value.Length-2)};[Environment]::SetEnvironmentVariable($Matches[1],$value)}}}
if(-not $env:NETLD_BASE_URL -or -not $env:NETLD_API_KEY){throw 'NETLD_BASE_URL and NETLD_API_KEY are required.'}
function Resolve-Output([string]$Value,[string]$Default){if(-not $Value){$Value=$Default};if([IO.Path]::IsPathRooted($Value)){$Value}else{Join-Path $PSScriptRoot $Value}}
$mode=if($env:NETLD_INITIAL_MODE){$env:NETLD_INITIAL_MODE.ToLowerInvariant()}else{'latest'};if($mode -notin @('latest','all')){throw 'NETLD_INITIAL_MODE must be either latest or all.'}
$config=[pscustomobject]@{BaseUrl=$env:NETLD_BASE_URL.TrimEnd('/');ApiKey=$env:NETLD_API_KEY;Networks=@(($env:NETLD_NETWORKS ?? 'Default').Split(',').Trim()|Where-Object{$_}|Sort-Object -Unique);ArchiveDir=Resolve-Output $env:NETLD_ARCHIVE_DIR 'configuration-archive';StatePath=Resolve-Output $env:NETLD_STATE_FILE 'configuration-archive-state.json';RunReportPath=Resolve-Output $env:NETLD_RUN_REPORT_FILE 'configuration-archive-run.json';InventoryPageSize=if($env:NETLD_INVENTORY_PAGE_SIZE){[int]$env:NETLD_INVENTORY_PAGE_SIZE}else{500};HistoryPageSize=if($env:NETLD_HISTORY_PAGE_SIZE){[int]$env:NETLD_HISTORY_PAGE_SIZE}else{500};SearchScheme=if($env:NETLD_SEARCH_SCHEME){$env:NETLD_SEARCH_SCHEME}else{'ipAddress'};SearchQuery=if($env:NETLD_SEARCH_QUERY){$env:NETLD_SEARCH_QUERY}else{''};InitialMode=$mode}
Import-Module (Join-Path $PSScriptRoot 'ArchiveConfigurationRevisions.psm1') -Force
$report=Start-ConfigurationRevisionArchive $config
Write-Host "Processed $($report.deviceCount) devices and archived $($report.archivedCount) revisions"
Write-Host "Recorded $($report.failureCount) failures in $($config.RunReportPath)"
if($report.failureCount){exit 2}
