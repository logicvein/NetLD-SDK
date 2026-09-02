function Import-DotEnv {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) { return }
    Get-Content -LiteralPath $Path | ForEach-Object {
        $line = $_.Trim()
        if (-not $line -or $line.StartsWith('#') -or -not $line.Contains('=')) { return }
        $name, $value = $line.Split('=', 2)
        [Environment]::SetEnvironmentVariable($name.Trim(), $value.Trim().Trim('"').Trim("'"), 'Process')
    }
}

class NetLDError : Exception {
    NetLDError([string]$message) : base($message) {}
}

class NetLDClient {
    [string]$BaseUrl
    [string]$ApiKey
    [int]$TimeoutSec
    [object]$Session

    NetLDClient([string]$baseUrl, [string]$apiKey, [int]$timeoutSec = 10) {
        $this.BaseUrl = $baseUrl.TrimEnd('/')
        $this.ApiKey = $apiKey
        $this.TimeoutSec = $timeoutSec
    }

    [void] Login() {
        $webSession = $null
        try {
            [void](Invoke-WebRequest -Uri "$($this.BaseUrl)/rest" `
                -Headers @{ Authorization = "Bearer $($this.ApiKey)" } `
                -SessionVariable webSession -MaximumRedirection 0 `
                -TimeoutSec $this.TimeoutSec -ErrorAction Stop)
        }
        catch { throw [NetLDError]::new("Could not authenticate to $($this.BaseUrl).") }
        $this.Session = $webSession
    }

    [object] Call([string]$method, [hashtable]$parameters) {
        $body = @{ jsonrpc = '2.0'; method = $method; params = $parameters; id = [guid]::NewGuid().ToString() } |
            ConvertTo-Json -Depth 20
        try {
            $response = Invoke-WebRequest -Uri "$($this.BaseUrl)/rest" -Method Post `
                -Headers @{ Authorization = "Bearer $($this.ApiKey)"; 'Content-Type' = 'application/json' } `
                -Body $body -WebSession $this.Session -MaximumRedirection 0 `
                -TimeoutSec $this.TimeoutSec -ErrorAction Stop
        }
        catch { throw [NetLDError]::new("netLD API call $method failed.") }
        $data = $response.Content | ConvertFrom-Json
        $errorProperty = $data.PSObject.Properties['error']
        if ($errorProperty -and $errorProperty.Value) {
            throw [NetLDError]::new(($errorProperty.Value | ConvertTo-Json -Depth 20 -Compress))
        }
        $resultProperty = $data.PSObject.Properties['result']
        if (-not $resultProperty) { throw [NetLDError]::new("netLD API call $method returned no result field.") }
        return $resultProperty.Value
    }

    [object] GetDevice([string]$network, [string]$ipAddress) {
        return $this.Call('Inventory.getDevice', @{ network = $network; ipAddress = $ipAddress })
    }

    [object] CreateDevice([string]$network, [string]$ipAddress, [string]$adapterId) {
        return $this.Call('Inventory.createDevice', @{
            network = $network; ipAddress = $ipAddress; adapterId = $adapterId
        })
    }
}

function New-CreateDeviceParameters {
    param(
        [Parameter(Mandatory)][string]$Network,
        [Parameter(Mandatory)][string]$IpAddress,
        [Parameter(Mandatory)][string]$AdapterId
    )
    $parsed = $null
    if (-not [Net.IPAddress]::TryParse($IpAddress, [ref]$parsed)) {
        throw [NetLDError]::new("NETLD_DEVICE_IP is not a valid IPv4 or IPv6 address: $IpAddress")
    }
    if (-not $Network.Trim()) { throw [NetLDError]::new('NETLD_NETWORK cannot be empty.') }
    if (-not $AdapterId.Trim()) { throw [NetLDError]::new('NETLD_ADAPTER_ID cannot be empty.') }
    return [ordered]@{
        network = $Network.Trim()
        ipAddress = $parsed.ToString()
        adapterId = $AdapterId.Trim()
    }
}

