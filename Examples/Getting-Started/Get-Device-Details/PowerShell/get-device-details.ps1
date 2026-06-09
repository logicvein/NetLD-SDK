param(
    [string]$EnvPath = "$PSScriptRoot/.env"
)

. "$PSScriptRoot/NetLDExampleClient.ps1"

Import-DotEnv -Path $EnvPath

$baseUrl = $env:NETLD_BASE_URL
$apiKey = $env:NETLD_API_KEY
$network = if ($env:NETLD_NETWORK) { $env:NETLD_NETWORK } else { "Default" }
$deviceIp = if ($env:NETLD_DEVICE_IP) { $env:NETLD_DEVICE_IP } else { "10.95.1.40" }
$debugMode = $env:NETLD_DEBUG -eq "1"

if (-not $baseUrl) {
    throw [NetLDError]::new("Set NETLD_BASE_URL in .env before running this example.")
}

if (-not $apiKey) {
    throw [NetLDError]::new("Set NETLD_API_KEY before running this example.")
}

$client = [NetLDClient]::new($baseUrl, $apiKey, 10, $debugMode)
$client.Login()

$device = $client.GetDevice($network, $deviceIp)

Show-DeviceDetails -Device $device
