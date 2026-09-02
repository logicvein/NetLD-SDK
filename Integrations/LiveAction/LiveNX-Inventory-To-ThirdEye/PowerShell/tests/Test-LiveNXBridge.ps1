$ErrorActionPreference = "Stop"
Import-Module "$PSScriptRoot/../LiveNXBridge.psm1" -Force

function Assert-Equal {
    param($Expected, $Actual, [string]$Message)
    if (($Expected | ConvertTo-Json -Compress) -ne ($Actual | ConvertTo-Json -Compress)) {
        throw "$Message Expected=$Expected Actual=$Actual"
    }
}

$csv = @"
IP ADDRESS,VENDOR,NAME
192.0.2.10,Cisco,router-1
2001:0db8::1,Juniper,router-2
not-an-address,Cisco,bad-row
192.0.2.20,,vendorless
"@
$addresses = @(ConvertFrom-LiveNXDeviceCsv -CsvText $csv)
Assert-Equal @("192.0.2.10", "2001:db8::1") $addresses "CSV parsing failed."

$source = [pscustomobject]@{
    managedNetwork = "Old"
    jobParameters = [pscustomobject]@{
        managedNetwork = "Old"
        includedAddresses = "192.0.2.1"
    }
}
$prepared = New-PreparedDiscoveryJob `
    -JobData $source `
    -Network "Default" `
    -Address @("2001:db8::1", "192.0.2.20")
Assert-Equal "Old" $source.managedNetwork "The source job was modified."
Assert-Equal "Default" $prepared.managedNetwork "The job network was not updated."
Assert-Equal `
    "192.0.2.20,2001:db8::1" `
    $prepared.jobParameters.includedAddresses `
    "The discovery addresses were not prepared correctly."

$rejected = $false
try {
    [void](New-PreparedDiscoveryJob `
        -JobData ([pscustomobject]@{ jobParameters = [pscustomobject]@{} }) `
        -Network "Default" `
        -Address @("192.0.2.1"))
}
catch {
    $rejected = $true
}
Assert-Equal $true $rejected "A non-discovery job was accepted."

Write-Host "PowerShell offline tests passed."
