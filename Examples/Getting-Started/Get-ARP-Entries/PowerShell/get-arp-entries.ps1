param(
    [string]$EnvPath = "$PSScriptRoot/.env"
)

. "$PSScriptRoot/NetLDExampleClient.ps1"

Import-DotEnv -Path $EnvPath

$baseUrl = $env:NETLD_BASE_URL
$apiKey = $env:NETLD_API_KEY
$networkAddress = if ($env:NETLD_ARP_NETWORK_ADDRESS) { $env:NETLD_ARP_NETWORK_ADDRESS } else { "10.95.1.0/24" }
$network = if ($env:NETLD_NETWORK) { $env:NETLD_NETWORK } else { "Default" }
$offset = if ($env:NETLD_ARP_OFFSET) { [int]$env:NETLD_ARP_OFFSET } else { 0 }
$pageSize = if ($env:NETLD_ARP_PAGE_SIZE) { [int]$env:NETLD_ARP_PAGE_SIZE } else { 100 }
$sort = if ($env:NETLD_ARP_SORT) { $env:NETLD_ARP_SORT } else { "ipAddress" }
$descending = if ($env:NETLD_ARP_DESCENDING) {
    $env:NETLD_ARP_DESCENDING -eq "true"
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

$pageData = $client.GetArpEntries(
    $networkAddress,
    @($network),
    $offset,
    $pageSize,
    $sort,
    $descending
)

Show-ArpEntries -PageData $pageData
