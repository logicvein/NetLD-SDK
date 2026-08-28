Set-StrictMode -Version Latest

class AdvancedExampleError : System.Exception {
    AdvancedExampleError([string]$message) : base($message) {}
}

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

function ConvertTo-EnvironmentBoolean {
    param([AllowNull()][string]$Value, [bool]$Default = $false)
    if ($null -eq $Value -or -not $Value.Trim()) { return $Default }
    return $Value.Trim().ToLowerInvariant() -in @('1', 'true', 'yes', 'on')
}

function ConvertTo-SafeFilename {
    param([Parameter(Mandatory)][string]$Value)
    $cleaned = ($Value.Trim() -replace '[^A-Za-z0-9._-]+', '_').Trim('.', '_')
    return $(if ($cleaned) { $cleaned } else { 'device' })
}

function New-CommandRunnerJob {
    param(
        [Parameter(Mandatory)][string]$Network,
        [Parameter(Mandatory)][string]$Target,
        [Parameter(Mandatory)][string[]]$Commands,
        [bool]$Backup = $false
    )
    if ($Commands.Count -eq 0) { throw [AdvancedExampleError]::new('The command file contains no commands.') }
    return [ordered]@{
        jobName = "API Commands - $Target"
        managedNetworks = @($Network)
        jobType = 'Script Tool Job'
        description = 'Ad hoc command execution from the NetLD SDK advanced example'
        jobParameters = [ordered]@{
            tool = 'org.ziptie.tools.scripts.commandRunner'
            managedNetwork = $Network
            ipResolutionScheme = 'ipCsv'
            ipResolutionData = "`"$Target@$Network`""
            backupOnCompletion = $Backup.ToString().ToLowerInvariant()
            'input.commandList' = $Commands -join "`n"
        }
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
    catch {
        throw [AdvancedExampleError]::new("Could not authenticate to $BaseUrl.")
    }
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
    catch {
        throw [AdvancedExampleError]::new("netLD API call $Method failed.")
    }
    $data = $response.Content | ConvertFrom-Json
    $errorProperty = $data.PSObject.Properties['error']
    if ($errorProperty -and $errorProperty.Value) {
        throw [AdvancedExampleError]::new("netLD API call $Method failed: $($errorProperty.Value | ConvertTo-Json -Compress -Depth 20)")
    }
    $resultProperty = $data.PSObject.Properties['result']
    if (-not $resultProperty) { throw [AdvancedExampleError]::new("netLD API call $Method returned no result field.") }
    return $resultProperty.Value
}

function Wait-NetLDExecution {
    param(
        [hashtable]$Connection,
        [object]$Execution,
        [double]$PollSeconds,
        [double]$TimeoutSeconds
    )
    $deadline = [datetime]::UtcNow.AddSeconds($TimeoutSeconds)
    $current = $Execution
    while ($null -eq $current.endTime) {
        if ([datetime]::UtcNow -ge $deadline) {
            throw [AdvancedExampleError]::new("Execution $($Execution.id) did not finish within $TimeoutSeconds seconds.")
        }
        Start-Sleep -Milliseconds ([math]::Max(1, [int]($PollSeconds * 1000)))
        $current = Invoke-NetLDCall -Connection $Connection `
            -Method 'Scheduler.getExecutionDataById' -Parameters @{ executionId = $Execution.id }
        if (-not $current) { throw [AdvancedExampleError]::new("Scheduler returned no data for execution $($Execution.id).") }
    }
    return $current
}

function Export-NetLDExecutionDetails {
    param([hashtable]$Connection, [object]$Execution, [string]$OutputDirectory)
    $details = @(Invoke-NetLDCall -Connection $Connection `
        -Method 'Plugins.getExecutionDetails' -Parameters @{ executionId = $Execution.id })
    if ($details.Count -eq 0) { throw [AdvancedExampleError]::new("No device output was returned for execution $($Execution.id).") }
    [void](New-Item -ItemType Directory -Path $OutputDirectory -Force)
    $paths = @()
    foreach ($detail in $details) {
        $milliseconds = if ($detail.startTime) { [long]$detail.startTime } else { [long]$Execution.startTime }
        $timestamp = [DateTimeOffset]::FromUnixTimeMilliseconds($milliseconds).UtcDateTime.ToString('yyyyMMddTHHmmssZ')
        $identity = ConvertTo-SafeFilename "$($detail.managedNetwork)_$($detail.ipAddress)"
        $path = Join-Path $OutputDirectory "${timestamp}_$($Execution.id)_$($detail.id)_${identity}.log"
        $uri = "$($Connection.BaseUrl.TrimEnd('/'))/servlet/pluginDetail?executionId=$($Execution.id)&recordId=$($detail.id)"
        try {
            $response = Invoke-WebRequest -Uri $uri -Headers @{ Authorization = "Bearer $($Connection.ApiKey)" } `
                -WebSession $Connection.Session -MaximumRedirection 0 `
                -TimeoutSec $Connection.TimeoutSec -ErrorAction Stop
        }
        catch { throw [AdvancedExampleError]::new("Could not download output record $($detail.id).") }
        Set-Content -LiteralPath $path -Value $response.Content -Encoding UTF8 -NoNewline
        $paths += $path
    }
    return $paths
}

function Invoke-RunCmdAndExportLog {
    param([Parameter(Mandatory)][string]$EnvPath)
    Import-DotEnv $EnvPath
    $baseUrl = Get-RequiredEnvironmentValue 'NETLD_BASE_URL'
    $apiKey = Get-RequiredEnvironmentValue 'NETLD_API_KEY'
    $target = Get-RequiredEnvironmentValue 'NETLD_TARGET'
    $network = if ($env:NETLD_NETWORK) { $env:NETLD_NETWORK } else { 'Default' }
    $commandFile = if ($env:NETLD_COMMAND_FILE) { $env:NETLD_COMMAND_FILE } else { 'commands.txt' }
    $outputDirectory = if ($env:NETLD_OUTPUT_DIR) { $env:NETLD_OUTPUT_DIR } else { 'output' }
    $baseDirectory = Split-Path -Parent $EnvPath
    if (-not [IO.Path]::IsPathRooted($commandFile)) { $commandFile = Join-Path $baseDirectory $commandFile }
    if (-not [IO.Path]::IsPathRooted($outputDirectory)) { $outputDirectory = Join-Path $baseDirectory $outputDirectory }
    if (-not (Test-Path -LiteralPath $commandFile)) { throw [AdvancedExampleError]::new("Could not read the command file: $commandFile") }
    $commands = @(Get-Content -LiteralPath $commandFile | ForEach-Object { $_.Trim() } | Where-Object { $_ })
    $job = New-CommandRunnerJob -Network $network -Target $target -Commands $commands `
        -Backup:(ConvertTo-EnvironmentBoolean $env:NETLD_BACKUP_ON_COMPLETION)
    $job | ConvertTo-Json -Depth 20
    if (-not (ConvertTo-EnvironmentBoolean $env:NETLD_RUN_JOB)) {
        Write-Host 'Dry run only. Set NETLD_RUN_JOB=true after reviewing this job.'
        return
    }

    $timeout = if ($env:REQUEST_TIMEOUT_SECONDS) { [int]$env:REQUEST_TIMEOUT_SECONDS } else { 30 }
    $connection = @{
        BaseUrl = $baseUrl; ApiKey = $apiKey; TimeoutSec = $timeout
        Session = New-NetLDSession -BaseUrl $baseUrl -ApiKey $apiKey -TimeoutSec $timeout
    }
    $execution = Invoke-NetLDCall -Connection $connection -Method 'Scheduler.runNow' -Parameters @{ jobData = $job }
    $final = Wait-NetLDExecution -Connection $connection -Execution $execution `
        -PollSeconds $(if ($env:NETLD_POLL_SECONDS) { [double]$env:NETLD_POLL_SECONDS } else { 2 }) `
        -TimeoutSeconds $(if ($env:NETLD_WAIT_TIMEOUT_SECONDS) { [double]$env:NETLD_WAIT_TIMEOUT_SECONDS } else { 300 })
    $final | ConvertTo-Json -Depth 20
    Export-NetLDExecutionDetails -Connection $connection -Execution $final -OutputDirectory $outputDirectory |
        ForEach-Object { Write-Host "Wrote $_" }
    if ($final.status -and $final.status -ne 'OK') {
        throw [AdvancedExampleError]::new("Execution completed with status $($final.status).")
    }
}

Export-ModuleMember -Function @('ConvertTo-SafeFilename', 'Invoke-RunCmdAndExportLog', 'New-CommandRunnerJob')
