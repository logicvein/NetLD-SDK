# Get netLD Device Interfaces

These examples retrieve the interfaces collected for one inventory device by
calling `Inventory.getDeviceInterfaces`.

The examples authenticate with an API key, preserve the netLD session, send a
JSON-RPC request to `POST /rest`, and print the returned interface list as
formatted JSON.

## Request Shape

```json
{
  "jsonrpc": "2.0",
  "method": "Inventory.getDeviceInterfaces",
  "params": {
    "network": "Default",
    "ipAddress": "10.95.1.40"
  },
  "id": "a-generated-guid"
}
```

Both `network` and `ipAddress` are required strings. The network identifies the
managed network containing the inventory device.

## Prerequisites

- A netLD or ThirdEye URL with API access enabled and a trusted HTTPS certificate
- A valid API key
- The device's managed network name and IPv4 or IPv6 address
- Interface data collected for the device
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

## Run with Python

From the `Python` directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install requests python-dotenv
python3 get_device_interfaces.py
```

## Run with Node.js

From the `nodeJS` directory:

```bash
npm install dotenv
node get-device-interfaces.mjs
```

## Run with PowerShell

From the `PowerShell` directory:

```powershell
pwsh ./get-device-interfaces.ps1
```

## Example Output

The result is a JSON array containing the interface data available for the
device:

```text
Login status=200
[
  {
    "name": "GigabitEthernet0/0/0",
    "description": "Uplink",
    "ipAddress": "10.95.1.40",
    "macAddress": "00:11:22:33:44:55",
    "adminStatus": "UP",
    "operStatus": "UP"
  }
]
```

The actual fields depend on the device adapter and the data collected by netLD.
Unavailable values may be returned as `null`.

## Troubleshooting

- **Empty interface list:** Confirm that `NETLD_NETWORK` and `NETLD_DEVICE_IP`
  identify the same inventory device and that interface data has been
  collected.
- **Connection failed:** Confirm that `NETLD_BASE_URL` is reachable and does not
  include `/rest`.
- **Login or API call redirected:** Confirm the server URL and API key.
- **TLS or certificate error:** Add the server certificate or its issuing CA to
  the client's trust store.
- **More detail needed:** Set `NETLD_DEBUG=1`. Debug output includes session
  cookies and response data, so handle it carefully.

## Files

Each language directory contains two files:

- A reusable client that handles authentication, cookies, JSON-RPC, and
  `Inventory.getDeviceInterfaces`
- A language-specific entry point that loads the device identity and prints the
  returned interface list

The client helper is example code, not a supported SDK package. Use it as a
starting point and adapt it to your team's automation standards.
