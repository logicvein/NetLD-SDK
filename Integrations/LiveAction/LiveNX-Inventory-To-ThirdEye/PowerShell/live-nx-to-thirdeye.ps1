[CmdletBinding()]
param(
    [string]$EnvPath = "$PSScriptRoot/.env",
    [switch]$Apply
)

Import-Module "$PSScriptRoot/LiveNXBridge.psm1" -Force

try {
    Invoke-LiveNXBridge -EnvPath $EnvPath -Apply:$Apply
}
catch {
    Write-Error $_.Exception.Message
    exit 1
}
