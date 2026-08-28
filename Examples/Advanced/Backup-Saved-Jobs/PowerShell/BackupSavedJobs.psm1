Set-StrictMode -Version Latest

class AdvancedExampleError : System.Exception {
    AdvancedExampleError([string]$message) : base($message) {}
}

$script:FormatName = 'logicvein-netld-saved-job-backup'
$script:FailureFormatName = 'logicvein-netld-saved-job-backup-failures'
$script:FormatVersion = 1

function Import-DotEnv {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) { return }
    Get-Content -LiteralPath $Path | ForEach-Object {
        $line = $_.Trim()
        if (-not $line -or $line.StartsWith('#') -or -not $line.Contains('=')) { return }
        $name, $value = $line.Split('=', 2)
        [Environment]::SetEnvironmentVariable($name.Trim(), $value.Trim().Trim('"').Trim("'"), 'Process')
    }
}

function Get-RequiredEnvironmentValue {
    param([string]$Name)
    $value = [Environment]::GetEnvironmentVariable($Name, 'Process')
    if (-not $value) { throw [AdvancedExampleError]::new("Set $Name in the environment file.") }
    return $value
}

function ConvertTo-ManagedNetworkList {
    param([string]$Value)
    $networks = @($Value.Split(',') | ForEach-Object { $_.Trim() } | Where-Object { $_ } | Sort-Object -Unique)
    if ($networks.Count -eq 0) { throw [AdvancedExampleError]::new('NETLD_NETWORKS must contain at least one managed network.') }
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

function Get-CompleteSavedJobs {
    param([scriptblock]$FetchPage, [scriptblock]$FetchJob, [int]$PageSize)
    if ($PageSize -le 0) { throw [AdvancedExampleError]::new('NETLD_JOB_PAGE_SIZE must be a positive integer.') }
    $jobsById = @{}
    $failuresById = @{}
    $offset = 0
    $total = $null
    while ($true) {
        $page = & $FetchPage $offset $PageSize
        if (-not $page) { throw [AdvancedExampleError]::new('Scheduler.searchJobs returned no page data.') }
        $shallowJobs = @($page.jobData)
        foreach ($shallow in $shallowJobs) {
            $jobIdProperty = $shallow.PSObject.Properties['jobId']
            if (-not $jobIdProperty -or $jobIdProperty.Value -isnot [int] -and $jobIdProperty.Value -isnot [long]) {
                throw [AdvancedExampleError]::new('Scheduler.searchJobs returned a job without an integer jobId.')
            }
            $jobId = [int]$jobIdProperty.Value
            $key = [string]$jobId
            if ($jobsById.ContainsKey($key) -or $failuresById.ContainsKey($key)) { continue }
            try {
                $full = & $FetchJob $jobId
                if (-not $full) { throw [AdvancedExampleError]::new("Scheduler.getJob returned no data for job ID $jobId.") }
                $jobsById[$key] = $full
            }
            catch {
                $failuresById[$key] = [pscustomobject][ordered]@{
                    jobId = $jobId
                    jobName = $shallow.PSObject.Properties['jobName'].Value
                    error = $_.Exception.Message
                }
            }
        }
        $pageSizeProperty = $page.PSObject.Properties['pageSize']
        $returnedPageSize = if ($pageSizeProperty -and $pageSizeProperty.Value) { [int]$pageSizeProperty.Value } else { $PageSize }
        if ($returnedPageSize -le 0) { throw [AdvancedExampleError]::new('Scheduler.searchJobs returned an invalid page size.') }
        $totalProperty = $page.PSObject.Properties['total']
        if ($null -eq $total -and $totalProperty -and $null -ne $totalProperty.Value) { $total = [int]$totalProperty.Value }
        if ($null -ne $total -and $offset + $shallowJobs.Count -ge $total) { break }
        if ($null -eq $total -and $shallowJobs.Count -lt $returnedPageSize) { break }
        if ($shallowJobs.Count -eq 0) { throw [AdvancedExampleError]::new('Scheduler.searchJobs returned an empty page before the reported total.') }
        $offset += $returnedPageSize
    }
    $jobs = @($jobsById.Keys | Sort-Object { [int]$_ } | ForEach-Object { $jobsById[$_] })
    $failures = @($failuresById.Keys | Sort-Object { [int]$_ } | ForEach-Object { $failuresById[$_] })
    return [pscustomobject]@{ Jobs = $jobs; Failures = $failures }
}

function New-SavedJobDocuments {
    param([object[]]$Jobs, [object[]]$Failures, [string[]]$Networks, [string]$ExportedAt)
    if (-not $ExportedAt) { $ExportedAt = [datetime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ssZ') }
    return [pscustomobject]@{
        Backup = [ordered]@{
            format = $script:FormatName; formatVersion = $script:FormatVersion
            exportedAt = $ExportedAt; networks = @($Networks | Sort-Object)
            complete = $Failures.Count -eq 0; jobCount = $Jobs.Count; jobs = @($Jobs)
        }
        FailureReport = [ordered]@{
            format = $script:FailureFormatName; formatVersion = $script:FormatVersion
            exportedAt = $ExportedAt; failureCount = $Failures.Count; failures = @($Failures)
        }
    }
}

function Write-AtomicJson {
    param([string]$OutputPath, [object]$Document)
    $directory = Split-Path -Parent $OutputPath
    if (-not $directory) { $directory = '.' }
    [void](New-Item -ItemType Directory -Path $directory -Force)
    $temporaryPath = Join-Path $directory ".$([IO.Path]::GetFileName($OutputPath)).$([guid]::NewGuid()).tmp"
    try {
        $json = $Document | ConvertTo-Json -Depth 100
        Set-Content -LiteralPath $temporaryPath -Value $json -Encoding utf8
        Move-Item -LiteralPath $temporaryPath -Destination $OutputPath -Force
    }
    catch {
        Remove-Item -LiteralPath $temporaryPath -Force -ErrorAction SilentlyContinue
        throw
    }
}

function Backup-NetLDSavedJobs {
    param(
        [scriptblock]$FetchPage, [scriptblock]$FetchJob, [string[]]$Networks,
        [int]$PageSize, [string]$OutputPath, [string]$FailurePath, [string]$ExportedAt
    )
    $collected = Get-CompleteSavedJobs $FetchPage $FetchJob $PageSize
    $documents = New-SavedJobDocuments @($collected.Jobs) @($collected.Failures) $Networks $ExportedAt
    Write-AtomicJson $OutputPath $documents.Backup
    Write-AtomicJson $FailurePath $documents.FailureReport
    return [pscustomobject]@{ JobCount = $collected.Jobs.Count; FailureCount = $collected.Failures.Count }
}

function Invoke-BackupSavedJobs {
    param([string]$EnvPath)
    Import-DotEnv $EnvPath
    $baseUrl = Get-RequiredEnvironmentValue 'NETLD_BASE_URL'
    $apiKey = Get-RequiredEnvironmentValue 'NETLD_API_KEY'
    $networks = ConvertTo-ManagedNetworkList $(if ($env:NETLD_NETWORKS) { $env:NETLD_NETWORKS } else { 'Default' })
    $pageSize = if ($env:NETLD_JOB_PAGE_SIZE) { [int]$env:NETLD_JOB_PAGE_SIZE } else { 100 }
    $outputName = if ($env:NETLD_OUTPUT_FILE) { $env:NETLD_OUTPUT_FILE } else { 'saved-jobs.json' }
    $failureName = if ($env:NETLD_FAILURE_FILE) { $env:NETLD_FAILURE_FILE } else { 'saved-job-failures.json' }
    $outputPath = if ([IO.Path]::IsPathRooted($outputName)) { $outputName } else { Join-Path $PSScriptRoot $outputName }
    $failurePath = if ([IO.Path]::IsPathRooted($failureName)) { $failureName } else { Join-Path $PSScriptRoot $failureName }
    $timeout = if ($env:REQUEST_TIMEOUT_SECONDS) { [int]$env:REQUEST_TIMEOUT_SECONDS } else { 30 }
    $connection = @{
        BaseUrl = $baseUrl; ApiKey = $apiKey; TimeoutSec = $timeout
        Session = New-NetLDSession $baseUrl $apiKey $timeout
    }
    $fetchPage = {
        param($offset, $requestedPageSize)
        Invoke-NetLDCall $connection 'Scheduler.searchJobs' @{
            pageData = @{ offset = $offset; jobData = @(); pageSize = $requestedPageSize; total = 1 }
            networks = $networks; sortColumn = ''; descending = $false
        }
    }
    $fetchJob = { param($jobId) Invoke-NetLDCall $connection 'Scheduler.getJob' @{ jobId = $jobId } }
    $result = Backup-NetLDSavedJobs $fetchPage $fetchJob $networks $pageSize $outputPath $failurePath ''
    Write-Host "Wrote $($result.JobCount) complete saved jobs to $outputPath"
    Write-Host "Wrote $($result.FailureCount) retrieval failures to $failurePath"
    return $result
}

Export-ModuleMember -Function @('Backup-NetLDSavedJobs', 'Get-CompleteSavedJobs', 'Invoke-BackupSavedJobs', 'New-SavedJobDocuments')
