# Get netLD Device Hardware

These examples retrieve the hardware inventory for one device by calling
`Inventory.getDeviceHardware` with its IP address and managed network.

The examples authenticate with an API key, preserve the netLD session, send a
JSON-RPC request to `POST /rest`, and print the returned list of `Hardware`
objects as formatted JSON.

For an introduction to the API, see
[Getting Started with the netLD API](https://logicvein.com/netld-api-get-started/).
The complete method reference is available in the
[netLD SDK API documentation](https://netld-sdk.readthedocs.io/en/latest/).

## Request Shape

```json
{
  "jsonrpc": "2.0",
  "method": "Inventory.getDeviceHardware",
  "params": {
    "ipAddress": "10.95.1.40",
    "network": "Default"
  },
  "id": "a-generated-guid"
}
```

Both `ipAddress` and `network` are required strings.

## Prerequisites

- A netLD or ThirdEye URL with API access enabled and a trusted HTTPS certificate
- A valid API key
- The device's managed network name and IPv4 or IPv6 address
- Hardware data collected for the device
- One of:
  - Python 3.10 or later
  - Node.js 20 or later
  - PowerShell 7 or later

## Configure the Example

Choose a language directory and create a `.env` file in that directory:

```dotenv
NETLD_BASE_URL=https://netld.example.com
NETLD_API_KEY=replace-with-your-api-key
NETLD_DEVICE_IP=10.95.1.40
NETLD_NETWORK=Default
NETLD_DEBUG=0
```

`NETLD_BASE_URL` must be the server URL without `/rest`. Do not commit the
`.env` file or otherwise expose the API key.

`NETLD_BASE_URL` and `NETLD_API_KEY` are required. The example IP address
defaults to `10.95.1.40`, and the network defaults to `Default`. Set
`NETLD_DEBUG=1` to print request and response JSON while troubleshooting.

## Run with Python

From the `Python` directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install requests python-dotenv
python3 get_device_hardware.py
```

On Windows, activate the virtual environment with:

```powershell
.\.venv\Scripts\Activate.ps1
```

## Run with Node.js

From the `nodeJS` directory:

```bash
npm install dotenv
node get-device-hardware.mjs
```

## Run with PowerShell

From the `PowerShell` directory:

```powershell
pwsh ./get-device-hardware.ps1
```

To use an environment file stored elsewhere:

```powershell
pwsh ./get-device-hardware.ps1 -EnvPath /path/to/netld.env
```

## Example Output

The result is a JSON array. Each item describes an asset such as a chassis,
memory module, CPU, card, or power supply:

```text
Login status=200
[
  {
    "hardwareId": 19,
    "deviceId": 5,
    "assetType": "CHASSIS",
    "make": "Aruba",
    "modelNumber": "7010",
    "serialNumber": "CG0046315",
    "captureTime": 1768769166313,
    "latest": true,
    "cardParentId": -1
  },
  {
    "hardwareId": 20,
    "deviceId": 5,
    "assetType": "MEMORY",
    "description": "Supervisor Card System : 1 GB",
    "captureTime": 1768769166313,
    "latest": true,
    "cardParentId": 19
  }
]
```

The actual output is not limited to these fields. Fields whose values are not
available may be returned as `null`. A child asset's `cardParentId` references
its parent asset's `hardwareId`; a top-level asset commonly has a
`cardParentId` of `-1`.

## Troubleshooting

- **Empty hardware list:** Confirm that `NETLD_DEVICE_IP` and `NETLD_NETWORK`
  identify the same inventory record and that hardware data has been collected
  for the device.
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
  errors, and `Inventory.getDeviceHardware`
- A language-specific entry point that loads configuration and prints the
  returned hardware list

The client helper is example code, not a supported SDK package. Use it as a
starting point and adapt it to your team's automation standards.
