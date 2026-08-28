param([string]$EnvPath = (Join-Path $PSScriptRoot '.env'))

$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSScriptRoot 'ExportDeviceInventory.psm1') -Force

try {
    Invoke-ExportDeviceInventory -EnvPath $EnvPath
}
catch {
    Write-Error $_.Exception.Message
    exit 1
}
