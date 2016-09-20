Class NLDService {
  [string] $url
  [string] $username
  [string] $password
  [int] $id = 0
  [Net.CookieContainer] $cookies = $null

  NLDService([string] $username, [string] $password, [string] $server) {
    $this.username = $username
    $this.password = $password
    $this.url = "https://${server}/rest"
  }

  NLDService([string] $username, [string] $password, [string] $server, [int] $port) {
    $this.username = $username
    $this.password = $password
    $this.url = "https://${server}:${port}/rest"
  }

  [PSCustomObject] call([string] $service, $params) {
    [string] $uri = $this.url

    if ($this.cookies -eq $null) {
      $this.cookies = New-Object Net.CookieContainer
      [Net.ServicePointManager]::ServerCertificateValidationCallback = {$true}
      $uri = "${uri}?j_username=$($this.username)&j_password=$($this.password)"
    }

    $this.id++

    [PSObject] $data = (New-Object PSObject |
      Add-Member -PassThru NoteProperty method $service |
      Add-Member -PassThru NoteProperty params $params  |
      Add-Member -PassThru NoteProperty id "$($this.id)")  |
      ConvertTo-Json -depth 3

    $bytes = [Text.Encoding]::utf8.GetBytes($data)

    [Net.HttpWebRequest] $web = [Net.WebRequest]::Create($uri)
    $web.Method = 'POST'
    $web.Headers.Add('Accept-Encoding: gzip,deflate')
    $web.CookieContainer = $this.cookies
    $web.ContentType = 'œapplication/json'
    $web.ContentLength = $bytes.Length

    $stream = $web.GetRequestStream()
    $stream.Write($bytes, 0, $bytes.Length)
    $stream.close()

    $reader = New-Object System.IO.Streamreader -ArgumentList $web.GetResponse().GetResponseStream()
    #return $reader.ReadToEnd() | ConvertFrom-Json
    $json = $reader.ReadToEnd() | ConvertFrom-Json
    return $json.result
    $reader.Close()
  }

  close() {
    $this.call('Security.logoutCurrentUser', @())
  }
}
