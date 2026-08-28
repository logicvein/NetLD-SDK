# Create a Device

These examples add one device to a netLD or ThirdEye inventory with `Inventory.createDevice`, then retrieve it with `Inventory.getDevice` to verify the result.

Implementations are provided for [Python](Python/), [PowerShell](PowerShell/), and [Node.js](nodeJS/).

> [!CAUTION]
> Creating a device changes the product inventory. Preview mode is the default. Review the managed network, IP address, and adapter ID before setting `NETLD_CREATE_DEVICE=true`.

## API flow

The create request uses named JSON-RPC parameters:

```json
{
  "jsonrpc": "2.0",
  "method": "Inventory.createDevice",
  "params": {
    "network": "Default",
    "ipAddress": "192.0.2.10",
    "adapterId": "Cisco::IOS"
  },
  "id": "a-generated-request-id"
}
```

`Inventory.createDevice` returns `null` when creation succeeds and an error message otherwise. After a successful create call, the example calls `Inventory.getDevice` and confirms that the returned IP address and adapter ID match the request.

## Prerequisites

- A netLD or ThirdEye URL with API access enabled and a trusted HTTPS certificate
- An API key allowed to view and create inventory devices
- An existing managed-network name
- A currently unused management IPv4 or IPv6 address
- A valid LogicVein adapter ID for the device platform
- Python 3.10+, PowerShell 7+, or Node.js 20+

## Configure

Copy the selected implementation's `.env.example` to `.env`:

```dotenv
NETLD_BASE_URL=https://netld.example.com
NETLD_API_KEY=replace-with-your-api-key
NETLD_NETWORK=Default
NETLD_DEVICE_IP=192.0.2.10
NETLD_ADAPTER_ID=Cisco::IOS
NETLD_CREATE_DEVICE=false
```

Do not commit `.env` or expose the API key. Confirm the adapter ID from a comparable managed device or your product's adapter list; an incorrect adapter prevents successful device communication and backup.

## Preview

Run the selected implementation with `NETLD_CREATE_DEVICE=false`. It validates and prints the exact parameters without contacting the server.

## Create and verify

After reviewing the preview, set:

```dotenv
NETLD_CREATE_DEVICE=true
```

Run the example again. It:

1. Authenticates with the API key.
2. Stops if the device already exists in that managed network.
3. Calls `Inventory.createDevice`.
4. Retrieves the new record with `Inventory.getDevice`.
5. Prints the verified device record.

The example deliberately leaves the created device in inventory. Removing it is a separate administrative decision; use `Inventory.deleteDevice` only when deletion is intended.

## Validation

The Python, PowerShell, and Node.js implementations were each validated end to end against a ThirdEye Suite lab on August 28, 2026. Each implementation created the same temporary TEST-NET device record, retrieved and verified it, and exited successfully. The test record was deleted and confirmed absent between implementations; no test inventory remains.

## Run

### Python

```shell
cd Python
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
cp .env.example .env
python3 create_device.py
```

### PowerShell

```powershell
cd PowerShell
Copy-Item .env.example .env
pwsh ./create-device.ps1
```

### Node.js

```shell
cd nodeJS
npm install
cp .env.example .env
node create-device.mjs
```
