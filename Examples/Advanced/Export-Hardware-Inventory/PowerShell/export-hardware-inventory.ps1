[CmdletBinding()]param([string]$EnvPath=(Join-Path $PSScriptRoot '.env'),[ValidateSet('csv','json')][string]$Format)
$ErrorActionPreference='Stop';Import-Module (Join-Path $PSScriptRoot 'ExportHardwareInventory.psm1') -Force
try{$result=Invoke-ExportHardwareInventory -EnvPath $EnvPath -Format $Format;if($result.FailureCount){exit 2}}catch{Write-Error $_;exit 1}
