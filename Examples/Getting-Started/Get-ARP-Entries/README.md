# Get netLD ARP Entries

These examples retrieve ARP entries collected from devices by calling
`Telemetry.getArpEntries`.

The method searches across devices in one or more managed networks and returns
only ARP entries whose IP address is contained in the `networkAddress` filter.
The examples print the complete paged result as formatted JSON.

## Request Shape

```json
{
  "jsonrpc": "2.0",
  "method": "Telemetry.getArpEntries",
  "params": {
    "pageData": {
      "offset": 0,
      "pageSize": 100,
      "total": 0
    },
    "networkAddress": "10.95.1.0/24",
    "sort": "ipAddress",
    "descending": true,
    "networks": [
      "Default"
    ]
  },
  "id": "a-generated-guid"
}
```

## Filters

`networkAddress` and `networks` filter different things:

| Parameter | Filters |
| --- | --- |
| `networkAddress` | The IP addresses contained in the returned ARP entries |
| `networks` | The netLD managed networks whose devices are searched |

For example, `networkAddress: "10.95.1.0/24"` with `networks: ["Default"]`
finds ARP entries for hosts in that subnet that were learned by devices in the
`Default` managed network.

## Prerequisites

- A netLD or ThirdEye URL with API access enabled and a trusted HTTPS certificate
- A valid API key
- Telemetry and ARP data collected from devices in the selected managed network
- One of:
  - Python 3.10 or later
  - Node.js 20 or later
  - PowerShell 7 or later

## Configure the Example

Choose a language directory and create a `.env` file in that directory:

```dotenv
NETLD_BASE_URL=https://netld.example.com
NETLD_API_KEY=replace-with-your-api-key
NETLD_ARP_NETWORK_ADDRESS=10.95.1.0/24
NETLD_NETWORK=Default
NETLD_ARP_OFFSET=0
NETLD_ARP_PAGE_SIZE=100
NETLD_ARP_SORT=ipAddress
NETLD_ARP_DESCENDING=true
NETLD_DEBUG=0
```

`NETLD_ARP_NETWORK_ADDRESS` accepts an address or CIDR filter. `NETLD_NETWORK`
selects the managed network to search.

`NETLD_BASE_URL` must be the server URL without `/rest`. Do not commit the
`.env` file or otherwise expose the API key.

## Run with Python

From the `Python` directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install requests python-dotenv
python3 get_arp_entries.py
```

## Run with Node.js

From the `nodeJS` directory:

```bash
npm install dotenv
node get-arp-entries.mjs
```

## Run with PowerShell

From the `PowerShell` directory:

```powershell
pwsh ./get-arp-entries.ps1
```

## Example Output

The result is a `DeviceArpPageData` object. Each entry identifies both the
learned host and the device that supplied the ARP entry:

```text
Login status=200
{
  "offset": 0,
  "pageSize": 100,
  "total": 2,
  "arpEntries": [
    {
      "device": "10.95.1.1",
      "managedNetwork": "Default",
      "ipAddress": "10.95.1.40",
      "macAddress": "00:11:22:33:44:55",
      "interfaceName": "Vlan1"
    }
  ]
}
```

## Paging and Sorting

- Increase `NETLD_ARP_OFFSET` by `NETLD_ARP_PAGE_SIZE` to retrieve the next
  page.
- When `offset + pageSize` is greater than or equal to `total`, there are no
  more results.
- `NETLD_ARP_SORT` selects a `DeviceArpTableEntry` field such as `ipAddress`.
- `NETLD_ARP_DESCENDING` controls ascending or descending order.

The reusable client methods accept multiple managed networks even though the
entry points read one `NETLD_NETWORK` value.

## Troubleshooting

- **No ARP entries returned:** Confirm that telemetry has collected ARP data,
  the managed network is correct, and the `networkAddress` filter contains the
  expected host addresses.
- **Unexpected source device:** The `device` field identifies the device whose
  ARP table contained the entry; it is not the learned host's IP address.
- **Connection failed:** Confirm that `NETLD_BASE_URL` is reachable and does not
  include `/rest`.
- **Login or API call redirected:** Confirm the server URL and API key.
- **TLS or certificate error:** Add the server certificate or its issuing CA to
  the client's trust store.
- **More detail needed:** Set `NETLD_DEBUG=1`. Debug output includes session
  cookies and response data, so handle it carefully.

## Files

Each language directory contains two files:

- A reusable client that handles authentication, cookies, JSON-RPC, paging, and
  `Telemetry.getArpEntries`
- A language-specific entry point that loads filters and prints the ARP page

The client helper is example code, not a supported SDK package. Use it as a
starting point and adapt it to your team's automation standards.
