param([string]$EnvPath = (Join-Path $PSScriptRoot '.env'))

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'NetLDExampleClient.ps1')

try {
    Import-DotEnv -Path $EnvPath
    $parameters = New-CreateDeviceParameters `
        -Network $(if ($env:NETLD_NETWORK) { $env:NETLD_NETWORK } else { 'Default' }) `
        -IpAddress $(if ($env:NETLD_DEVICE_IP) { $env:NETLD_DEVICE_IP } else { '192.0.2.10' }) `
        -AdapterId $(if ($env:NETLD_ADAPTER_ID) { $env:NETLD_ADAPTER_ID } else { 'Cisco::IOS' })
    $parameters | ConvertTo-Json
    if ($env:NETLD_CREATE_DEVICE -ne 'true') {
        Write-Host 'Dry run only. Set NETLD_CREATE_DEVICE=true after reviewing these parameters.'
        exit 0
    }
    if (-not $env:NETLD_BASE_URL) { throw [NetLDError]::new('Set NETLD_BASE_URL in .env before running this example.') }
    if (-not $env:NETLD_API_KEY) { throw [NetLDError]::new('Set NETLD_API_KEY in .env before running this example.') }

    $client = [NetLDClient]::new($env:NETLD_BASE_URL, $env:NETLD_API_KEY, 10)
    $client.Login()
    if ($client.GetDevice($parameters.network, $parameters.ipAddress)) {
        throw [NetLDError]::new('A device with this IP address already exists in the selected network.')
    }
    $createResult = $client.CreateDevice($parameters.network, $parameters.ipAddress, $parameters.adapterId)
    if ($null -ne $createResult) {
        throw [NetLDError]::new("Inventory.createDevice returned: $createResult")
    }
    $device = $client.GetDevice($parameters.network, $parameters.ipAddress)
    if (-not $device) { throw [NetLDError]::new('The create call succeeded, but Inventory.getDevice returned no device.') }
    if ($device.ipAddress -ne $parameters.ipAddress -or $device.adapterId -ne $parameters.adapterId) {
        throw [NetLDError]::new('The created device does not match the requested IP address and adapter ID.')
    }
    Write-Host 'Device created and verified:'
    $device | ConvertTo-Json -Depth 20
}
catch {
    Write-Error $_.Exception.Message
    exit 1
}
