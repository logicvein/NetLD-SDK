Set-StrictMode -Version Latest

class AdvancedExampleError : System.Exception {
    AdvancedExampleError([string]$message) : base($message) {}
}

$script:CsvFields = @(
    'network', 'ipAddress', 'hostname', 'adapterId', 'deviceType',
    'hardwareVendor', 'model', 'serialNumber', 'softwareVendor', 'osVersion',
    'backupStatus', 'complianceState', 'lastBackup', 'lastTelemetry', 'memoSummary',
    'custom1', 'custom2', 'custom3', 'custom4', 'custom5'
)

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
    if (-not $value) { throw [AdvancedExampleError]::new("Set $Name in .env before running this example.") }
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
    param(
        [Parameter(Mandatory)][hashtable]$Connection,
        [Parameter(Mandatory)][string]$Method,
        [Parameter(Mandatory)][object]$Parameters
    )
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
    param(
        [Parameter(Mandatory)][scriptblock]$FetchPage,
        [Parameter(Mandatory)][int]$PageSize
    )
    if ($PageSize -le 0) { throw [AdvancedExampleError]::new('NETLD_PAGE_SIZE must be a positive integer.') }
    $offset = 0
    $total = $null
    while ($true) {
        $page = & $FetchPage $offset $PageSize
        if (-not $page) { throw [AdvancedExampleError]::new('Inventory.search returned no page data.') }
        $devices = @($page.devices)
        foreach ($device in $devices) { Write-Output $device }
        $pageSizeProperty = $page.PSObject.Properties['pageSize']
        $returnedPageSize = if ($pageSizeProperty -and $pageSizeProperty.Value) {
            [int]$pageSizeProperty.Value
        } else { $PageSize }
        if ($returnedPageSize -le 0) {
            throw [AdvancedExampleError]::new('Inventory.search returned an invalid page size.')
        }
        $totalProperty = $page.PSObject.Properties['total']
        if ($null -eq $total -and $totalProperty -and $null -ne $totalProperty.Value) {
            $total = [int]$totalProperty.Value
        }
        if ($null -ne $total -and $offset + $devices.Count -ge $total) { break }
        if ($null -eq $total -and $devices.Count -lt $returnedPageSize) { break }
        if ($devices.Count -eq 0) {
            throw [AdvancedExampleError]::new('Inventory.search returned an empty page before the reported total.')
        }
        $offset += $returnedPageSize
    }
}

function Export-NetLDInventoryCsv {
    param(
        [Parameter(Mandatory)][AllowEmptyCollection()][object[]]$Devices,
        [Parameter(Mandatory)][string]$OutputPath
    )
    $directory = Split-Path -Parent $OutputPath
    if (-not $directory) { $directory = '.' }
    [void](New-Item -ItemType Directory -Path $directory -Force)
    $temporaryPath = Join-Path $directory ".$([IO.Path]::GetFileName($OutputPath)).$([guid]::NewGuid()).tmp"
    try {
        if ($Devices.Count -gt 0) {
            $Devices | Select-Object -Property $script:CsvFields |
                Export-Csv -LiteralPath $temporaryPath -NoTypeInformation -Encoding utf8
        }
        else {
            $empty = [ordered]@{}
            foreach ($field in $script:CsvFields) { $empty[$field] = $null }
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

function Export-NetLDInventoryJson {
    param(
        [Parameter(Mandatory)][AllowEmptyCollection()][object[]]$Devices,
        [Parameter(Mandatory)][string]$OutputPath
    )
    $directory = Split-Path -Parent $OutputPath
    if (-not $directory) { $directory = '.' }
    [void](New-Item -ItemType Directory -Path $directory -Force)
    $temporaryPath = Join-Path $directory ".$([IO.Path]::GetFileName($OutputPath)).$([guid]::NewGuid()).tmp"
    try {
        $records = @($Devices | Select-Object -Property $script:CsvFields)
        $json = ConvertTo-Json -InputObject $records -Depth 20
        Set-Content -LiteralPath $temporaryPath -Value $json -Encoding utf8
        Move-Item -LiteralPath $temporaryPath -Destination $OutputPath -Force
    }
    catch {
        Remove-Item -LiteralPath $temporaryPath -Force -ErrorAction SilentlyContinue
        throw
    }
}

function Invoke-ExportDeviceInventory {
    param([Parameter(Mandatory)][string]$EnvPath, [string]$Format)
    Import-DotEnv $EnvPath
    $baseUrl = Get-RequiredEnvironmentValue 'NETLD_BASE_URL'
    $apiKey = Get-RequiredEnvironmentValue 'NETLD_API_KEY'
    $networks = ConvertTo-ManagedNetworkList $(if ($env:NETLD_NETWORKS) { $env:NETLD_NETWORKS } else { 'Default' })
    $pageSize = if ($env:NETLD_PAGE_SIZE) { [int]$env:NETLD_PAGE_SIZE } else { 500 }
    if ($pageSize -le 0) { throw [AdvancedExampleError]::new('NETLD_PAGE_SIZE must be a positive integer.') }
    $scheme = if ($env:NETLD_SEARCH_SCHEME) { $env:NETLD_SEARCH_SCHEME } else { 'ipAddress' }
    $query = if ($null -ne $env:NETLD_SEARCH_QUERY) { $env:NETLD_SEARCH_QUERY } else { '' }
    if (-not $query.EndsWith("`n")) { $query = "$query`n" }
    $outputFormat = $(if ($Format) { $Format } elseif ($env:NETLD_OUTPUT_FORMAT) { $env:NETLD_OUTPUT_FORMAT } else { 'csv' }).ToLowerInvariant()
    if ($outputFormat -notin @('csv', 'json')) {
        throw [AdvancedExampleError]::new('NETLD_OUTPUT_FORMAT must be either csv or json.')
    }
    $outputPath = if ($env:NETLD_OUTPUT_FILE) { $env:NETLD_OUTPUT_FILE } else { "inventory.$outputFormat" }
    if (-not [IO.Path]::IsPathRooted($outputPath)) {
        $outputPath = Join-Path $PSScriptRoot $outputPath
    }
    $timeout = if ($env:REQUEST_TIMEOUT_SECONDS) { [int]$env:REQUEST_TIMEOUT_SECONDS } else { 30 }
    $connection = @{
        BaseUrl = $baseUrl; ApiKey = $apiKey; TimeoutSec = $timeout
        Session = New-NetLDSession -BaseUrl $baseUrl -ApiKey $apiKey -TimeoutSec $timeout
    }
    $fetchPage = {
        param($offset, $requestedPageSize)
        Invoke-NetLDCall -Connection $connection -Method 'Inventory.search' -Parameters @{
            network = $networks
            scheme = $scheme
            query = $query
            pageData = @{ offset = $offset; pageSize = $requestedPageSize }
            sortColumn = 'ipAddress'
            descending = $false
        }
    }
    $devices = @(Get-NetLDInventoryDevices -FetchPage $fetchPage -PageSize $pageSize)
    if ($outputFormat -eq 'json') {
        Export-NetLDInventoryJson -Devices $devices -OutputPath $outputPath
    }
    else {
        Export-NetLDInventoryCsv -Devices $devices -OutputPath $outputPath
    }
    Write-Host "Wrote $($devices.Count) devices to $outputPath"
}

Export-ModuleMember -Function @(
    'ConvertTo-ManagedNetworkList', 'Export-NetLDInventoryCsv', 'Export-NetLDInventoryJson',
    'Get-NetLDInventoryDevices', 'Invoke-ExportDeviceInventory'
)
