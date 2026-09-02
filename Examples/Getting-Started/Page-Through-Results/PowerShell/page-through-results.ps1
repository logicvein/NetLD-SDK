param(
    [string]$EnvPath = "$PSScriptRoot/.env"
)

. "$PSScriptRoot/NetLDExampleClient.ps1"
Import-DotEnv -Path $EnvPath

$baseUrl = $env:NETLD_BASE_URL
$apiKey = $env:NETLD_API_KEY
$network = if ($env:NETLD_NETWORK) { $env:NETLD_NETWORK } else { "Default" }
$ipAddress = $env:NETLD_DEVICE_IP
$pageSize = if ($env:NETLD_PAGE_SIZE) { [int]$env:NETLD_PAGE_SIZE } else { 10 }
$debugMode = $env:NETLD_DEBUG -eq "1"

if (-not $baseUrl) { throw [NetLDError]::new("Set NETLD_BASE_URL in .env before running this example.") }
if (-not $apiKey) { throw [NetLDError]::new("Set NETLD_API_KEY in .env before running this example.") }
if (-not $ipAddress) { throw [NetLDError]::new("Set NETLD_DEVICE_IP in .env before running this example.") }
if ($pageSize -le 0) { throw [NetLDError]::new("NETLD_PAGE_SIZE must be a positive integer.") }

$client = [NetLDClient]::new($baseUrl, $apiKey, 10, $debugMode)
$client.Login()

$changeLogs = @()
$offset = 0
$total = $null

while ($null -eq $total -or $offset -lt $total) {
    $page = $client.GetConfigurationChangeLogPage($network, $ipAddress, $offset, $pageSize)
    if ($null -eq $page -or $null -eq $page.changeLogs) {
        throw [NetLDError]::new(
            "Configuration.retrieveSnapshotChangeLog returned an invalid page."
        )
    }
    $pageLogs = @($page.changeLogs)
    $pageOffset = if ($null -ne $page.offset) { [int]$page.offset } else { $offset }
    $reportedTotal = if ($null -ne $page.total) {
        [int]$page.total
    } else {
        $pageOffset + $pageLogs.Count
    }
    if ($null -eq $total -or $reportedTotal -gt $total) {
        $total = $reportedTotal
    }
    $changeLogs += $pageLogs
    $nextOffset = $pageOffset + $pageLogs.Count

    Write-Host "Fetched $($pageLogs.Count) records at offset $pageOffset ($nextOffset of $total)"

    if ($nextOffset -ge $total) { break }
    if ($pageLogs.Count -eq 0 -or $nextOffset -le $offset) {
        throw [NetLDError]::new("Paging stopped before all results were returned.")
    }
    $offset = $nextOffset
}

@{
    total = $changeLogs.Count
    changeLogs = $changeLogs
} | ConvertTo-Json -Depth 20
