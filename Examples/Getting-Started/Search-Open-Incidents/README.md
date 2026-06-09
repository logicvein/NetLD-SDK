# Search Open ThirdEye Incidents

These examples search open and working incidents by calling
`Incidents.searchIncidents`.

> [!IMPORTANT]
> This API returns incident data only from ThirdEye. A netLD server may accept
> the request and return HTTP `200 OK` with an empty or `null` response. The
> examples detect that response and explain that the method is ThirdEye-only.

The examples authenticate with an API key, preserve the ThirdEye session, send
a JSON-RPC request to `POST /rest`, and print the complete paged incident result
as formatted JSON.

The complete method reference is available in the
[netLD SDK API documentation](https://netld-sdk.readthedocs.io/en/latest/Incidents.html).

## Request Shape

```json
{
  "jsonrpc": "2.0",
  "method": "Incidents.searchIncidents",
  "params": {
    "pageData": {
      "offset": 0,
      "total": 0,
      "pageSize": 100,
      "incidents": []
    },
    "queries": [
      "status=OPEN,WORKING",
      "networks=Default"
    ],
    "sortColumn": "modified",
    "descending": false
  },
  "id": "a-generated-guid"
}
```

The first query includes incidents whose status is `OPEN` or `WORKING`. The
second limits results to the selected managed network.

## Prerequisites

- A ThirdEye URL with API access enabled and a trusted HTTPS certificate
- A valid ThirdEye API key
- The name of a managed network, such as `Default`
- One of:
  - Python 3.10 or later
  - Node.js 20 or later
  - PowerShell 7 or later

## Configure the Example

Choose a language directory and create a `.env` file in that directory:

```dotenv
NETLD_BASE_URL=https://thirdeye.example.com
NETLD_API_KEY=replace-with-your-api-key
NETLD_NETWORK=Default
NETLD_INCIDENT_OFFSET=0
NETLD_INCIDENT_PAGE_SIZE=100
NETLD_INCIDENT_SORT_COLUMN=modified
NETLD_INCIDENT_DESCENDING=false
NETLD_DEBUG=0
```

The shared `NETLD_*` variable names match the other getting-started examples
and are also used for ThirdEye. `NETLD_BASE_URL` must be the server URL without
`/rest`. Do not commit the `.env` file or otherwise expose the API key.

Only `NETLD_BASE_URL` and `NETLD_API_KEY` are required. The remaining variables
use the values shown above by default. Set `NETLD_DEBUG=1` to print request and
response JSON while troubleshooting.

## Run with Python

From the `Python` directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install requests python-dotenv
python3 search_open_incidents.py
```

On Windows, activate the virtual environment with:

```powershell
.\.venv\Scripts\Activate.ps1
```

## Run with Node.js

From the `nodeJS` directory:

```bash
npm install dotenv
node search-open-incidents.mjs
```

## Run with PowerShell

From the `PowerShell` directory:

```powershell
pwsh ./search-open-incidents.ps1
```

To use an environment file stored elsewhere:

```powershell
pwsh ./search-open-incidents.ps1 -EnvPath /path/to/thirdeye.env
```

## Example ThirdEye Output

```text
Login status=200
{
  "offset": 0,
  "total": 1,
  "incidents": [
    {
      "incidentId": 1,
      "network": "Default",
      "summary": "No response from node c9200",
      "severity": "WARNING",
      "priority": "MEDIUM",
      "status": "OPEN",
      "resolution": "PENDING",
      "modified": 1781023915867,
      "nodes": 18,
      "triggers": 1,
      "occurrences": 497285,
      "traits": [
        "icmp"
      ]
    }
  ],
  "pageSize": 100
}
```

The actual output is not limited to these fields. Timestamps such as `created`,
`modified`, and `resolved` are Unix epoch milliseconds.

## Example netLD Output

When pointed at netLD, the examples handle the successful empty or `null`
response and print:

```text
Login status=200
No incident data returned. Incidents.searchIncidents is available only on ThirdEye.
```

## Paging and Sorting

- Increase `NETLD_INCIDENT_OFFSET` by `NETLD_INCIDENT_PAGE_SIZE` to retrieve the
  next page.
- When `offset + pageSize` is greater than or equal to `total`, there are no
  more results.
- `NETLD_INCIDENT_SORT_COLUMN` and `NETLD_INCIDENT_DESCENDING` control result
  ordering.

## Troubleshooting

- **No incident data returned:** Confirm that `NETLD_BASE_URL` points to
  ThirdEye, not netLD.
- **No incidents in the result:** Confirm the selected network has incidents
  with an `OPEN` or `WORKING` status.
- **Connection failed:** Confirm that `NETLD_BASE_URL` is reachable and does not
  include `/rest`.
- **Login or API call redirected:** Confirm the server URL and API key.
  Redirects commonly mean the request is being sent through an SSO or browser
  login path instead of directly to the API.
- **TLS or certificate error:** These examples verify HTTPS certificates. Add
  the ThirdEye server certificate or its issuing CA to the client's trust store.
- **More detail needed:** Set `NETLD_DEBUG=1` and rerun the example. Debug output
  includes session cookies and request/response data, so handle it carefully.

## Files

Each language directory contains two files:

- A small reusable ThirdEye client that handles authentication, cookies,
  JSON-RPC, empty responses, errors, and `Incidents.searchIncidents`
- A language-specific entry point that loads configuration and prints the
  returned incident page

The client helper is example code, not a supported SDK package. Use it as a
starting point and adapt it to your team's automation standards.
