# Get netLD Device Details

These examples retrieve the complete inventory record for one device by calling
`Inventory.getDevice` with its managed network and IP address.

The examples authenticate with an API key, preserve the netLD session, send a
JSON-RPC request to `POST /rest`, and print the returned `Device` object as
formatted JSON. If the device does not exist, `Inventory.getDevice` returns
`null` and the example prints `Device not found`.

For an introduction to the API, see
[Getting Started with the netLD API](https://logicvein.com/netld-api-get-started/).
The complete method reference is available in the
[netLD SDK API documentation](https://netld-sdk.readthedocs.io/en/latest/).

## Request Shape

```json
{
  "jsonrpc": "2.0",
  "method": "Inventory.getDevice",
  "params": {
    "network": "Default",
    "ipAddress": "10.95.1.40"
  },
  "id": "a-generated-guid"
}
```

Both `network` and `ipAddress` are required strings. Unlike
`Inventory.search`, the network parameter is not a list.

## Prerequisites

- A netLD or ThirdEye URL with API access enabled and a trusted HTTPS certificate
- A valid API key
- The device's managed network name and IPv4 or IPv6 address
- One of:
  - Python 3.10 or later
  - Node.js 20 or later
  - PowerShell 7 or later

## Configure the Example

Choose a language directory and create a `.env` file in that directory:

```dotenv
NETLD_BASE_URL=https://netld.example.com
NETLD_API_KEY=replace-with-your-api-key
NETLD_NETWORK=Default
NETLD_DEVICE_IP=10.95.1.40
NETLD_DEBUG=0
```

`NETLD_BASE_URL` must be the server URL without `/rest`. Do not commit the
`.env` file or otherwise expose the API key.

`NETLD_BASE_URL` and `NETLD_API_KEY` are required. The network defaults to
`Default`, and the example IP address defaults to `10.95.1.40`. Set
`NETLD_DEBUG=1` to print request and response JSON while troubleshooting.

## Run with Python

From the `Python` directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install requests python-dotenv
python3 get_device_details.py
```

On Windows, activate the virtual environment with:

```powershell
.\.venv\Scripts\Activate.ps1
```

## Run with Node.js

From the `nodeJS` directory:

```bash
npm install dotenv
node get-device-details.mjs
```

## Run with PowerShell

From the `PowerShell` directory:

```powershell
pwsh ./get-device-details.ps1
```

To use an environment file stored elsewhere:

```powershell
pwsh ./get-device-details.ps1 -EnvPath /path/to/netld.env
```

## Example Output

The complete response includes identity, platform, backup, compliance,
telemetry, lifecycle, custom-field, and metadata details when available:

```text
Login status=200
{
  "ipAddress": "10.95.1.40",
  "hostname": "aruba7010.testdev.lwpca.fm",
  "adapterId": "Aruba::ArubaOS",
  "deviceType": "Wireless Controller",
  "hardwareVendor": "Aruba",
  "model": "7010",
  "osVersion": "8.12.0.1",
  "backupStatus": "SUCCESS",
  "sysLocation": "Lab Rack, Carleton Place, ON",
  "network": "Default",
  "serialNumber": "CG0046315"
}
```

The actual output is not limited to these fields. Fields whose values are not
available may be returned as `null`.

## Troubleshooting

- **Device not found:** Confirm that `NETLD_NETWORK` and `NETLD_DEVICE_IP`
  identify the same inventory record. The network name is required even when an
  IP address is unique.
- **Connection failed:** Confirm that `NETLD_BASE_URL` is reachable from the
  machine running the example and does not include `/rest`.
- **Login or API call redirected:** Confirm the server URL and API key.
  Redirects commonly mean the request is being sent through an SSO or browser
  login path instead of directly to the API.
- **TLS or certificate error:** These examples verify HTTPS certificates. Add
  the netLD server certificate or its issuing CA to the client's trust store.
- **More detail needed:** Set `NETLD_DEBUG=1` and rerun the example. Debug output
  includes session cookies and request/response data, so handle it carefully.

## Files

Each language directory contains two files:

- A small reusable netLD client that handles authentication, cookies, JSON-RPC,
  errors, and `Inventory.getDevice`
- A language-specific entry point that loads configuration and prints the
  returned device details

The client helper is example code, not a supported SDK package. Use it as a
starting point and adapt it to your team's automation standards.
