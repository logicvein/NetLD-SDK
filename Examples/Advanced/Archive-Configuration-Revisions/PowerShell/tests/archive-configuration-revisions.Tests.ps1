$ErrorActionPreference='Stop'
Import-Module (Join-Path $PSScriptRoot '..' 'ArchiveConfigurationRevisions.psm1') -Force
function Assert-Equal($Expected,$Actual,[string]$Message){if($Expected-ne$Actual){throw "$Message (expected $Expected, got $Actual)"}}
function New-TestConfig([string]$Base,[string]$Mode='latest'){[pscustomobject]@{ArchiveDir=Join-Path $Base 'archive';StatePath=Join-Path $Base 'state.json';RunReportPath=Join-Path $Base 'run.json';InitialMode=$Mode}}
$items=@([pscustomobject]@{managedNetwork='Default';ipAddress='192.0.2.1';path='/running-config';lastChanged=300;mimeType='text/plain'},[pscustomobject]@{managedNetwork='Default';ipAddress='192.0.2.1';path='/startup-config';lastChanged=200;mimeType='text/plain'},[pscustomobject]@{managedNetwork='Default';ipAddress='192.0.2.1';path='/running-config';lastChanged=100;mimeType='text/plain'})
$getDevices={@([pscustomobject]@{network='Default';ipAddress='192.0.2.1'})};$getHistory={param($device,$old)$items};$getRevision={param($item)[pscustomobject]@{path=$item.path;lastChanged=$item.lastChanged;mimeType='text/plain';size=4;content=[Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes('test'))}}
$base=Join-Path ([IO.Path]::GetTempPath()) "netld-pwsh-$([guid]::NewGuid())"
try{$config=New-TestConfig $base;$first=Invoke-ConfigurationRevisionArchive $config $getDevices $getHistory $getRevision '2026-08-28T12:00:00Z';$second=Invoke-ConfigurationRevisionArchive $config $getDevices $getHistory $getRevision '2026-08-28T12:01:00Z';Assert-Equal 2 $first.archivedCount 'latest baseline';Assert-Equal 0 $second.archivedCount 'incremental no-op';$state=Get-Content $config.StatePath -Raw|ConvertFrom-Json;Assert-Equal 300 $state.devices.'Default@192.0.2.1'.lastChanged 'watermark'}finally{if(Test-Path $base){Remove-Item $base -Recurse -Force}}
$base=Join-Path ([IO.Path]::GetTempPath()) "netld-pwsh-$([guid]::NewGuid())"
try{$config=New-TestConfig $base 'all';$report=Invoke-ConfigurationRevisionArchive $config $getDevices $getHistory $getRevision;Assert-Equal 3 $report.archivedCount 'all baseline'}finally{if(Test-Path $base){Remove-Item $base -Recurse -Force}}
Write-Host 'PowerShell archive tests passed.'
