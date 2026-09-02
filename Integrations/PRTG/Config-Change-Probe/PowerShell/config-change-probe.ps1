param([string]$EnvPath = (Join-Path $PSScriptRoot '.env'))

$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSScriptRoot 'ConfigChangeProbe.psm1') -Force

try {
    $result = Invoke-ConfigChangeProbe -EnvPath $EnvPath
    ConvertTo-PrtgXmlResult -DeviceCount $result.DeviceCount
}
catch {
    ConvertTo-PrtgXmlError -Message $_.Exception.Message
}
exit 0

