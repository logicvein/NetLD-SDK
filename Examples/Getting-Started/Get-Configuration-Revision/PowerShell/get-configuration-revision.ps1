param(
    [string]$EnvPath = "$PSScriptRoot/.env"
)

. "$PSScriptRoot/NetLDExampleClient.ps1"

Import-DotEnv -Path $EnvPath

$baseUrl = $env:NETLD_BASE_URL
$apiKey = $env:NETLD_API_KEY
$network = if ($env:NETLD_NETWORK) { $env:NETLD_NETWORK } else { "Default" }
$deviceIp = if ($env:NETLD_DEVICE_IP) { $env:NETLD_DEVICE_IP } else { "10.95.1.40" }
$configPath = if ($env:NETLD_CONFIG_PATH) { $env:NETLD_CONFIG_PATH } else { "/running-config" }
$debugMode = $env:NETLD_DEBUG -eq "1"

if (-not $baseUrl) {
    throw [NetLDError]::new("Set NETLD_BASE_URL in .env before running this example.")
}

if (-not $apiKey) {
    throw [NetLDError]::new("Set NETLD_API_KEY before running this example.")
}

$client = [NetLDClient]::new($baseUrl, $apiKey, 10, $debugMode)
$client.Login()

$pageData = $client.GetConfigurationHistory(@($network), "ipAddress", $deviceIp, 0, 100, "session", $true)
$matches = @($pageData.configHistoryItems | Where-Object { $_.path -eq $configPath })

if ($matches.Count -eq 0) {
    throw [NetLDError]::new(
        "No configuration history item for `"$configPath`" was found on $deviceIp@$network."
    )
}

$historyItem = $matches[0]
$revision = $client.RetrieveRevision(
    $historyItem.managedNetwork,
    $historyItem.ipAddress,
    $historyItem.path,
    [long]$historyItem.lastChanged
)

if (-not $revision) {
    throw [NetLDError]::new("Configuration.retrieveRevision returned no revision.")
}

$metadata = $revision | Select-Object * -ExcludeProperty content
Write-Host "Revision metadata:"
$metadata | ConvertTo-Json -Depth 12

$decodedContent = ConvertFrom-RevisionContent -Revision $revision
if ($null -eq $decodedContent) {
    Write-Host "Revision content is empty or binary; Base64 content was not printed."
} else {
    Write-Host "Decoded revision content:"
    Write-Output $decodedContent
}
