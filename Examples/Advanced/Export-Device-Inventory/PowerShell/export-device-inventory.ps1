param(
    [string]$EnvPath = (Join-Path $PSScriptRoot '.env'),
    [ValidateSet('csv', 'json')][string]$Format
)

$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSScriptRoot 'ExportDeviceInventory.psm1') -Force

try {
    Invoke-ExportDeviceInventory -EnvPath $EnvPath -Format $Format
}
catch {
    Write-Error $_.Exception.Message
    exit 1
}
