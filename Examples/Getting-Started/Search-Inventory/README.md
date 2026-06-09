# Search the netLD Inventory

These examples show the basic flow for calling the netLD JSON-RPC API with an
API key:

1. Send a bearer token to `GET /rest` to authenticate and establish a session.
2. Preserve the session cookies.
3. Send an `Inventory.search` JSON-RPC request to `POST /rest`.
4. Print the IP address, hostname, and adapter ID for each matching device.

For an introduction to the API, see
[Getting Started with the netLD API](https://logicvein.com/netld-api-get-started/).
The complete method reference is available in the
[netLD SDK API documentation](https://netld-sdk.readthedocs.io/en/latest/).

## Prerequisites

- A netLD or ThirdEye URL with API access enabled and a trusted HTTPS certificate
- A valid API key
- The name of a managed network, such as `Default`
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
NETLD_SEARCH_SCHEME=ipAddress
NETLD_SEARCH_QUERY=10.95.1.0/24
NETLD_DEBUG=0
```

`NETLD_BASE_URL` must be the server URL without `/rest`. Do not commit the
`.env` file or otherwise expose the API key.

The first two variables are required. The remaining variables are optional and
use the values shown above by default. Set `NETLD_DEBUG=1` to print request and
response JSON while troubleshooting.

## Run with Python

From the `Python` directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install requests python-dotenv
python3 search_inventory.py
```

On Windows, activate the virtual environment with:

```powershell
.\.venv\Scripts\Activate.ps1
```

## Run with Node.js

From the `nodeJS` directory:

```bash
npm install dotenv
node search-inventory.mjs
```

## Run with PowerShell

From the `PowerShell` directory:

```powershell
pwsh ./search-inventory.ps1
```

To use an environment file stored elsewhere:

```powershell
pwsh ./search-inventory.ps1 -EnvPath /path/to/netld.env
```

The `NetLDExampleClient.ps1` helper is dot-sourced automatically by the search
script.

## Expected Output

A successful request first prints the login status, followed by the matching
devices:

```text
Login status=200
Returned 3 of 3 matching devices
10.95.1.12      core-switch-01                 Cisco::IOS
10.95.1.13      core-switch-02                 Cisco::IOS
10.95.1.44      branch-fw-01                   PaloAlto::PANOS
```

## Customize the Search

Set `NETLD_SEARCH_SCHEME` and `NETLD_SEARCH_QUERY` to change the search. Common
examples include:

| Search | Scheme | Query example |
| --- | --- | --- |
| IP address or subnet | `ipAddress` | `10.95.1.0/24` |
| Interface IP address or subnet | `interfaceIpAddress` | `10.95.1.0/24` |
| Hostname | `hostname` | `core-*` |
| Adapter ID/vendor | `vendor` | `Cisco::IOS` |
| Serial number | `serial` | `ABC123*` |
| Inventory status | `status` | `S` |
| Tag | `tag` | `datacenter AND core` |

The reusable client in each language directory also accepts multiple schemes
and queries. Schemes are sent as a comma-separated string, and the corresponding
queries are separated by newline characters, as required by `Inventory.search`.
The helper adds the required trailing newline to the search text and always
passes the network parameter as a list, even when searching only one network.

Results are requested in pages. These examples retrieve the first 100 matches,
sorted by IP address in ascending order. Use the client helper directly to
change the page size, offset, sort column, or sort direction.

## Troubleshooting

- **Connection failed:** Confirm that `NETLD_BASE_URL` is reachable from the
  machine running the example and does not include `/rest`.
- **Login or API call redirected:** Confirm the server URL and API key.
  Redirects commonly mean the request is being sent through an SSO or browser
  login path instead of directly to the API.
- **TLS or certificate error:** These examples verify HTTPS certificates. Add
  the netLD server certificate or its issuing CA to the client's trust store.
- **No devices returned:** Confirm `NETLD_NETWORK`, the selected search scheme,
  and the query value in the netLD web interface.
- **More detail needed:** Set `NETLD_DEBUG=1` and rerun the example. Debug output
  includes session cookies and request/response data, so handle it carefully.

## Files

Each language directory contains two files:

- A small reusable netLD client that handles authentication, cookies, JSON-RPC,
  errors, and inventory searching
- A language-specific search entry point that loads configuration and prints
  results

The client helper is example code, not a supported SDK package. Use it as a
starting point and adapt it to your team's automation standards. To call other
netLD API methods, add methods beside the inventory search wrapper and reuse the
same login and JSON-RPC plumbing.
