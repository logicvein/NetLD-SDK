# Get a netLD Configuration Revision

These examples retrieve and decode one device configuration revision using a
two-call workflow:

1. Call `Configuration.retrieveConfigHistory` for the device.
2. Select the newest history item matching a configuration path.
3. Pass the selected item's `managedNetwork`, `ipAddress`, `path`, and
   `lastChanged` values to `Configuration.retrieveRevision`.
4. Decode the returned Base64 `content` when its MIME type is text.

This avoids manually copying a configuration path and timestamp from a previous
history response.

## API Flow

First, request the device's configuration history:

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

The examples select the first history item whose `path` matches
`NETLD_CONFIG_PATH`. Because the history request is sorted descending, this is
the newest matching revision.

The selected item supplies the next request:

```json
{
  "jsonrpc": "2.0",
  "method": "Configuration.retrieveRevision",
  "params": {
    "network": "Default",
    "ipAddress": "10.95.1.40",
    "configPath": "/running-config",
    "timestamp": 1769174469000
  },
  "id": "a-generated-guid"
}
```

Field mapping:

| History item | Revision request |
| --- | --- |
| `managedNetwork` | `network` |
| `ipAddress` | `ipAddress` |
| `path` | `configPath` |
| `lastChanged` | `timestamp` |

## Base64 Content

The API documentation defines the returned revision's `content` field as a
Base64-encoded string.

The examples validate the Base64 data and decode it as UTF-8 only when
`mimeType` starts with `text/`. For binary MIME types, metadata is printed but
the encoded content is not dumped to the terminal.

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
NETLD_DEVICE_IP=10.95.1.40
NETLD_CONFIG_PATH=/running-config
NETLD_DEBUG=0
```

`NETLD_CONFIG_PATH` defaults to `/running-config`. Set it to another path, such
as `/startup-config`, to retrieve that configuration's newest revision.

`NETLD_BASE_URL` must be the server URL without `/rest`. Do not commit the
`.env` file or otherwise expose the API key.

## Run with Python

From the `Python` directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install requests python-dotenv
python3 get_configuration_revision.py
```

## Run with Node.js

From the `nodeJS` directory:

```bash
npm install dotenv
node get-configuration-revision.mjs
```

## Run with PowerShell

From the `PowerShell` directory:

```powershell
pwsh ./get-configuration-revision.ps1
```

## Example Output

```text
Login status=200
Revision metadata:
{
  "lastChanged": 1769174469000,
  "path": "/running-config",
  "author": "chindy@lwpca.net",
  "mimeType": "text/plain",
  "size": 44496,
  "prevChange": 1769174053000
}
Decoded revision content:
hostname aruba7010
...
```

## Selection Behavior

- History is requested newest-first using `sortColumn: "session"` and
  `descending: true`.
- The examples select the first item matching `NETLD_CONFIG_PATH`.
- The examples search the first 100 history items. Increase the page size in
  the entry point if the desired path is not present.
- To retrieve a specific older revision, select a different history item before
  calling `retrieveRevision`.

## Troubleshooting

- **No matching configuration history item:** Confirm `NETLD_NETWORK`,
  `NETLD_DEVICE_IP`, and `NETLD_CONFIG_PATH`.
- **Invalid Base64:** The server returned content that does not match the
  documented revision format. Enable debug output and inspect the response.
- **Binary content:** Binary revisions are intentionally not printed. Adapt the
  example to write decoded bytes to a controlled destination when needed.
- **Connection failed:** Confirm that `NETLD_BASE_URL` is reachable and does not
  include `/rest`.
- **Login or API call redirected:** Confirm the server URL and API key.
- **More detail needed:** Set `NETLD_DEBUG=1`. Debug output includes session
  cookies and response data, including encoded configuration content, so handle
  it carefully.

## Files

Each language directory contains two files:

- A reusable client that handles authentication, history lookup,
  `Configuration.retrieveRevision`, and Base64 decoding
- A language-specific entry point that selects and prints the newest matching
  text revision

The client helper is example code, not a supported SDK package. Use it as a
starting point and adapt it to your team's automation standards.
