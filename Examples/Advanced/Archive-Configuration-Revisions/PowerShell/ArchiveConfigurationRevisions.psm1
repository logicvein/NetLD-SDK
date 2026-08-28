Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$script:StateFormat = 'logicvein-netld-configuration-archive-state'
$script:RunFormat = 'logicvein-netld-configuration-archive-run'

function Get-ObjectValue($Object, [string]$Name, $Default = $null) {
    if ($Object -is [System.Collections.IDictionary]) { if ($Object.Contains($Name)) { return $Object[$Name] } }
    elseif ($null -ne $Object -and $Object.PSObject.Properties[$Name]) { return $Object.$Name }
    return $Default
}
function Get-SafeName([string]$Value, [string]$Fallback) {
    $clean = ($Value.Trim() -replace '[^A-Za-z0-9._-]+', '_').Trim(' ','.','_')
    if ($clean) { $clean } else { $Fallback }
}
function Get-PathHash([string]$Value) {
    $sha = [Security.Cryptography.SHA256]::Create()
    try { ([BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($Value))) -replace '-', '').ToLowerInvariant().Substring(0,8) } finally { $sha.Dispose() }
}
function Write-AtomicBytes([string]$Path, [byte[]]$Bytes) {
    $directory = Split-Path -Parent $Path
    [IO.Directory]::CreateDirectory($directory) | Out-Null
    $temporary = Join-Path $directory ".$([IO.Path]::GetFileName($Path)).$([guid]::NewGuid()).tmp"
    try { [IO.File]::WriteAllBytes($temporary, $Bytes); [IO.File]::Move($temporary, $Path, $true) } finally { if (Test-Path -LiteralPath $temporary) { Remove-Item -LiteralPath $temporary -Force } }
}
function Write-AtomicJson([string]$Path, $Value) {
    $json = ($Value | ConvertTo-Json -Depth 30) + [Environment]::NewLine
    Write-AtomicBytes $Path ([Text.UTF8Encoding]::new($false).GetBytes($json))
}
function Get-ArchiveState([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) { return [ordered]@{ format=$script:StateFormat; formatVersion=1; devices=@{} } }
    $state = Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json -AsHashtable
    if ($state.format -ne $script:StateFormat -or $state.formatVersion -ne 1 -or $state.devices -isnot [System.Collections.IDictionary]) { throw 'The archive state file has an unsupported format.' }
    $state
}
function Select-RevisionCandidates($Items, $StateEntry, [string]$InitialMode) {
    $selected = @()
    if ($null -eq $StateEntry) {
        if ($InitialMode -eq 'all') { $selected = @($Items) }
        else {
            $seen = @{}; foreach ($item in $Items) { $p = [string](Get-ObjectValue $item 'path'); if (-not $seen.ContainsKey($p)) { $seen[$p]=$true; $selected += $item } }
        }
    } else {
        $watermark = [long](Get-ObjectValue $StateEntry 'lastChanged'); $paths = @((Get-ObjectValue $StateEntry 'pathsAtLastChanged' @{}))
        $selected = @($Items | Where-Object { [long](Get-ObjectValue $_ 'lastChanged') -gt $watermark -or ([long](Get-ObjectValue $_ 'lastChanged') -eq $watermark -and $paths -notcontains [string](Get-ObjectValue $_ 'path')) })
    }
    $unique = @{}; foreach ($item in $selected) { $unique["$([long](Get-ObjectValue $item 'lastChanged'))`0$([string](Get-ObjectValue $item 'path'))"] = $item }
    @($unique.Values | Sort-Object @{Expression={ [long](Get-ObjectValue $_ 'lastChanged') }}, @{Expression={ [string](Get-ObjectValue $_ 'path') }})
}
function Save-Revision($Config, $Item, $Revision) {
    try { [byte[]]$content = [Convert]::FromBase64String([string](Get-ObjectValue $Revision 'content' '')) } catch { throw 'Configuration revision content is not valid Base64.' }
    $network=[string](Get-ObjectValue $Item 'managedNetwork'); $ip=[string](Get-ObjectValue $Item 'ipAddress'); $configPath=[string](Get-ObjectValue $Item 'path'); $timestamp=[long](Get-ObjectValue $Item 'lastChanged')
    $mime=[string](Get-ObjectValue $Revision 'mimeType' (Get-ObjectValue $Item 'mimeType' '')); $extension=if ($mime.StartsWith('text/')) { '.txt' } else { '.bin' }
    $stem="${timestamp}_$(Get-SafeName $configPath 'config')_$(Get-PathHash $configPath)"; $directory=Join-Path $Config.ArchiveDir (Join-Path (Get-SafeName $network 'network') (Get-SafeName $ip 'device'))
    $contentPath=Join-Path $directory ($stem+$extension); $metadataPath=Join-Path $directory ($stem+'.metadata.json'); Write-AtomicBytes $contentPath $content
    $revisionMetadata=[ordered]@{}; foreach ($property in $Revision.PSObject.Properties) { if ($property.Name -ne 'content') { $revisionMetadata[$property.Name]=$property.Value } }
    Write-AtomicJson $metadataPath ([ordered]@{ network=$network; ipAddress=$ip; configPath=$configPath; lastChanged=$timestamp; history=$Item; revision=$revisionMetadata; contentFile=[IO.Path]::GetFileName($contentPath) })
    [ordered]@{ network=$network; ipAddress=$ip; configPath=$configPath; lastChanged=$timestamp; mimeType=$mime; size=$content.Length; contentFile=[IO.Path]::GetRelativePath($Config.ArchiveDir,$contentPath); metadataFile=[IO.Path]::GetRelativePath($Config.ArchiveDir,$metadataPath) }
}

function Invoke-ConfigurationRevisionArchive {
    [CmdletBinding()] param([Parameter(Mandatory)]$Config,[Parameter(Mandatory)][scriptblock]$GetDevices,[Parameter(Mandatory)][scriptblock]$GetHistory,[Parameter(Mandatory)][scriptblock]$GetRevision,[string]$GeneratedAt)
    $state=Get-ArchiveState $Config.StatePath; $archived=[Collections.Generic.List[object]]::new(); $failures=[Collections.Generic.List[object]]::new(); $devices=@(& $GetDevices)
    foreach ($device in $devices) {
        $network=[string](Get-ObjectValue $device 'network'); $ip=[string](Get-ObjectValue $device 'ipAddress'); $key="$network@$ip"; $old=if ($state.devices.Contains($key)) {$state.devices[$key]} else {$null}
        try { $items=@(& $GetHistory $device $old); $candidates=@(Select-RevisionCandidates $items $old $Config.InitialMode) } catch { $failures.Add([ordered]@{stage='history';network=$network;ipAddress=$ip;error=$_.Exception.Message}); continue }
        $failed=$false
        foreach ($item in $candidates) { try { $archived.Add((Save-Revision $Config $item (& $GetRevision $item))) } catch { $failed=$true; $failures.Add([ordered]@{stage='revision';network=(Get-ObjectValue $item 'managedNetwork');ipAddress=(Get-ObjectValue $item 'ipAddress');configPath=(Get-ObjectValue $item 'path');lastChanged=(Get-ObjectValue $item 'lastChanged');error=$_.Exception.Message}) } }
        if ($candidates.Count -and -not $failed) { $newest=($candidates | ForEach-Object {[long](Get-ObjectValue $_ 'lastChanged')} | Measure-Object -Maximum).Maximum; $paths=@($candidates | Where-Object {[long](Get-ObjectValue $_ 'lastChanged') -eq $newest} | ForEach-Object {[string](Get-ObjectValue $_ 'path')}); if ($null-ne $old -and $newest -eq [long](Get-ObjectValue $old 'lastChanged')) {$paths+=@(Get-ObjectValue $old 'pathsAtLastChanged' @())}; $state.devices[$key]=[ordered]@{lastChanged=[long]$newest;pathsAtLastChanged=@($paths|Sort-Object -Unique)} }
    }
    if (-not $GeneratedAt) {$GeneratedAt=[DateTime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ssZ')}; $report=[ordered]@{format=$script:RunFormat;formatVersion=1;generatedAt=$GeneratedAt;initialMode=$Config.InitialMode;deviceCount=$devices.Count;archivedCount=$archived.Count;failureCount=$failures.Count;archived=@($archived);failures=@($failures)}
    Write-AtomicJson $Config.StatePath $state; Write-AtomicJson $Config.RunReportPath $report; $report
}

function Invoke-NetLDRpc($Session,[string]$BaseUrl,[string]$ApiKey,[string]$Method,$Parameters) {
    $headers=@{Authorization="Bearer $ApiKey"}; $body=@{jsonrpc='2.0';method=$Method;params=$Parameters;id=[guid]::NewGuid().ToString()}|ConvertTo-Json -Depth 15
    $response=Invoke-RestMethod -WebSession $Session -Uri "$BaseUrl/rest" -Method Post -Headers $headers -ContentType 'application/json' -Body $body
    $rpcError=Get-ObjectValue $response 'error'; if ($rpcError) { throw "$Method failed: $($rpcError | ConvertTo-Json -Compress -Depth 10)" }; Get-ObjectValue $response 'result'
}
function Get-PagedValues([scriptblock]$Fetch,[string]$Property,[int]$PageSize,$StopBefore=$null) {
    $values=[Collections.Generic.List[object]]::new();$offset=0;$total=$null
    while ($true) { $page=& $Fetch $offset; $pageValues=@(Get-ObjectValue $page $Property @()); foreach($value in $pageValues){if($null-ne $StopBefore -and [long](Get-ObjectValue $value 'lastChanged') -lt [long]$StopBefore){return @($values)};$values.Add($value)};if($null-eq $total -and $null-ne (Get-ObjectValue $page 'total')){$total=[long](Get-ObjectValue $page 'total')};$actual=[int](Get-ObjectValue $page 'pageSize' $PageSize);if(($null-ne $total -and $offset+$pageValues.Count-ge $total)-or($null-eq $total -and $pageValues.Count-lt $actual)){return @($values)};if(-not $pageValues.Count){throw "$Property returned an empty page before the reported total."};$offset+=$actual }
}

function Start-ConfigurationRevisionArchive {
    [CmdletBinding()] param([Parameter(Mandatory)]$Config)
    $session=New-Object Microsoft.PowerShell.Commands.WebRequestSession; Invoke-WebRequest -WebSession $session -Uri "$($Config.BaseUrl)/rest" -Headers @{Authorization="Bearer $($Config.ApiKey)"} -Method Get -MaximumRedirection 0 | Out-Null
    $getDevices={ Get-PagedValues {param($offset) Invoke-NetLDRpc $session $Config.BaseUrl $Config.ApiKey 'Inventory.search' @{network=@($Config.Networks);scheme=$Config.SearchScheme;query=($Config.SearchQuery+$(if($Config.SearchQuery.EndsWith("`n")){''}else{"`n"}));pageData=@{offset=$offset;pageSize=$Config.InventoryPageSize};sortColumn='ipAddress';descending=$false}} 'devices' $Config.InventoryPageSize }
    $getHistory={param($device,$old) $stop=if($null-ne $old){[long](Get-ObjectValue $old 'lastChanged')}else{$null}; Get-PagedValues {param($offset) Invoke-NetLDRpc $session $Config.BaseUrl $Config.ApiKey 'Configuration.retrieveConfigHistory' @{pageData=@{offset=$offset;pageSize=$Config.HistoryPageSize;total=0;configHistoryItems=@()};networks=@($device.network);scheme='ipAddress';data=$device.ipAddress;sortColumn='session';descending=$true}} 'configHistoryItems' $Config.HistoryPageSize $stop }
    $getRevision={param($item) Invoke-NetLDRpc $session $Config.BaseUrl $Config.ApiKey 'Configuration.retrieveRevision' @{network=$item.managedNetwork;ipAddress=$item.ipAddress;configPath=$item.path;timestamp=$item.lastChanged}}
    Invoke-ConfigurationRevisionArchive $Config $getDevices $getHistory $getRevision
}
Export-ModuleMember -Function Invoke-ConfigurationRevisionArchive,Start-ConfigurationRevisionArchive
