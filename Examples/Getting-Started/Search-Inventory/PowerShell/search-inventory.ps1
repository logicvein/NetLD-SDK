param(
    [string]$EnvPath = "$PSScriptRoot/.env"
)

. "$PSScriptRoot/NetLDExampleClient.ps1"

Import-DotEnv -Path $EnvPath

$baseUrl = $env:NETLD_BASE_URL
$apiKey = $env:NETLD_API_KEY
$network = if ($env:NETLD_NETWORK) { $env:NETLD_NETWORK } else { "Default" }
$searchScheme = if ($env:NETLD_SEARCH_SCHEME) { $env:NETLD_SEARCH_SCHEME } else { "ipAddress" }
$searchQuery = if ($env:NETLD_SEARCH_QUERY) { $env:NETLD_SEARCH_QUERY } else { "10.95.1.0/24" }
$debugMode = $env:NETLD_DEBUG -eq "1"

if (-not $baseUrl) {
    throw [NetLDError]::new("Set NETLD_BASE_URL in .env before running this example.")
}

if (-not $apiKey) {
    throw [NetLDError]::new("Set NETLD_API_KEY before running this example.")
}

$client = [NetLDClient]::new($baseUrl, $apiKey, 10, $debugMode)
$client.Login()

$pageData = $client.SearchInventory(
    @($network),
    @($searchScheme),
    @($searchQuery),
    0,
    100,
    "ipAddress",
    $false
)

Show-Devices -PageData $pageData
