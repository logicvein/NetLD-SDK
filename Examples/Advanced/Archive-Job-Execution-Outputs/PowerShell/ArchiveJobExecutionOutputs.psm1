Set-StrictMode -Version Latest

$script:StateFormat = 'logicvein-netld-job-execution-output-state'
$script:RunFormat = 'logicvein-netld-job-execution-output-run'

function Get-Value($Object, [string]$Name, $Default = $null) {
    if ($Object -is [Collections.IDictionary]) {
        if ($Object.Contains($Name)) { return $Object[$Name] }
    }
    elseif ($null -ne $Object -and $Object.PSObject.Properties[$Name]) {
        return $Object.$Name
    }
    return $Default
}

function Get-SafeName([string]$Value, [string]$Fallback) {
    $clean = ($Value.Trim() -replace '[^A-Za-z0-9._-]+', '_').Trim(' ', '.', '_')
    if ($clean) { return $clean }
    return $Fallback
}

function Write-AtomicBytes([string]$Path, [byte[]]$Bytes) {
    $directory = Split-Path -Parent $Path
    [IO.Directory]::CreateDirectory($directory) | Out-Null
    $temporary = Join-Path $directory ".$([IO.Path]::GetFileName($Path)).$([guid]::NewGuid()).tmp"
    try {
        [IO.File]::WriteAllBytes($temporary, $Bytes)
        [IO.File]::Move($temporary, $Path, $true)
    }
    finally {
        if (Test-Path $temporary) { Remove-Item $temporary -Force }
    }
}

function Write-AtomicJson([string]$Path, $Value) {
    $json = ($Value | ConvertTo-Json -Depth 30) + [Environment]::NewLine
    Write-AtomicBytes $Path ([Text.UTF8Encoding]::new($false).GetBytes($json))
}

function Get-ExecutionArchiveState([string]$Path) {
    if (-not (Test-Path $Path)) {
        return [ordered]@{ format = $script:StateFormat; formatVersion = 1 }
    }
    $state = Get-Content $Path -Raw | ConvertFrom-Json -AsHashtable
    if ($state.format -ne $script:StateFormat -or $state.formatVersion -ne 1) {
        throw 'The job-execution state file has an unsupported format.'
    }
    return $state
}

function Get-ExecutionId($Execution) {
    $value = Get-Value $Execution 'id' (Get-Value $Execution 'executionId')
    if ($null -eq $value) {
        throw 'Scheduler.searchExecutions returned a record without an execution ID.'
    }
    return [long]$value
}

function Get-ExecutionEnd($Execution) {
    $value = Get-Value $Execution 'endTime'
    if ($null -eq $value) { return $null }
    return [long]$value
}

function Test-EligibleExecution($Config, $Execution) {
    $typeMatch = -not $Config.JobType -or (Get-Value $Execution 'jobType') -eq $Config.JobType
    $nameMatch = -not $Config.JobName -or (Get-Value $Execution 'jobName') -eq $Config.JobName
    return $typeMatch -and $nameMatch
}

function Get-NewExecutions($Config, $State, [scriptblock]$SearchPage) {
    $hasWatermark = $State.Contains('lastEndTime')
    $watermark = if ($hasWatermark) { [long]$State.lastEndTime } else { $null }
    $watermarkIds = @{}
    foreach ($id in @(Get-Value $State 'executionIdsAtLastEndTime' @())) {
        $watermarkIds[[long]$id] = $true
    }
    $observed = [Collections.Generic.List[object]]::new()
    $offset = 0
    $reportedTotal = $null

    while ($null -eq $reportedTotal -or $offset -lt $reportedTotal) {
        $page = & $SearchPage $offset $Config.PageSize
        $batch = @(Get-Value $page 'executionData' @())
        $pageOffset = [int](Get-Value $page 'offset' $offset)
        $pageTotal = [int](Get-Value $page 'total' ($pageOffset + $batch.Count))
        if ($null -eq $reportedTotal -or $pageTotal -gt $reportedTotal) {
            $reportedTotal = $pageTotal
        }
        $passedWatermark = $false
        foreach ($execution in $batch) {
            $endTime = Get-ExecutionEnd $execution
            if ($null -eq $endTime) { continue }
            if ($hasWatermark -and $endTime -lt $watermark) {
                $passedWatermark = $true
                break
            }
            $observed.Add($execution)
        }
        if ($passedWatermark -or (-not $hasWatermark -and $Config.InitialMode -eq 'latest')) { break }
        $nextOffset = $pageOffset + $batch.Count
        if ($nextOffset -ge $reportedTotal) { break }
        if (-not $batch.Count -or $nextOffset -le $offset) {
            throw 'Execution paging stopped before all results were returned.'
        }
        $offset = $nextOffset
    }

    $candidates = @()
    if ($hasWatermark -or $Config.InitialMode -eq 'all') {
        $candidates = @($observed | Where-Object {
            $endTime = Get-ExecutionEnd $_
            $isNew = $null -ne $endTime -and (
                -not $hasWatermark -or
                $endTime -gt $watermark -or
                ($endTime -eq $watermark -and -not $watermarkIds.ContainsKey((Get-ExecutionId $_)))
            )
            $isNew -and (Test-EligibleExecution $Config $_)
        } | Sort-Object @{ Expression = { Get-ExecutionEnd $_ } }, @{ Expression = { Get-ExecutionId $_ } })
    }
    return [pscustomobject]@{ Observed = @($observed); Candidates = @($candidates) }
}

function Save-JobExecution($Config, $Execution, [scriptblock]$GetDetails, [scriptblock]$DownloadDetail) {
    $executionId = Get-ExecutionId $Execution
    $endTime = Get-ExecutionEnd $Execution
    if ($null -eq $endTime) { throw "Execution $executionId has not completed." }
    $date = [DateTimeOffset]::FromUnixTimeMilliseconds($endTime).UtcDateTime.ToString('yyyy-MM-dd')
    $jobName = Get-SafeName ([string](Get-Value $Execution 'jobName' 'job')) 'job'
    $directory = Join-Path $Config.OutputDir (Join-Path $date "${executionId}_$jobName")
    $details = @(& $GetDetails $executionId)
    $outputs = [Collections.Generic.List[object]]::new()

    foreach ($detail in $details) {
        $detailId = [long](Get-Value $detail 'id')
        $identity = Get-SafeName "$([string](Get-Value $detail 'managedNetwork' 'network'))_$([string](Get-Value $detail 'ipAddress' 'device'))" 'device'
        $contentPath = Join-Path $directory "${detailId}_${identity}.log"
        $metadataPath = Join-Path $directory "${detailId}_${identity}.metadata.json"
        [byte[]]$content = & $DownloadDetail $executionId $detailId
        Write-AtomicBytes $contentPath $content
        Write-AtomicJson $metadataPath ([ordered]@{
            executionId = $executionId
            detail = $detail
            contentFile = [IO.Path]::GetFileName($contentPath)
        })
        $outputs.Add([ordered]@{
            detailId = $detailId
            bytes = $content.Length
            contentFile = [IO.Path]::GetRelativePath($Config.OutputDir, $contentPath)
            metadataFile = [IO.Path]::GetRelativePath($Config.OutputDir, $metadataPath)
        })
    }
    $executionPath = Join-Path $directory 'execution.metadata.json'
    Write-AtomicJson $executionPath ([ordered]@{ execution = $Execution; outputCount = $outputs.Count })
    return [ordered]@{
        executionId = $executionId
        endTime = $endTime
        jobName = Get-Value $Execution 'jobName'
        outputCount = $outputs.Count
        metadataFile = [IO.Path]::GetRelativePath($Config.OutputDir, $executionPath)
        outputs = @($outputs)
    }
}

function Update-ExecutionArchiveState($State, $Observed) {
    $completed = @($Observed | Where-Object { $null -ne (Get-ExecutionEnd $_) })
    if (-not $completed.Count) { return }
    $newest = [long](($completed | ForEach-Object { Get-ExecutionEnd $_ } | Measure-Object -Maximum).Maximum)
    $ids = @($completed | Where-Object { (Get-ExecutionEnd $_) -eq $newest } | ForEach-Object { Get-ExecutionId $_ })
    if ($State.Contains('lastEndTime') -and [long]$State.lastEndTime -eq $newest) {
        $ids += @(Get-Value $State 'executionIdsAtLastEndTime' @())
    }
    $State.lastEndTime = $newest
    $State.executionIdsAtLastEndTime = @($ids | Sort-Object -Unique)
}

function Export-JobExecutionOutputData(
    $Config,
    [scriptblock]$SearchPage,
    [scriptblock]$GetDetails,
    [scriptblock]$DownloadDetail,
    [string]$GeneratedAt
) {
    $state = Get-ExecutionArchiveState $Config.StatePath
    $initialBaseline = -not $state.Contains('lastEndTime') -and $Config.InitialMode -eq 'latest'
    $selection = Get-NewExecutions $Config $state $SearchPage
    $archived = [Collections.Generic.List[object]]::new()
    $failures = [Collections.Generic.List[object]]::new()
    foreach ($execution in $selection.Candidates) {
        try {
            $archived.Add((Save-JobExecution $Config $execution $GetDetails $DownloadDetail))
        }
        catch {
            $failures.Add([ordered]@{
                executionId = Get-Value $execution 'id'
                error = $_.Exception.Message
            })
        }
    }
    if (-not $failures.Count) { Update-ExecutionArchiveState $state $selection.Observed }
    if (-not $GeneratedAt) { $GeneratedAt = [DateTime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ssZ') }
    $outputCount = 0
    foreach ($item in $archived) {
        $outputCount += [int](Get-Value $item 'outputCount' 0)
    }
    $report = [ordered]@{
        format = $script:RunFormat
        formatVersion = 1
        generatedAt = $GeneratedAt
        initialBaseline = $initialBaseline
        observedCount = $selection.Observed.Count
        candidateCount = $selection.Candidates.Count
        archivedCount = $archived.Count
        outputCount = [int]$outputCount
        failureCount = $failures.Count
        archived = @($archived)
        failures = @($failures)
    }
    Write-AtomicJson $Config.StatePath $state
    Write-AtomicJson $Config.ReportPath $report
    return $report
}

function Invoke-NetLDRpc($Connection, [string]$Method, $Parameters) {
    $body = @{ jsonrpc = '2.0'; method = $Method; params = $Parameters; id = [guid]::NewGuid().ToString() } |
        ConvertTo-Json -Depth 20
    $response = Invoke-WebRequest `
        -Uri "$($Connection.BaseUrl)/rest" `
        -Method Post `
        -Headers @{ Authorization = "Bearer $($Connection.ApiKey)"; 'Content-Type' = 'application/json' } `
        -Body $body `
        -WebSession $Connection.Session `
        -MaximumRedirection 0 `
        -TimeoutSec 30
    $data = $response.Content | ConvertFrom-Json
    if ($data.PSObject.Properties['error'] -and $data.error) {
        throw "$Method failed: $($data.error | ConvertTo-Json -Compress -Depth 10)"
    }
    return $data.result
}

function Invoke-ArchiveJobExecutionOutputs($Config) {
    $session = New-Object Microsoft.PowerShell.Commands.WebRequestSession
    Invoke-WebRequest `
        -Uri "$($Config.BaseUrl)/rest" `
        -Headers @{ Authorization = "Bearer $($Config.ApiKey)" } `
        -WebSession $session `
        -MaximumRedirection 0 `
        -TimeoutSec 30 | Out-Null
    $connection = @{ BaseUrl = $Config.BaseUrl; ApiKey = $Config.ApiKey; Session = $session }
    $search = {
        param($offset, $pageSize)
        Invoke-NetLDRpc $connection 'Scheduler.searchExecutions' @{
            scheme = $Config.SearchScheme
            data = $Config.SearchData
            pageData = @{ offset = $offset; executionData = @(); pageSize = $pageSize; total = 0 }
            sortColumn = 'endTime'
            descending = $true
        }
    }
    $details = { param($executionId) @(Invoke-NetLDRpc $connection 'Plugins.getExecutionDetails' @{ executionId = $executionId }) }
    $download = {
        param($executionId, $recordId)
        $query = "executionId=$([uri]::EscapeDataString($executionId))&recordId=$([uri]::EscapeDataString($recordId))"
        $response = Invoke-WebRequest `
            -Uri "$($Config.BaseUrl)/servlet/pluginDetail?$query" `
            -Headers @{ Authorization = "Bearer $($Config.ApiKey)" } `
            -WebSession $session `
            -MaximumRedirection 0 `
            -TimeoutSec 30
        return ,([byte[]]$response.RawContentStream.ToArray())
    }
    return Export-JobExecutionOutputData $Config $search $details $download
}

Export-ModuleMember -Function Export-JobExecutionOutputData,Get-NewExecutions,Invoke-ArchiveJobExecutionOutputs
