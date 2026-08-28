param([string]$EnvPath = (Join-Path $PSScriptRoot '.env'))

$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSScriptRoot 'RunCmdAndExportLog.psm1') -Force

try {
    Invoke-RunCmdAndExportLog -EnvPath $EnvPath
}
catch {
    Write-Error $_.Exception.Message
    exit 1
}

