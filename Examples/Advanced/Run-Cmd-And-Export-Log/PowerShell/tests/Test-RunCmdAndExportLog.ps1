$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSScriptRoot '..' 'RunCmdAndExportLog.psm1') -Force

function Assert-Equal($Expected, $Actual, [string]$Message) {
    if ($Expected -ne $Actual) { throw "$Message Expected '$Expected', got '$Actual'." }
}

$job = New-CommandRunnerJob -Network 'Lab' -Target '192.0.2.10' -Commands @('show version', 'show clock')
Assert-Equal 'Lab' $job.managedNetworks[0] 'Managed network failed.'
Assert-Equal 'Script Tool Job' $job.jobType 'Job type failed.'
Assert-Equal 'ipCsv' $job.jobParameters.ipResolutionScheme 'Resolution scheme failed.'
Assert-Equal '"192.0.2.10@Lab"' $job.jobParameters.ipResolutionData 'Resolution data failed.'
Assert-Equal "show version`nshow clock" $job.jobParameters.'input.commandList' 'Command list failed.'
Assert-Equal 'false' $job.jobParameters.backupOnCompletion 'Backup default failed.'
Assert-Equal 'Lab_192.0.2.10' (ConvertTo-SafeFilename 'Lab / 192.0.2.10') 'Filename sanitizing failed.'

$threw = $false
try { [void](New-CommandRunnerJob -Network 'Lab' -Target '192.0.2.10' -Commands @()) } catch { $threw = $true }
if (-not $threw) { throw 'Empty command list was not rejected.' }

Write-Host 'PowerShell tests passed.'

