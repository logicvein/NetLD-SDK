param(
    [string]$EnvPath = "$PSScriptRoot/.env"
)

. "$PSScriptRoot/NetLDExampleClient.ps1"

Import-DotEnv -Path $EnvPath

$baseUrl = $env:NETLD_BASE_URL
$apiKey = $env:NETLD_API_KEY
$network = if ($env:NETLD_NETWORK) { $env:NETLD_NETWORK } else { "Default" }
$offset = if ($env:NETLD_JOB_OFFSET) { [int]$env:NETLD_JOB_OFFSET } else { 0 }
$pageSize = if ($env:NETLD_JOB_PAGE_SIZE) { [int]$env:NETLD_JOB_PAGE_SIZE } else { 100 }
$sortColumn = if ($null -ne $env:NETLD_JOB_SORT_COLUMN) { $env:NETLD_JOB_SORT_COLUMN } else { "" }
$descending = if ($env:NETLD_JOB_DESCENDING) {
    $env:NETLD_JOB_DESCENDING -eq "true"
} else {
    $false
}
$debugMode = $env:NETLD_DEBUG -eq "1"

if (-not $baseUrl) {
    throw [NetLDError]::new("Set NETLD_BASE_URL in .env before running this example.")
}

if (-not $apiKey) {
    throw [NetLDError]::new("Set NETLD_API_KEY before running this example.")
}

$client = [NetLDClient]::new($baseUrl, $apiKey, 10, $debugMode)
$client.Login()

$pageData = $client.SearchAvailableJobs(
    @($network),
    $offset,
    $pageSize,
    $sortColumn,
    $descending
)

Show-AvailableJobs -PageData $pageData
