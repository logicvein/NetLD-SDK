param(
    [string]$EnvPath = "$PSScriptRoot/.env"
)

. "$PSScriptRoot/NetLDExampleClient.ps1"

Import-DotEnv -Path $EnvPath

$baseUrl = $env:NETLD_BASE_URL
$apiKey = $env:NETLD_API_KEY
$network = if ($env:NETLD_NETWORK) { $env:NETLD_NETWORK } else { "Default" }
$scheme = if ($env:NETLD_HISTORY_SCHEME) { $env:NETLD_HISTORY_SCHEME } else { "ipAddress" }
$data = if ($env:NETLD_HISTORY_DATA) { $env:NETLD_HISTORY_DATA } else { "10.95.1.40" }
$offset = if ($env:NETLD_HISTORY_OFFSET) { [int]$env:NETLD_HISTORY_OFFSET } else { 0 }
$pageSize = if ($env:NETLD_HISTORY_PAGE_SIZE) { [int]$env:NETLD_HISTORY_PAGE_SIZE } else { 100 }
$sortColumn = if ($env:NETLD_HISTORY_SORT_COLUMN) { $env:NETLD_HISTORY_SORT_COLUMN } else { "session" }
$descending = if ($env:NETLD_HISTORY_DESCENDING) {
    $env:NETLD_HISTORY_DESCENDING -eq "true"
} else {
    $true
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

$pageData = $client.GetConfigurationHistory(
    @($network),
    $scheme,
    $data,
    $offset,
    $pageSize,
    $sortColumn,
    $descending
)

Show-ConfigurationHistory -PageData $pageData
