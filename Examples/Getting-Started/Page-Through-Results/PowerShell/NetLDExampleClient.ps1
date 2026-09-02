function Import-DotEnv {
    param([string]$Path)

    if (-not (Test-Path $Path)) { return }
    Get-Content $Path | ForEach-Object {
        $line = $_.Trim()
        if (-not $line -or $line.StartsWith("#") -or -not $line.Contains("=")) { return }
        $name, $value = $line.Split("=", 2)
        [Environment]::SetEnvironmentVariable(
            $name.Trim(), $value.Trim().Trim('"').Trim("'"), "Process"
        )
    }
}

class NetLDError : Exception {
    NetLDError([string]$message) : base($message) {}
}

class NetLDClient {
    [string]$BaseUrl
    [string]$ApiKey
    [int]$TimeoutSec
    [bool]$Debug
    [object]$Session

    NetLDClient([string]$baseUrl, [string]$apiKey, [int]$timeoutSec = 10, [bool]$debug = $false) {
        $this.BaseUrl = $baseUrl.TrimEnd("/")
        $this.ApiKey = $apiKey
        $this.TimeoutSec = $timeoutSec
        $this.Debug = $debug
    }

    [void] Login() {
        $webSession = $null
        try {
            $response = Invoke-WebRequest `
                -Uri "$($this.BaseUrl)/rest" `
                -Headers @{ Authorization = "Bearer $($this.ApiKey)" } `
                -SessionVariable webSession `
                -MaximumRedirection 0 `
                -TimeoutSec $this.TimeoutSec `
                -ErrorAction Stop
            $this.Session = $webSession
        }
        catch {
            throw [NetLDError]::new("Could not authenticate with $($this.BaseUrl): $($_.Exception.Message)")
        }
        Write-Host "Login status=$($response.StatusCode)"
    }

    [object] Call([string]$method, [hashtable]$params) {
        $payload = @{
            jsonrpc = "2.0"
            method = $method
            params = $params
            id = [guid]::NewGuid().ToString()
        }
        $body = $payload | ConvertTo-Json -Depth 12
        if ($this.Debug) { Write-Host "Request JSON:`n$body" }
        try {
            $response = Invoke-WebRequest `
                -Uri "$($this.BaseUrl)/rest" `
                -Method Post `
                -Headers @{
                    Authorization = "Bearer $($this.ApiKey)"
                    "Content-Type" = "application/json"
                } `
                -Body $body `
                -WebSession $this.Session `
                -MaximumRedirection 0 `
                -TimeoutSec $this.TimeoutSec `
                -ErrorAction Stop
        }
        catch {
            throw [NetLDError]::new("API call $method failed: $($_.Exception.Message)")
        }
        $data = $response.Content | ConvertFrom-Json
        if ($this.Debug) { Write-Host "Response JSON:`n$($data | ConvertTo-Json -Depth 12)" }
        if ($data.error) {
            throw [NetLDError]::new(($data.error | ConvertTo-Json -Depth 12))
        }
        return $data.result
    }

    [object] GetConfigurationChangeLogPage(
        [string]$network,
        [string]$ipAddress,
        [int]$offset,
        [int]$pageSize
    ) {
        return $this.Call("Configuration.retrieveSnapshotChangeLog", @{
            network = $network
            ipAddress = $ipAddress
            pageData = @{ offset = $offset; pageSize = $pageSize }
        })
    }
}
