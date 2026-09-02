Set-StrictMode -Version Latest

$script:StateFormat = 'logicvein-thirdeye-violation-export-state'
$script:RunFormat = 'logicvein-thirdeye-violation-export-run'
$script:CsvFields = @(
    'eventId', 'incidentId', 'severity', 'clearState', 'eventType', 'network',
    'ipAddress', 'hostname', 'deviceId', 'hostUuid', 'measurement',
    'measurementIndex', 'message', 'occurrences', 'triggerId', 'created', 'updated'
)

function Get-Value($Object, [string]$Name, $Default = $null) {
    if ($Object -is [Collections.IDictionary]) {
        if ($Object.Contains($Name)) { return $Object[$Name] }
    }
    elseif ($null -ne $Object -and $Object.PSObject.Properties[$Name]) {
        return $Object.$Name
    }
    return $Default
}

function Test-HasValue($Object, [string]$Name) {
    if ($Object -is [Collections.IDictionary]) { return $Object.Contains($Name) }
    return $null -ne $Object -and $null -ne $Object.PSObject.Properties[$Name]
}

function ConvertTo-UtcIso([long]$Milliseconds) {
    [DateTimeOffset]::FromUnixTimeMilliseconds($Milliseconds).UtcDateTime.ToString('yyyy-MM-ddTHH:mm:ssZ')
}

function Get-EventNumber($Event, [string]$Name) {
    $value = Get-Value $Event $Name
    $parsed = 0L
    if ($null -eq $value -or -not [long]::TryParse([string]$value, [ref]$parsed)) {
        throw "Incidents.searchTriggerEvents returned an invalid $Name."
    }
    return $parsed
}

function ConvertFrom-SearchQueries([string]$Value) {
    try {
        $parsed = @($Value | ConvertFrom-Json)
    }
    catch {
        throw 'NETLD_SEARCH_QUERIES must be a JSON array of strings.'
    }
    if (-not $Value.Trim().StartsWith('[')) {
        throw 'NETLD_SEARCH_QUERIES must be a JSON array of strings.'
    }
    $queries = [Collections.Generic.List[string]]::new()
    foreach ($item in $parsed) {
        if ($item -isnot [string] -or -not $item.Trim()) {
            throw 'NETLD_SEARCH_QUERIES must be a JSON array of non-empty strings.'
        }
        $query = $item.Trim()
        if ($query -match '^(?i:start|end)=') {
            throw 'NETLD_SEARCH_QUERIES must not contain start or end; the exporter controls its time window.'
        }
        $queries.Add($query)
    }
    return @($queries)
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
    $content = ($Value | ConvertTo-Json -Depth 30) + [Environment]::NewLine
    Write-AtomicBytes $Path ([Text.UTF8Encoding]::new($false).GetBytes($content))
}

function Get-ViolationExportState([string]$Path) {
    if (-not (Test-Path $Path)) {
        return [ordered]@{ format = $script:StateFormat; formatVersion = 1 }
    }
    $state = Get-Content $Path -Raw | ConvertFrom-Json -AsHashtable
    if ($state.format -ne $script:StateFormat -or $state.formatVersion -ne 1) {
        throw 'The violation-export state file has an unsupported format.'
    }
    return $state
}

function Get-ViolationQueries($Config, $State, [long]$NowMs) {
    $start = if ($State.Contains('lastUpdated')) {
        [long]$State.lastUpdated
    }
    else {
        $NowMs - ([long]$Config.InitialLookbackHours * 60 * 60 * 1000)
    }
    $queries = [Collections.Generic.List[string]]::new()
    foreach ($query in @($Config.SearchQueries)) { $queries.Add([string]$query) }
    $queries.Add("start=$(ConvertTo-UtcIso $start)")
    $queries.Add("end=$(ConvertTo-UtcIso $NowMs)")
    return @($queries)
}

function Get-ThirdEyeViolationEvents([scriptblock]$Search, [string[]]$Queries, [int]$PageSize) {
    $offset = 0
    $total = $null
    $pageCount = 0
    $events = [Collections.Generic.List[object]]::new()
    while ($null -eq $total -or $offset -lt $total) {
        $page = & $Search $Queries $offset $PageSize
        if (-not (Test-HasValue $page 'violations')) {
            throw 'Incidents.searchTriggerEvents returned invalid page data.'
        }
        $batch = @(Get-Value $page 'violations' @())
        $pageOffset = [int](Get-Value $page 'offset' $offset)
        $pageTotal = [int](Get-Value $page 'total' ($pageOffset + $batch.Count))
        $total = if ($null -eq $total) { $pageTotal } else { [Math]::Max([int]$total, $pageTotal) }
        $pageCount++
        foreach ($event in $batch) {
            [void](Get-EventNumber $event 'eventId')
            [void](Get-EventNumber $event 'updated')
            $events.Add($event)
        }
        $nextOffset = $pageOffset + $batch.Count
        if ($nextOffset -ge $total) { break }
        if (-not $batch.Count -or $nextOffset -le $offset) {
            throw 'Violation paging stopped before all reported results were returned.'
        }
        $offset = $nextOffset
    }
    $unique = @{}
    foreach ($event in $events) {
        $key = "$(Get-EventNumber $event 'updated'):$(Get-EventNumber $event 'eventId')"
        $unique[$key] = $event
    }
    $sorted = @($unique.Values | Sort-Object `
        @{ Expression = { Get-EventNumber $_ 'updated' } }, `
        @{ Expression = { Get-EventNumber $_ 'eventId' } })
    [pscustomobject]@{
        Events = $sorted
        PageCount = $pageCount
    }
}

function Select-ViolationEvents($Events, $State) {
    if (-not $State.Contains('lastUpdated')) { return @($Events) }
    $watermark = [long]$State.lastUpdated
    $ids = @{}
    foreach ($id in @(Get-Value $State 'eventIdsAtLastUpdated' @())) { $ids[[long]$id] = $true }
    return @($Events | Where-Object {
        $updated = Get-EventNumber $_ 'updated'
        $id = Get-EventNumber $_ 'eventId'
        $updated -gt $watermark -or ($updated -eq $watermark -and -not $ids.ContainsKey($id))
    })
}

function Write-ViolationExport([string]$Path, [string]$Format, $Events) {
    if ($Format -eq 'json') {
        Write-AtomicJson $Path @($Events)
        return
    }
    $rows = foreach ($event in $Events) {
        $row = [ordered]@{}
        foreach ($field in $script:CsvFields) {
            $value = Get-Value $event $field
            if ($field -in @('created', 'updated') -and $null -ne $value) {
                $value = ConvertTo-UtcIso ([long]$value)
            }
            $row[$field] = $value
        }
        [pscustomobject]$row
    }
    $content = (@($rows) | ConvertTo-Csv -NoTypeInformation) -join [Environment]::NewLine
    $content += [Environment]::NewLine
    Write-AtomicBytes $Path ([Text.UTF8Encoding]::new($false).GetBytes($content))
}

function Update-ViolationState($State, $Events) {
    if (-not @($Events).Count) { return }
    $newest = (@($Events) | ForEach-Object { Get-EventNumber $_ 'updated' } | Measure-Object -Maximum).Maximum
    $ids = @(
        $Events |
            Where-Object { (Get-EventNumber $_ 'updated') -eq $newest } |
            ForEach-Object { Get-EventNumber $_ 'eventId' }
    )
    if ($State.Contains('lastUpdated') -and [long]$State.lastUpdated -eq $newest) {
        $ids += @(Get-Value $State 'eventIdsAtLastUpdated' @())
    }
    $State.lastUpdated = [long]$newest
    $State.eventIdsAtLastUpdated = @($ids | Sort-Object -Unique)
}

function Export-ThirdEyeViolationData(
    $Config,
    [scriptblock]$Search,
    [long]$NowMs,
    [string]$GeneratedAt
) {
    $state = Get-ViolationExportState $Config.StatePath
    $queries = @(Get-ViolationQueries $Config $state $NowMs)
    $result = Get-ThirdEyeViolationEvents $Search $queries $Config.PageSize
    $events = @($result.Events)
    $selected = @(Select-ViolationEvents $events $state)
    $outputFile = $null
    if ($selected.Count) {
        $stamp = [DateTimeOffset]::FromUnixTimeMilliseconds($NowMs).UtcDateTime.ToString('yyyyMMddTHHmmssZ')
        $outputFile = Join-Path $Config.OutputDir "violations-$stamp.$($Config.OutputFormat)"
        Write-ViolationExport $outputFile $Config.OutputFormat $selected
        Update-ViolationState $state $selected
    }
    if (-not $GeneratedAt) { $GeneratedAt = ConvertTo-UtcIso $NowMs }
    $report = [ordered]@{
        format = $script:RunFormat
        formatVersion = 1
        generatedAt = $GeneratedAt
        queries = $queries
        pageCount = $result.PageCount
        resultCount = $events.Count
        exportedCount = $selected.Count
        outputFormat = $Config.OutputFormat
        outputFile = $outputFile
    }
    Write-AtomicJson $Config.StatePath $state
    Write-AtomicJson $Config.ReportPath $report
    return $report
}

function Invoke-NetLDRpc($Connection, [string]$Method, $Parameters) {
    $body = @{
        jsonrpc = '2.0'
        method = $Method
        params = $Parameters
        id = [guid]::NewGuid().ToString()
    } | ConvertTo-Json -Depth 20
    $request = @{
        Uri = "$($Connection.BaseUrl)/rest"
        Method = 'Post'
        Headers = @{ Authorization = "Bearer $($Connection.ApiKey)"; 'Content-Type' = 'application/json' }
        Body = $body
        WebSession = $Connection.Session
        MaximumRedirection = 0
        TimeoutSec = 30
    }
    $response = Invoke-WebRequest @request
    $data = $response.Content | ConvertFrom-Json
    $errorProperty = $data.PSObject.Properties['error']
    if ($errorProperty -and $errorProperty.Value) {
        throw "$Method failed: $($errorProperty.Value | ConvertTo-Json -Compress -Depth 10)"
    }
    return $data.result
}

function Invoke-ExportThirdEyeViolations($Config, [long]$NowMs = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()) {
    $session = New-Object Microsoft.PowerShell.Commands.WebRequestSession
    $login = @{
        Uri = "$($Config.BaseUrl)/rest"
        Headers = @{ Authorization = "Bearer $($Config.ApiKey)" }
        WebSession = $session
        MaximumRedirection = 0
        TimeoutSec = 30
    }
    Invoke-WebRequest @login | Out-Null
    $connection = @{ BaseUrl = $Config.BaseUrl; ApiKey = $Config.ApiKey; Session = $session }
    $search = {
        param($queries, $offset, $pageSize)
        Invoke-NetLDRpc $connection 'Incidents.searchTriggerEvents' @{
            pageData = @{ offset = $offset; total = 0; pageSize = $pageSize; violations = @() }
            queries = @($queries)
            sortColumn = 'updated'
            descending = $true
        }
    }
    Export-ThirdEyeViolationData $Config $search $NowMs
}

Export-ModuleMember -Function ConvertFrom-SearchQueries, Export-ThirdEyeViolationData, Get-ViolationQueries, Invoke-ExportThirdEyeViolations, Select-ViolationEvents
