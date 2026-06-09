# Get netLD Configuration History

These examples retrieve configuration revision history by calling
`Configuration.retrieveConfigHistory`.

The examples authenticate with an API key, preserve the netLD session, send a
JSON-RPC request to `POST /rest`, and print the complete paged history result as
formatted JSON.

For an introduction to the API, see
[Getting Started with the netLD API](https://logicvein.com/netld-api-get-started/).
The complete method reference is available in the
[netLD SDK API documentation](https://netld-sdk.readthedocs.io/en/latest/).

## Request Shape

```json
{
  "jsonrpc": "2.0",
  "method": "Configuration.retrieveConfigHistory",
  "params": {
    "pageData": {
      "offset": 0,
      "pageSize": 100,
      "total": 0,
      "configHistoryItems": []
    },
    "networks": [
      "Default"
    ],
    "scheme": "ipAddress",
    "data": "10.95.1.40",
    "sortColumn": "session",
    "descending": true
  },
  "id": "a-generated-guid"
}
```

The request searches one or more managed networks using a search `scheme` and
matching `data`. These examples default to retrieving the newest configuration
history for one IP address.

## Prerequisites

- A netLD or ThirdEye URL with API access enabled and a trusted HTTPS certificate
- A valid API key
- Configuration history collected for the target device
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
NETLD_HISTORY_SCHEME=ipAddress
NETLD_HISTORY_DATA=10.95.1.40
NETLD_HISTORY_OFFSET=0
NETLD_HISTORY_PAGE_SIZE=100
NETLD_HISTORY_SORT_COLUMN=session
NETLD_HISTORY_DESCENDING=true
NETLD_DEBUG=0
```

`NETLD_BASE_URL` must be the server URL without `/rest`. Do not commit the
`.env` file or otherwise expose the API key.

Only `NETLD_BASE_URL` and `NETLD_API_KEY` are required. The remaining variables
use the values shown above by default. Set `NETLD_DEBUG=1` to print request and
response JSON while troubleshooting.

## Run with Python

From the `Python` directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install requests python-dotenv
python3 get_configuration_history.py
```

On Windows, activate the virtual environment with:

```powershell
.\.venv\Scripts\Activate.ps1
```

## Run with Node.js

From the `nodeJS` directory:

```bash
npm install dotenv
node get-configuration-history.mjs
```

## Run with PowerShell

From the `PowerShell` directory:

```powershell
pwsh ./get-configuration-history.ps1
```

To use an environment file stored elsewhere:

```powershell
pwsh ./get-configuration-history.ps1 -EnvPath /path/to/netld.env
```

## Example Output

The result contains paging information and a `configHistoryItems` array:

```text
Login status=200
{
  "offset": 0,
  "pageSize": 100,
  "total": 4,
  "configHistoryItems": [
    {
      "ipAddress": "10.95.1.40",
      "managedNetwork": "Default",
      "hostname": "aruba7010.testdev.lwpca.fm",
      "path": "/running-config",
      "author": "chindy@lwpca.net",
      "adapterId": "Aruba::ArubaOS",
      "lastChanged": 1769174469000,
      "prevChange": 1769174053000,
      "mimeType": "text/plain",
      "size": 44496,
      "previousRevisionExists": true
    }
  ]
}
```

The actual output contains up to `pageSize` history items. Timestamps such as
`lastChanged` and `prevChange` are Unix epoch milliseconds. A `null`
`prevChange` and `previousRevisionExists: false` indicate that no earlier
revision is available for that configuration path.

## Paging and Filtering

- Increase `NETLD_HISTORY_OFFSET` by `NETLD_HISTORY_PAGE_SIZE` to retrieve the
  next page.
- When `offset + pageSize` is greater than or equal to `total`, there are no
  more results.
- `NETLD_NETWORK` selects the managed network to search.
- `NETLD_HISTORY_SCHEME` and `NETLD_HISTORY_DATA` define the history filter.
- `NETLD_HISTORY_SORT_COLUMN` and `NETLD_HISTORY_DESCENDING` control result
  ordering.

The reusable client methods accept multiple networks even though the entry
points read one `NETLD_NETWORK` value.

## Troubleshooting

- **No history items:** Confirm that the network, scheme, and data identify a
  device with collected configuration history.
- **Unexpected order:** Confirm `NETLD_HISTORY_SORT_COLUMN` and
  `NETLD_HISTORY_DESCENDING`. The defaults request newest-first results.
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
  errors, and `Configuration.retrieveConfigHistory`
- A language-specific entry point that loads configuration and prints the
  returned history page

The client helper is example code, not a supported SDK package. Use it as a
starting point and adapt it to your team's automation standards.
