Set-StrictMode -Version Latest

class AdvancedExampleError : System.Exception {
    AdvancedExampleError([string]$message) : base($message) {}
}

$script:InterfaceFields = @(
    'network', 'deviceIpAddress', 'hostname', 'interfaceId', 'interfaceIndex',
    'name', 'ifName', 'type', 'description', 'comment', 'macAddress', 'mtu',
    'speed', 'adminUp', 'vrfName', 'ipAddresses'
)
$script:FailureFields = @('network', 'deviceIpAddress', 'hostname', 'error')

function Import-DotEnv {
    param([Parameter(Mandatory)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) { return }
    Get-Content -LiteralPath $Path | ForEach-Object {
        $line = $_.Trim()
        if (-not $line -or $line.StartsWith('#') -or -not $line.Contains('=')) { return }
        $name, $value = $line.Split('=', 2)
        [Environment]::SetEnvironmentVariable($name.Trim(), $value.Trim().Trim('"').Trim("'"), 'Process')
    }
}

function Get-RequiredEnvironmentValue {
    param([Parameter(Mandatory)][string]$Name)
    $value = [Environment]::GetEnvironmentVariable($Name, 'Process')
    if (-not $value) { throw [AdvancedExampleError]::new("Set $Name in the environment file.") }
    return $value
}

function ConvertTo-ManagedNetworkList {
    param([Parameter(Mandatory)][string]$Value)
    $networks = @($Value.Split(',') | ForEach-Object { $_.Trim() } | Where-Object { $_ })
    if ($networks.Count -eq 0) {
        throw [AdvancedExampleError]::new('NETLD_NETWORKS must contain at least one managed network.')
    }
    return $networks
}

function Get-ObjectPropertyValue {
    param([object]$InputObject, [string]$Name)
    if ($null -eq $InputObject) { return $null }
    $property = $InputObject.PSObject.Properties[$Name]
    return $(if ($property) { $property.Value } else { $null })
}

function ConvertTo-InterfaceIpList {
    param([object]$Interface)
    $values = @()
    foreach ($address in @(Get-ObjectPropertyValue $Interface 'ipAddresses')) {
        $ipAddress = [string](Get-ObjectPropertyValue $address 'ipAddress')
        if (-not $ipAddress.Trim()) { continue }
        $prefix = Get-ObjectPropertyValue $address 'cidrPrefix'
        $values += $(if ($null -ne $prefix) { "$ipAddress/$prefix" } else { $ipAddress })
    }
    return $values -join ';'
}

function ConvertTo-InterfaceRow {
    param([object]$Device, [object]$Interface)
    $adminUp = Get-ObjectPropertyValue $Interface 'adminUp'
    if ($adminUp -is [bool]) { $adminUp = $adminUp.ToString().ToLowerInvariant() }
    return [pscustomobject][ordered]@{
        network = Get-ObjectPropertyValue $Device 'network'
        deviceIpAddress = Get-ObjectPropertyValue $Device 'ipAddress'
        hostname = Get-ObjectPropertyValue $Device 'hostname'
        interfaceId = Get-ObjectPropertyValue $Interface 'id'
        interfaceIndex = Get-ObjectPropertyValue $Interface 'index'
        name = Get-ObjectPropertyValue $Interface 'name'
        ifName = Get-ObjectPropertyValue $Interface 'ifName'
        type = Get-ObjectPropertyValue $Interface 'type'
        description = Get-ObjectPropertyValue $Interface 'description'
        comment = Get-ObjectPropertyValue $Interface 'comment'
        macAddress = Get-ObjectPropertyValue $Interface 'macAddress'
        mtu = Get-ObjectPropertyValue $Interface 'mtu'
        speed = Get-ObjectPropertyValue $Interface 'speed'
        adminUp = $adminUp
        vrfName = Get-ObjectPropertyValue $Interface 'vrfName'
        ipAddresses = ConvertTo-InterfaceIpList $Interface
    }
}

function New-NetLDSession {
    param([string]$BaseUrl, [string]$ApiKey, [int]$TimeoutSec)
    $session = $null
    try {
        [void](Invoke-WebRequest -Uri "$($BaseUrl.TrimEnd('/'))/rest" `
            -Headers @{ Authorization = "Bearer $ApiKey" } -SessionVariable session `
            -MaximumRedirection 0 -TimeoutSec $TimeoutSec -ErrorAction Stop)
    }
    catch { throw [AdvancedExampleError]::new("Could not authenticate to $BaseUrl.") }
    return $session
}

function Invoke-NetLDCall {
    param([hashtable]$Connection, [string]$Method, [object]$Parameters)
    $body = @{ jsonrpc = '2.0'; method = $Method; params = $Parameters; id = [guid]::NewGuid().ToString() } |
        ConvertTo-Json -Depth 50
    try {
        $response = Invoke-WebRequest -Uri "$($Connection.BaseUrl.TrimEnd('/'))/rest" -Method Post `
            -Headers @{ Authorization = "Bearer $($Connection.ApiKey)"; 'Content-Type' = 'application/json' } `
            -Body $body -WebSession $Connection.Session -MaximumRedirection 0 `
            -TimeoutSec $Connection.TimeoutSec -ErrorAction Stop
    }
    catch { throw [AdvancedExampleError]::new("netLD API call $Method failed.") }
    $data = $response.Content | ConvertFrom-Json
    $errorProperty = $data.PSObject.Properties['error']
    if ($errorProperty -and $errorProperty.Value) {
        throw [AdvancedExampleError]::new("netLD API call $Method failed: $($errorProperty.Value | ConvertTo-Json -Compress -Depth 20)")
    }
    $resultProperty = $data.PSObject.Properties['result']
    if (-not $resultProperty) { throw [AdvancedExampleError]::new("netLD API call $Method returned no result field.") }
    return $resultProperty.Value
}

function Get-NetLDInventoryDevices {
    param([scriptblock]$FetchPage, [int]$PageSize)
    if ($PageSize -le 0) { throw [AdvancedExampleError]::new('NETLD_PAGE_SIZE must be a positive integer.') }
    $offset = 0
    $total = $null
    while ($true) {
        $page = & $FetchPage $offset $PageSize
        if (-not $page) { throw [AdvancedExampleError]::new('Inventory.search returned no page data.') }
        $devices = @($page.devices)
        foreach ($device in $devices) { Write-Output $device }
        $pageSizeProperty = $page.PSObject.Properties['pageSize']
        $returnedPageSize = if ($pageSizeProperty -and $pageSizeProperty.Value) { [int]$pageSizeProperty.Value } else { $PageSize }
        if ($returnedPageSize -le 0) { throw [AdvancedExampleError]::new('Inventory.search returned an invalid page size.') }
        $totalProperty = $page.PSObject.Properties['total']
        if ($null -eq $total -and $totalProperty -and $null -ne $totalProperty.Value) { $total = [int]$totalProperty.Value }
        if ($null -ne $total -and $offset + $devices.Count -ge $total) { break }
        if ($null -eq $total -and $devices.Count -lt $returnedPageSize) { break }
        if ($devices.Count -eq 0) { throw [AdvancedExampleError]::new('Inventory.search returned an empty page before the reported total.') }
        $offset += $returnedPageSize
    }
}

function Write-AtomicCsv {
    param([object[]]$Rows, [string[]]$Fields, [string]$OutputPath)
    $directory = Split-Path -Parent $OutputPath
    if (-not $directory) { $directory = '.' }
    [void](New-Item -ItemType Directory -Path $directory -Force)
    $temporaryPath = Join-Path $directory ".$([IO.Path]::GetFileName($OutputPath)).$([guid]::NewGuid()).tmp"
    try {
        if ($Rows.Count -gt 0) {
            $Rows | Select-Object -Property $Fields | Export-Csv -LiteralPath $temporaryPath -NoTypeInformation -Encoding utf8
        }
        else {
            $empty = [ordered]@{}
            foreach ($field in $Fields) { $empty[$field] = $null }
            $header = @([pscustomobject]$empty | ConvertTo-Csv -NoTypeInformation)[0]
            Set-Content -LiteralPath $temporaryPath -Value $header -Encoding utf8
        }
        Move-Item -LiteralPath $temporaryPath -Destination $OutputPath -Force
    }
    catch {
        Remove-Item -LiteralPath $temporaryPath -Force -ErrorAction SilentlyContinue
        throw
    }
}

function Export-NetLDInterfaceData {
    param([object[]]$Devices, [scriptblock]$FetchInterfaces, [string]$OutputPath, [string]$FailurePath)
    $rows = [Collections.Generic.List[object]]::new()
    $failures = [Collections.Generic.List[object]]::new()
    foreach ($device in $Devices) {
        try {
            $interfaces = @(& $FetchInterfaces $device)
            foreach ($interface in $interfaces) { $rows.Add((ConvertTo-InterfaceRow $device $interface)) }
        }
        catch {
            $failures.Add([pscustomobject][ordered]@{
                network = Get-ObjectPropertyValue $device 'network'
                deviceIpAddress = Get-ObjectPropertyValue $device 'ipAddress'
                hostname = Get-ObjectPropertyValue $device 'hostname'
                error = $_.Exception.Message
            })
        }
    }
    Write-AtomicCsv -Rows @($rows) -Fields $script:InterfaceFields -OutputPath $OutputPath
    Write-AtomicCsv -Rows @($failures) -Fields $script:FailureFields -OutputPath $FailurePath
    return [pscustomobject]@{
        DeviceCount = $Devices.Count; InterfaceCount = $rows.Count; FailureCount = $failures.Count
    }
}

function Invoke-ExportDeviceInterfaces {
    param([Parameter(Mandatory)][string]$EnvPath)
    Import-DotEnv $EnvPath
    $baseUrl = Get-RequiredEnvironmentValue 'NETLD_BASE_URL'
    $apiKey = Get-RequiredEnvironmentValue 'NETLD_API_KEY'
    $networks = ConvertTo-ManagedNetworkList $(if ($env:NETLD_NETWORKS) { $env:NETLD_NETWORKS } else { 'Default' })
    $pageSize = if ($env:NETLD_PAGE_SIZE) { [int]$env:NETLD_PAGE_SIZE } else { 500 }
    $scheme = if ($env:NETLD_SEARCH_SCHEME) { $env:NETLD_SEARCH_SCHEME } else { 'ipAddress' }
    $query = if ($null -ne $env:NETLD_SEARCH_QUERY) { $env:NETLD_SEARCH_QUERY } else { '' }
    if (-not $query.EndsWith("`n")) { $query = "$query`n" }
    $outputName = if ($env:NETLD_OUTPUT_FILE) { $env:NETLD_OUTPUT_FILE } else { 'interfaces.csv' }
    $failureName = if ($env:NETLD_FAILURE_FILE) { $env:NETLD_FAILURE_FILE } else { 'interface-failures.csv' }
    $outputPath = if ([IO.Path]::IsPathRooted($outputName)) { $outputName } else { Join-Path $PSScriptRoot $outputName }
    $failurePath = if ([IO.Path]::IsPathRooted($failureName)) { $failureName } else { Join-Path $PSScriptRoot $failureName }
    $timeout = if ($env:REQUEST_TIMEOUT_SECONDS) { [int]$env:REQUEST_TIMEOUT_SECONDS } else { 30 }
    $connection = @{
        BaseUrl = $baseUrl; ApiKey = $apiKey; TimeoutSec = $timeout
        Session = New-NetLDSession -BaseUrl $baseUrl -ApiKey $apiKey -TimeoutSec $timeout
    }
    $fetchPage = {
        param($offset, $requestedPageSize)
        Invoke-NetLDCall $connection 'Inventory.search' @{
            network = $networks; scheme = $scheme; query = $query
            pageData = @{ offset = $offset; pageSize = $requestedPageSize }
            sortColumn = 'ipAddress'; descending = $false
        }
    }
    $fetchInterfaces = {
        param($device)
        @(Invoke-NetLDCall $connection 'Inventory.getDeviceInterfaces' @{
            network = $device.network; ipAddress = $device.ipAddress
        })
    }
    $devices = @(Get-NetLDInventoryDevices $fetchPage $pageSize)
    $result = Export-NetLDInterfaceData $devices $fetchInterfaces $outputPath $failurePath
    Write-Host "Processed $($result.DeviceCount) devices and wrote $($result.InterfaceCount) interfaces to $outputPath"
    Write-Host "Wrote $($result.FailureCount) device lookup failures to $failurePath"
    return $result
}

Export-ModuleMember -Function @(
    'ConvertTo-InterfaceIpList', 'ConvertTo-InterfaceRow', 'Export-NetLDInterfaceData',
    'Get-NetLDInventoryDevices', 'Invoke-ExportDeviceInterfaces'
)
