param(
    [string]$EnvPath = "$PSScriptRoot/.env"
)

. "$PSScriptRoot/NetLDExampleClient.ps1"

Import-DotEnv -Path $EnvPath

$baseUrl = $env:NETLD_BASE_URL
$apiKey = $env:NETLD_API_KEY
$network = if ($env:NETLD_NETWORK) { $env:NETLD_NETWORK } else { "Default" }
$jobName = $env:NETLD_JOB_NAME
$pageSize = if ($env:NETLD_JOB_PAGE_SIZE) { [int]$env:NETLD_JOB_PAGE_SIZE } else { 100 }
$runJob = $env:NETLD_RUN_JOB -eq "true"
$debugMode = $env:NETLD_DEBUG -eq "1"

if (-not $baseUrl) {
    throw [NetLDError]::new("Set NETLD_BASE_URL in .env before running this example.")
}

if (-not $apiKey) {
    throw [NetLDError]::new("Set NETLD_API_KEY before running this example.")
}

if (-not $jobName) {
    throw [NetLDError]::new("Set NETLD_JOB_NAME to the exact name of the job to run.")
}

$client = [NetLDClient]::new($baseUrl, $apiKey, 10, $debugMode)
$client.Login()

$pageData = $client.SearchAvailableJobs(@($network), 0, $pageSize, "", $false)
$matches = @($pageData.jobData | Where-Object { $_.jobName -eq $jobName })

if ($matches.Count -eq 0) {
    throw [NetLDError]::new("No available job named `"$jobName`" was found.")
}

if ($matches.Count -gt 1) {
    $jobIds = ($matches | ForEach-Object { $_.jobId }) -join ", "
    throw [NetLDError]::new("Multiple jobs named `"$jobName`" were found: $jobIds")
}

$jobId = [int]$matches[0].jobId
$jobData = $client.GetJob($jobId)

if (-not $jobData) {
    throw [NetLDError]::new("Scheduler.getJob returned no data for job ID $jobId.")
}

Write-Host "Selected job `"$jobName`" with ID ${jobId}:"
Show-Json -Value $jobData

if (-not $runJob) {
    Write-Host "Dry run only. Set NETLD_RUN_JOB=true to execute this job."
} else {
    $execution = $client.RunNow($jobData)
    Write-Host "Execution started:"
    Show-Json -Value $execution
}
