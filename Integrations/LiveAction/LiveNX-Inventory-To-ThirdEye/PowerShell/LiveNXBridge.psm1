Set-StrictMode -Version Latest

class LiveNXBridgeError : System.Exception {
    LiveNXBridgeError([string]$message) : base($message) {}
}

function Import-DotEnv {
    param([Parameter(Mandatory)][string]$Path)

    if (-not (Test-Path $Path)) {
        return
    }

    Get-Content $Path | ForEach-Object {
        $line = $_.Trim()
        if (-not $line -or $line.StartsWith("#") -or -not $line.Contains("=")) {
            return
        }

        $name, $value = $line.Split("=", 2)
        $value = $value.Trim().Trim('"').Trim("'")
        [Environment]::SetEnvironmentVariable($name.Trim(), $value, "Process")
    }
}

function Get-RequiredEnvironmentValue {
    param([Parameter(Mandatory)][string]$Name)

    $value = [Environment]::GetEnvironmentVariable($Name, "Process")
    if (-not $value) {
        throw [LiveNXBridgeError]::new("Set $Name in .env before running this integration.")
    }
    return $value
}

function ConvertTo-EnvironmentBoolean {
    param(
        [AllowNull()][string]$Value,
        [bool]$Default = $false
    )

    if ($null -eq $Value -or $Value.Trim() -eq "") {
        return $Default
    }
    return $Value.Trim().ToLowerInvariant() -in @("1", "true", "yes", "on")
}

function ConvertTo-NormalizedHeader {
    param([Parameter(Mandatory)][string]$Value)

    return ($Value.ToUpperInvariant() -replace '[^A-Z0-9]', '')
}

function ConvertTo-CanonicalIPAddress {
    param([Parameter(Mandatory)][string]$Value)

    $parsed = $null
    if (-not [System.Net.IPAddress]::TryParse($Value.Trim(), [ref]$parsed)) {
        return $null
    }
    return $parsed.ToString()
}

function Get-SortedIPAddress {
    param([Parameter(Mandatory)][string[]]$Address)

    return @($Address | Sort-Object `
        @{ Expression = { if ([System.Net.IPAddress]::Parse($_).AddressFamily -eq 'InterNetwork') { 4 } else { 6 } } }, `
        @{ Expression = { $_ } })
}

function ConvertFrom-LiveNXDeviceCsv {
    param(
        [Parameter(Mandatory)][string]$CsvText,
        [bool]$RequireVendor = $true
    )

    $rows = @($CsvText.TrimStart([char]0xFEFF) | ConvertFrom-Csv)
    if ($rows.Count -eq 0) {
        return @()
    }

    $fieldMap = @{}
    foreach ($name in $rows[0].PSObject.Properties.Name) {
        $fieldMap[(ConvertTo-NormalizedHeader -Value $name)] = $name
    }

    $ipField = $null
    foreach ($candidate in @("IPADDRESS", "MANAGEMENTIPADDRESS", "MANAGEMENTIP", "IP")) {
        if ($fieldMap.ContainsKey($candidate)) {
            $ipField = $fieldMap[$candidate]
            break
        }
    }
    if (-not $ipField) {
        $available = $rows[0].PSObject.Properties.Name -join ", "
        throw [LiveNXBridgeError]::new(
            "The LiveNX CSV does not contain a recognized IP-address column. Available columns: $available"
        )
    }

    $vendorField = if ($fieldMap.ContainsKey("VENDOR")) { $fieldMap["VENDOR"] } else { $null }
    if ($RequireVendor -and -not $vendorField) {
        throw [LiveNXBridgeError]::new(
            "LIVENX_REQUIRE_VENDOR=true, but the LiveNX CSV has no VENDOR column."
        )
    }

    $addresses = [System.Collections.Generic.HashSet[string]]::new()
    foreach ($row in $rows) {
        if ($RequireVendor -and -not ([string]$row.$vendorField).Trim()) {
            continue
        }

        $address = ConvertTo-CanonicalIPAddress -Value ([string]$row.$ipField)
        if ($address) {
            [void]$addresses.Add($address)
        }
    }

    return @(Get-SortedIPAddress -Address @($addresses))
}

function New-PreparedDiscoveryJob {
    param(
        [Parameter(Mandatory)][object]$JobData,
        [Parameter(Mandatory)][string]$Network,
        [Parameter(Mandatory)][string[]]$Address
    )

    $prepared = $JobData | ConvertTo-Json -Depth 50 | ConvertFrom-Json
    if (-not $prepared.jobParameters) {
        throw [LiveNXBridgeError]::new("The selected job has no jobParameters object.")
    }
    if (-not ($prepared.jobParameters.PSObject.Properties.Name -contains "includedAddresses")) {
        throw [LiveNXBridgeError]::new(
            "The selected job is not a compatible Discover Devices job: " +
            "jobParameters.includedAddresses is missing."
        )
    }

    if ($prepared.PSObject.Properties.Name -contains "managedNetwork") {
        $prepared.managedNetwork = $Network
    }
    if ($prepared.PSObject.Properties.Name -contains "managedNetworks") {
        $prepared.managedNetworks = if ($prepared.managedNetworks -is [array]) { @($Network) } else { $Network }
    }
    if ($prepared.jobParameters.PSObject.Properties.Name -contains "managedNetwork") {
        $prepared.jobParameters.managedNetwork = $Network
    }

    $prepared.jobParameters.includedAddresses = (Get-SortedIPAddress -Address $Address) -join ","
    return $prepared
}

function Invoke-LiveNXDeviceExport {
    param(
        [Parameter(Mandatory)][string]$BaseUrl,
        [Parameter(Mandatory)][string]$ApiToken,
        [Parameter(Mandatory)][string]$ExportPath,
        [int]$TimeoutSec = 30
    )

    $url = "$($BaseUrl.TrimEnd('/'))/$($ExportPath.TrimStart('/'))"
    try {
        $response = Invoke-WebRequest `
            -Uri $url `
            -Headers @{ Accept = "text/csv"; Authorization = "Bearer $ApiToken" } `
            -MaximumRedirection 0 `
            -TimeoutSec $TimeoutSec `
            -ErrorAction Stop
    }
    catch {
        if ($_.Exception.Response) {
            $statusCode = [int]$_.Exception.Response.StatusCode
            throw [LiveNXBridgeError]::new("LiveNX device export failed with HTTP $statusCode.")
        }
        throw [LiveNXBridgeError]::new("Could not retrieve the LiveNX device export from $url.")
    }

    return $response.Content
}

function New-NetLDSession {
    param(
        [Parameter(Mandatory)][string]$BaseUrl,
        [Parameter(Mandatory)][string]$ApiKey,
        [int]$TimeoutSec = 30
    )

    $webSession = $null
    try {
        [void](Invoke-WebRequest `
            -Uri "$($BaseUrl.TrimEnd('/'))/rest" `
            -Headers @{ Authorization = "Bearer $ApiKey" } `
            -SessionVariable webSession `
            -MaximumRedirection 0 `
            -TimeoutSec $TimeoutSec `
            -ErrorAction Stop)
    }
    catch {
        if ($_.Exception.Response) {
            $statusCode = [int]$_.Exception.Response.StatusCode
            throw [LiveNXBridgeError]::new("ThirdEye login failed with HTTP $statusCode.")
        }
        throw [LiveNXBridgeError]::new("Could not reach $BaseUrl.")
    }
    return $webSession
}

function Invoke-NetLDCall {
    param(
        [Parameter(Mandatory)][string]$BaseUrl,
        [Parameter(Mandatory)][string]$ApiKey,
        [Parameter(Mandatory)][Microsoft.PowerShell.Commands.WebRequestSession]$Session,
        [Parameter(Mandatory)][string]$Method,
        [Parameter(Mandatory)][hashtable]$Parameters,
        [int]$TimeoutSec = 30,
        [bool]$DebugMode = $false
    )

    $payload = @{
        jsonrpc = "2.0"
        method = $Method
        params = $Parameters
        id = [guid]::NewGuid().ToString()
    }
    $body = $payload | ConvertTo-Json -Depth 50
    if ($DebugMode) {
        Write-Host "ThirdEye request:"
        Write-Host $body
    }

    try {
        $response = Invoke-WebRequest `
            -Uri "$($BaseUrl.TrimEnd('/'))/rest" `
            -Method Post `
            -Headers @{ Authorization = "Bearer $ApiKey"; "Content-Type" = "application/json" } `
            -Body $body `
            -WebSession $Session `
            -MaximumRedirection 0 `
            -TimeoutSec $TimeoutSec `
            -ErrorAction Stop
    }
    catch {
        if ($_.Exception.Response) {
            $statusCode = [int]$_.Exception.Response.StatusCode
            throw [LiveNXBridgeError]::new("ThirdEye API call $Method failed with HTTP $statusCode.")
        }
        throw [LiveNXBridgeError]::new("ThirdEye API call $Method failed to connect.")
    }

    $data = $response.Content | ConvertFrom-Json
    if ($data.error) {
        throw [LiveNXBridgeError]::new(
            "ThirdEye API call $Method failed: $($data.error | ConvertTo-Json -Depth 20 -Compress)"
        )
    }
    return $data.result
}

function Get-NetLDInventoryAddress {
    param(
        [Parameter(Mandatory)][hashtable]$Connection,
        [Parameter(Mandatory)][string]$Network,
        [int]$PageSize = 500
    )

    $addresses = [System.Collections.Generic.HashSet[string]]::new()
    $offset = 0
    do {
        $page = Invoke-NetLDCall @Connection -Method "Inventory.search" -Parameters @{
            network = @($Network)
            scheme = "ipAddress"
            query = "`n"
            pageData = @{ offset = $offset; pageSize = $PageSize }
            sortColumn = "ipAddress"
            descending = $false
        }
        $devices = @($page.devices)
        foreach ($device in $devices) {
            $address = ConvertTo-CanonicalIPAddress -Value ([string]$device.ipAddress)
            if ($address) {
                [void]$addresses.Add($address)
            }
        }
        $offset += $devices.Count
        $total = if ($null -ne $page.total) { [int]$page.total } else { $offset }
    } while ($devices.Count -gt 0 -and $offset -lt $total)

    return @(Get-SortedIPAddress -Address @($addresses))
}

function Get-NetLDJobByName {
    param(
        [Parameter(Mandatory)][hashtable]$Connection,
        [Parameter(Mandatory)][string]$Network,
        [Parameter(Mandatory)][string]$JobName,
        [int]$PageSize = 100
    )

    $matches = @()
    $offset = 0
    do {
        $page = Invoke-NetLDCall @Connection -Method "Scheduler.searchJobs" -Parameters @{
            pageData = @{ offset = $offset; jobData = @(); pageSize = $PageSize; total = 1 }
            networks = @($Network)
            sortColumn = ""
            descending = $false
        }
        $jobs = @($page.jobData)
        $matches += @($jobs | Where-Object { $_.jobName -eq $JobName })
        $offset += $jobs.Count
        $total = if ($null -ne $page.total) { [int]$page.total } else { $offset }
    } while ($jobs.Count -gt 0 -and $offset -lt $total)

    if ($matches.Count -eq 0) {
        throw [LiveNXBridgeError]::new("No available job named `"$JobName`" was found.")
    }
    if ($matches.Count -gt 1) {
        $ids = ($matches | ForEach-Object { $_.jobId }) -join ", "
        throw [LiveNXBridgeError]::new("Multiple jobs named `"$JobName`" were found: $ids")
    }

    $jobData = Invoke-NetLDCall @Connection -Method "Scheduler.getJob" -Parameters @{
        jobId = $matches[0].jobId
    }
    if (-not $jobData) {
        throw [LiveNXBridgeError]::new(
            "Scheduler.getJob returned no data for job ID $($matches[0].jobId)."
        )
    }
    return $jobData
}

function Invoke-LiveNXBridge {
    param(
        [Parameter(Mandatory)][string]$EnvPath,
        [switch]$Apply
    )

    Import-DotEnv -Path $EnvPath
    $liveNXBaseUrl = Get-RequiredEnvironmentValue -Name "LIVENX_BASE_URL"
    $liveNXApiToken = Get-RequiredEnvironmentValue -Name "LIVENX_API_TOKEN"
    $netLDBaseUrl = Get-RequiredEnvironmentValue -Name "NETLD_BASE_URL"
    $netLDApiKey = Get-RequiredEnvironmentValue -Name "NETLD_API_KEY"
    $exportPath = if ($env:LIVENX_DEVICE_EXPORT_PATH) { $env:LIVENX_DEVICE_EXPORT_PATH } else { "/v1/devices/export/csv" }
    $network = if ($env:NETLD_NETWORK) { $env:NETLD_NETWORK } else { "Default" }
    $timeout = if ($env:REQUEST_TIMEOUT_SECONDS) { [int]$env:REQUEST_TIMEOUT_SECONDS } else { 30 }
    $requireVendor = ConvertTo-EnvironmentBoolean -Value $env:LIVENX_REQUIRE_VENDOR -Default $true
    $debugMode = ConvertTo-EnvironmentBoolean -Value $env:NETLD_DEBUG

    $csvText = Invoke-LiveNXDeviceExport `
        -BaseUrl $liveNXBaseUrl `
        -ApiToken $liveNXApiToken `
        -ExportPath $exportPath `
        -TimeoutSec $timeout
    $liveNXAddresses = @(ConvertFrom-LiveNXDeviceCsv -CsvText $csvText -RequireVendor $requireVendor)

    $session = New-NetLDSession -BaseUrl $netLDBaseUrl -ApiKey $netLDApiKey -TimeoutSec $timeout
    $connection = @{
        BaseUrl = $netLDBaseUrl
        ApiKey = $netLDApiKey
        Session = $session
        TimeoutSec = $timeout
        DebugMode = $debugMode
    }
    $managedAddresses = @(Get-NetLDInventoryAddress -Connection $connection -Network $network)
    $managedSet = [System.Collections.Generic.HashSet[string]]::new([string[]]$managedAddresses)
    $missingAddresses = @($liveNXAddresses | Where-Object { -not $managedSet.Contains($_) })

    Write-Host "LiveNX device addresses: $($liveNXAddresses.Count)"
    Write-Host "ThirdEye managed addresses: $($managedAddresses.Count)"
    Write-Host "Missing from ThirdEye: $($missingAddresses.Count)"
    Get-SortedIPAddress -Address $missingAddresses | ForEach-Object { Write-Host "  $_" }

    if ($missingAddresses.Count -eq 0) {
        Write-Host "No discovery is required."
        return
    }
    if (-not $Apply) {
        Write-Host "Dry run only. Re-run with -Apply to start discovery."
        return
    }
    if (-not $env:NETLD_DISCOVERY_JOB_NAME) {
        throw [LiveNXBridgeError]::new(
            "Set NETLD_DISCOVERY_JOB_NAME to an existing Discover Devices job before using -Apply."
        )
    }

    $jobData = Get-NetLDJobByName `
        -Connection $connection `
        -Network $network `
        -JobName $env:NETLD_DISCOVERY_JOB_NAME
    $preparedJob = New-PreparedDiscoveryJob `
        -JobData $jobData `
        -Network $network `
        -Address $missingAddresses
    $execution = Invoke-NetLDCall @connection -Method "Scheduler.runNow" -Parameters @{
        jobData = $preparedJob
    }
    Write-Host "Discovery started:"
    Write-Host ($execution | ConvertTo-Json -Depth 20)
}

Export-ModuleMember -Function @(
    "ConvertFrom-LiveNXDeviceCsv",
    "ConvertTo-CanonicalIPAddress",
    "Invoke-LiveNXBridge",
    "Get-SortedIPAddress",
    "New-PreparedDiscoveryJob"
)
