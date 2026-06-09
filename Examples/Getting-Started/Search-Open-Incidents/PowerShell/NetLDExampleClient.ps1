function Import-DotEnv {
    param([string]$Path)

    if (-not (Test-Path $Path)) {
        return
    }

    Get-Content $Path | ForEach-Object {
        $line = $_.Trim()
        if (-not $line -or $line.StartsWith("#") -or -not $line.Contains("=")) {
            return
        }

        $name, $value = $line.Split("=", 2)
        $value = $value.Trim().Trim('"').Trim("'")
        [Environment]::SetEnvironmentVariable($name.Trim(), $value, "Process")
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
        $this.Session = $null
    }

    [hashtable] Headers() {
        return @{
            Authorization = "Bearer $($this.ApiKey)"
            "Content-Type" = "application/json"
        }
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
            if (-not $_.Exception.Response) {
                throw [NetLDError]::new(
                    "Could not reach $($this.BaseUrl). Check NETLD_BASE_URL in your .env file."
                )
            }

            $statusCode = [int]$_.Exception.Response.StatusCode
            if ($statusCode -ge 300 -and $statusCode -lt 400) {
                $location = $_.Exception.Response.Headers.Location
                throw [NetLDError]::new(
                    "Login redirected instead of returning a netLD session. Redirect target: $location"
                )
            }
            throw
        }

        Write-Host "Login status=$($response.StatusCode)"

        if ($this.Debug) {
            Write-Host "Cookies=$($this.Session.Cookies.GetCookieHeader($this.BaseUrl))"
        }
    }

    [object] Call([string]$method, [hashtable]$params) {
        $payload = @{
            jsonrpc = "2.0"
            method = $method
            params = $params
            id = [guid]::NewGuid().ToString()
        }
        $body = $payload | ConvertTo-Json -Depth 12

        if ($this.Debug) {
            Write-Host "Request JSON:"
            Write-Host $body
        }

        try {
            $response = Invoke-WebRequest `
                -Uri "$($this.BaseUrl)/rest" `
                -Method Post `
                -Headers $this.Headers() `
                -Body $body `
                -WebSession $this.Session `
                -MaximumRedirection 0 `
                -TimeoutSec $this.TimeoutSec `
                -ErrorAction Stop
        }
        catch {
            if (-not $_.Exception.Response) {
                throw [NetLDError]::new(
                    "Could not reach $($this.BaseUrl). Check NETLD_BASE_URL in your .env file."
                )
            }

            $statusCode = [int]$_.Exception.Response.StatusCode
            if ($statusCode -ge 300 -and $statusCode -lt 400) {
                $location = $_.Exception.Response.Headers.Location
                throw [NetLDError]::new(
                    "API call redirected instead of returning JSON-RPC data. Redirect target: $location"
                )
            }
            throw
        }

        if ([string]::IsNullOrWhiteSpace($response.Content)) {
            return $null
        }

        $data = $response.Content | ConvertFrom-Json

        if ($null -eq $data) {
            return $null
        }

        if ($this.Debug) {
            Write-Host "Response JSON:"
            Write-Host ($data | ConvertTo-Json -Depth 12)
        }

        if ($data.error) {
            throw [NetLDError]::new(($data.error | ConvertTo-Json -Depth 12))
        }

        return $data.result
    }

    [object] SearchOpenIncidents(
        [string]$network,
        [int]$offset,
        [int]$pageSize,
        [string]$sortColumn,
        [bool]$descending
    ) {
        return $this.Call("Incidents.searchIncidents", @{
            pageData = @{
                offset = $offset
                total = 0
                pageSize = $pageSize
                incidents = @()
            }
            queries = @(
                "status=OPEN,WORKING"
                "networks=$network"
            )
            sortColumn = $sortColumn
            descending = $descending
        })
    }
}

function Show-Incidents {
    param([object]$PageData)

    if (-not $PageData) {
        Write-Host "No incident data returned. Incidents.searchIncidents is available only on ThirdEye."
        return
    }

    $PageData | ConvertTo-Json -Depth 12
}
