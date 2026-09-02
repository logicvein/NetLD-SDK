Set-StrictMode -Version Latest

class ConfigChangeProbeError : System.Exception {
    ConfigChangeProbeError([string]$message) : base($message) {}
}

function Import-DotEnv {
    param([Parameter(Mandatory)][string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) { return }
    Get-Content -LiteralPath $Path | ForEach-Object {
        $line = $_.Trim()
        if (-not $line -or $line.StartsWith('#') -or -not $line.Contains('=')) { return }
        $name, $value = $line.Split('=', 2)
        [Environment]::SetEnvironmentVariable(
            $name.Trim(), $value.Trim().Trim('"').Trim("'"), 'Process'
        )
    }
}

function Get-RequiredEnvironmentValue {
    param([Parameter(Mandatory)][string]$Name)

    $value = [Environment]::GetEnvironmentVariable($Name, 'Process')
    if (-not $value) {
        throw [ConfigChangeProbeError]::new("Set $Name in .env before running this integration.")
    }
    return $value
}

function ConvertTo-UtcString {
    param([Parameter(Mandatory)][datetime]$Value)
    return $Value.ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ss-00:00')
}

function ConvertFrom-EpochMilliseconds {
    param([Parameter(Mandatory)][long]$Value)
    return [DateTimeOffset]::FromUnixTimeMilliseconds($Value).UtcDateTime
}

function Read-ProbeState {
    param([Parameter(Mandatory)][string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        return [pscustomobject]@{ lastRun = ConvertTo-UtcString -Value ([datetime]::UtcNow) }
    }
    try {
        $state = Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json
        $parsed = [datetime]::Parse([string]$state.lastRun).ToUniversalTime()
        return [pscustomobject]@{ lastRun = ConvertTo-UtcString -Value $parsed }
    }
    catch {
        throw [ConfigChangeProbeError]::new("The probe state file is invalid: $Path")
    }
}

function Write-ProbeState {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string]$LastRun
    )

    $parent = Split-Path -Parent $Path
    if ($parent -and -not (Test-Path -LiteralPath $parent)) {
        [void](New-Item -ItemType Directory -Path $parent -Force)
    }
    $temporary = "$Path.$([guid]::NewGuid().ToString('N')).tmp"
    try {
        @{ lastRun = $LastRun } | ConvertTo-Json | Set-Content -LiteralPath $temporary -Encoding UTF8
        Move-Item -LiteralPath $temporary -Destination $Path -Force
    }
    finally {
        if (Test-Path -LiteralPath $temporary) { Remove-Item -LiteralPath $temporary -Force }
    }
}

function New-NetLDSession {
    param(
        [Parameter(Mandatory)][string]$BaseUrl,
        [Parameter(Mandatory)][string]$ApiKey,
        [int]$TimeoutSec = 30
    )

    $webSession = $null
    try {
        [void](Invoke-WebRequest -Uri "$($BaseUrl.TrimEnd('/'))/rest" `
            -Headers @{ Authorization = "Bearer $ApiKey" } -SessionVariable webSession `
            -MaximumRedirection 0 -TimeoutSec $TimeoutSec -ErrorAction Stop)
    }
    catch {
        $responseProperty = $_.Exception.PSObject.Properties['Response']
        if ($responseProperty -and $responseProperty.Value) {
            throw [ConfigChangeProbeError]::new("netLD login failed with HTTP $([int]$responseProperty.Value.StatusCode).")
        }
        throw [ConfigChangeProbeError]::new("Could not reach $BaseUrl.")
    }
    return $webSession
}

function Invoke-NetLDCall {
    param(
        [Parameter(Mandatory)][string]$BaseUrl,
        [Parameter(Mandatory)][string]$ApiKey,
        [Parameter(Mandatory)][Microsoft.PowerShell.Commands.WebRequestSession]$Session,
        [Parameter(Mandatory)][string]$Method,
        [Parameter(Mandatory)][object]$Parameters,
        [int]$TimeoutSec = 30
    )

    $body = @{ jsonrpc = '2.0'; method = $Method; params = $Parameters; id = [guid]::NewGuid().ToString() } |
        ConvertTo-Json -Depth 50
    try {
        $response = Invoke-WebRequest -Uri "$($BaseUrl.TrimEnd('/'))/rest" -Method Post `
            -Headers @{ Authorization = "Bearer $ApiKey"; 'Content-Type' = 'application/json' } `
            -Body $body -WebSession $Session -MaximumRedirection 0 `
            -TimeoutSec $TimeoutSec -ErrorAction Stop
    }
    catch {
        $responseProperty = $_.Exception.PSObject.Properties['Response']
        if ($responseProperty -and $responseProperty.Value) {
            throw [ConfigChangeProbeError]::new("netLD API call $Method failed with HTTP $([int]$responseProperty.Value.StatusCode).")
        }
        throw [ConfigChangeProbeError]::new("netLD API call $Method failed to connect.")
    }

    $data = $response.Content | ConvertFrom-Json
    $errorProperty = $data.PSObject.Properties['error']
    if ($errorProperty -and $errorProperty.Value) {
        throw [ConfigChangeProbeError]::new("netLD API call $Method failed: $($errorProperty.Value | ConvertTo-Json -Depth 20 -Compress)")
    }
    $resultProperty = $data.PSObject.Properties['result']
    if (-not $resultProperty) {
        throw [ConfigChangeProbeError]::new("netLD API call $Method returned no result field.")
    }
    return $resultProperty.Value
}

function Get-ChangeSummary {
    param(
        [AllowEmptyCollection()][object[]]$Changes = @(),
        [AllowEmptyCollection()][string[]]$Networks = @()
    )

    $allowed = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::Ordinal)
    foreach ($network in $Networks) { if ($network.Trim()) { [void]$allowed.Add($network.Trim()) } }
    $byNetwork = @{}
    $earliest = [long]::MaxValue
    $latest = [long]::MinValue

    foreach ($change in $Changes) {
        $network = [string]$change.managedNetwork
        $address = [string]$change.ipAddress
        if (-not $network -or -not $address -or ($allowed.Count -gt 0 -and -not $allowed.Contains($network))) {
            continue
        }
        $changed = [long]$change.lastChanged
        $earliest = [math]::Min($earliest, $changed)
        $latest = [math]::Max($latest, $changed)
        if (-not $byNetwork.ContainsKey($network)) {
            $byNetwork[$network] = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::Ordinal)
        }
        [void]$byNetwork[$network].Add($address)
    }

    $count = 0
    foreach ($network in $byNetwork.Keys) { $count += $byNetwork[$network].Count }
    return [pscustomobject]@{
        ByNetwork = $byNetwork
        DeviceCount = $count
        Earliest = if ($count -gt 0) { $earliest } else { $null }
        Latest = if ($count -gt 0) { $latest } else { $null }
    }
}

function Get-NetLDJobByName {
    param(
        [Parameter(Mandatory)][hashtable]$Connection,
        [Parameter(Mandatory)][string]$Network,
        [Parameter(Mandatory)][string]$JobName
    )

    $matches = @()
    $offset = 0
    do {
        $page = Invoke-NetLDCall @Connection -Method 'Scheduler.searchJobs' -Parameters @{
            pageData = @{ offset = $offset; jobData = @(); pageSize = 100; total = 1 }
            networks = @($Network); sortColumn = ''; descending = $false
        }
        $jobs = @($page.jobData)
        $matches += @($jobs | Where-Object { $_.jobName -eq $JobName })
        $offset += $jobs.Count
        $total = if ($null -ne $page.total) { [int]$page.total } else { $offset }
    } while ($jobs.Count -gt 0 -and $offset -lt $total)

    if ($matches.Count -ne 1) {
        throw [ConfigChangeProbeError]::new("Expected one available job named `"$JobName`"; found $($matches.Count).")
    }
    $job = Invoke-NetLDCall @Connection -Method 'Scheduler.getJob' -Parameters @{ jobId = $matches[0].jobId }
    if (-not $job) { throw [ConfigChangeProbeError]::new("Scheduler.getJob returned no data for job ID $($matches[0].jobId).") }
    return $job
}

function New-PreparedReportJob {
    param(
        [Parameter(Mandatory)][object]$JobData,
        [Parameter(Mandatory)][string]$Network,
        [Parameter(Mandatory)][string[]]$Addresses,
        [Parameter(Mandatory)][long]$Earliest,
        [Parameter(Mandatory)][long]$Latest
    )

    $prepared = $JobData | ConvertTo-Json -Depth 50 | ConvertFrom-Json
    if (-not $prepared.jobParameters) {
        throw [ConfigChangeProbeError]::new('The selected report job has no jobParameters object.')
    }
    foreach ($name in @('input.start_date', 'input.end_date', 'ipResolutionData')) {
        if (-not ($prepared.jobParameters.PSObject.Properties.Name -contains $name)) {
            throw [ConfigChangeProbeError]::new("The selected report job is missing jobParameters.$name.")
        }
    }
    if ($prepared.PSObject.Properties.Name -contains 'managedNetwork') { $prepared.managedNetwork = $Network }
    if ($prepared.jobParameters.PSObject.Properties.Name -contains 'managedNetwork') { $prepared.jobParameters.managedNetwork = $Network }
    $prepared.jobParameters.'input.start_date' = ConvertTo-UtcString -Value ((ConvertFrom-EpochMilliseconds $Earliest).AddSeconds(-1))
    $prepared.jobParameters.'input.end_date' = ConvertTo-UtcString -Value ((ConvertFrom-EpochMilliseconds $Latest).AddSeconds(1))
    $prepared.jobParameters.ipResolutionData = (@($Addresses | Sort-Object -Unique | ForEach-Object { "$_@$Network" })) -join ','
    return $prepared
}

function Invoke-ConfigChangeProbe {
    param([Parameter(Mandatory)][string]$EnvPath)

    Import-DotEnv -Path $EnvPath
    $baseUrl = Get-RequiredEnvironmentValue 'NETLD_BASE_URL'
    $apiKey = Get-RequiredEnvironmentValue 'NETLD_API_KEY'
    $timeout = if ($env:REQUEST_TIMEOUT_SECONDS) { [int]$env:REQUEST_TIMEOUT_SECONDS } else { 30 }
    $reportName = if ($env:NETLD_REPORT_JOB_NAME) { $env:NETLD_REPORT_JOB_NAME } else { 'PRTG Realtime Changes' }
    $reportNetwork = if ($env:NETLD_REPORT_JOB_NETWORK) { $env:NETLD_REPORT_JOB_NETWORK } else { 'Default' }
    $networks = if ($env:NETLD_NETWORKS) { @($env:NETLD_NETWORKS.Split(',') | ForEach-Object { $_.Trim() } | Where-Object { $_ }) } else { @() }
    $statePath = if ($env:PRTG_STATE_PATH) { $env:PRTG_STATE_PATH } else { 'config-change-probe-state.json' }
    if (-not [IO.Path]::IsPathRooted($statePath)) { $statePath = Join-Path (Split-Path -Parent $EnvPath) $statePath }

    $stateExists = Test-Path -LiteralPath $statePath
    $state = Read-ProbeState -Path $statePath
    if (-not $stateExists) { Write-ProbeState -Path $statePath -LastRun $state.lastRun }

    $session = New-NetLDSession -BaseUrl $baseUrl -ApiKey $apiKey -TimeoutSec $timeout
    $connection = @{ BaseUrl = $baseUrl; ApiKey = $apiKey; Session = $session; TimeoutSec = $timeout }
    $changes = @(Invoke-NetLDCall @connection -Method 'Configuration.retrieveConfigsSince' -Parameters @([string]$state.lastRun))
    $summary = Get-ChangeSummary -Changes $changes -Networks $networks
    if ($summary.DeviceCount -eq 0) { return $summary }

    $job = Get-NetLDJobByName -Connection $connection -Network $reportNetwork -JobName $reportName
    foreach ($network in @($summary.ByNetwork.Keys | Sort-Object)) {
        $prepared = New-PreparedReportJob -JobData $job -Network $network `
            -Addresses @($summary.ByNetwork[$network]) -Earliest $summary.Earliest -Latest $summary.Latest
        [void](Invoke-NetLDCall @connection -Method 'Scheduler.runNow' -Parameters @{ jobData = $prepared })
    }
    $lastRun = ConvertTo-UtcString -Value (ConvertFrom-EpochMilliseconds $summary.Latest)
    Write-ProbeState -Path $statePath -LastRun $lastRun
    return $summary
}

function ConvertTo-PrtgXmlResult {
    param([Parameter(Mandatory)][int]$DeviceCount)

    $word = if ($DeviceCount -eq 1) { 'device' } else { 'devices' }
    $message = if ($DeviceCount -gt 0) { "Configuration changes on $DeviceCount $word." } else { 'OK' }
    $notify = if ($DeviceCount -gt 0) { '<NotifyChanged />' } else { '' }
    return "<prtg><text>$message</text><result><channel>Configuration Changes</channel><value>$DeviceCount</value><unit>Count</unit>$notify</result></prtg>"
}

function ConvertTo-PrtgXmlError {
    param([Parameter(Mandatory)][string]$Message)
    $escaped = [System.Security.SecurityElement]::Escape($Message)
    return "<prtg><error>1</error><text>$escaped</text></prtg>"
}

Export-ModuleMember -Function @(
    'ConvertTo-PrtgXmlError', 'ConvertTo-PrtgXmlResult', 'Get-ChangeSummary',
    'Invoke-ConfigChangeProbe', 'New-PreparedReportJob', 'Read-ProbeState', 'Write-ProbeState'
)
