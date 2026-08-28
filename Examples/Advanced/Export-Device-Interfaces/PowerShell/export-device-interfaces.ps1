param([string]$EnvPath = (Join-Path $PSScriptRoot '.env'))

$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSScriptRoot 'ExportDeviceInterfaces.psm1') -Force

try {
    $result = Invoke-ExportDeviceInterfaces -EnvPath $EnvPath
    if ($result.FailureCount -gt 0) { exit 2 }
}
catch {
    Write-Error $_.Exception.Message
    exit 1
}
