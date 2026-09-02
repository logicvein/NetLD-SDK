# Page Through netLD API Results

These examples demonstrate how to retrieve every page of a netLD or ThirdEye
API result. They call `Configuration.retrieveSnapshotChangeLog`, read the
`offset`, `pageSize`, and `total` values returned by the server, and continue
until every configuration change log has been collected.

For API documentation, see the
[LogicVein API manual](https://docs.logicvein.com/manuals/logicvein-api/).

## Request Shape

The first request starts at offset zero:

```json
{
  "jsonrpc": "2.0",
  "method": "Configuration.retrieveSnapshotChangeLog",
  "params": {
    "network": "Default",
    "ipAddress": "192.0.2.10",
    "pageData": {
      "offset": 0,
      "pageSize": 10
    }
  },
  "id": "a-generated-guid"
}
```

A response includes the current page and the total number of matching records:

```json
{
  "jsonrpc": "2.0",
  "id": "a-generated-guid",
  "result": {
    "offset": 0,
    "pageSize": 10,
    "total": 61,
    "changeLogs": []
  }
}
```

For 61 results and a page size of 10, the examples request offsets 0, 10, 20,
30, 40, 50, and 60. The final page contains one record. Each example advances
the offset by the number of records actually returned and stops when the next
offset reaches the total reported with the first page. Some product versions
return zero in the `total` field on later pages, so the examples retain the
largest total reported during the request sequence.

## Prerequisites

- A netLD or ThirdEye URL with API access enabled and a trusted HTTPS certificate
- A valid API key
- Configuration change history for the target device
- One of:
  - Python 3.10 or later
  - Node.js 20 or later
  - PowerShell 7 or later

## Configure the Example

Choose a language directory, copy `.env.example` to `.env`, and set values for
your system:

```dotenv
NETLD_BASE_URL=https://netld.example.com
NETLD_API_KEY=replace-with-your-api-key
NETLD_NETWORK=Default
NETLD_DEVICE_IP=192.0.2.10
NETLD_PAGE_SIZE=10
NETLD_DEBUG=0
```

`NETLD_BASE_URL` must not include `/rest`. Do not commit the `.env` file or
otherwise expose the API key. `NETLD_PAGE_SIZE` must be a positive integer.

## Run with Python

From the `Python` directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 page_through_results.py
```

On Windows, activate the environment with
`.\.venv\Scripts\Activate.ps1`.

## Run with Node.js

From the `nodeJS` directory:

```bash
cp .env.example .env
node --env-file=.env page-through-results.mjs
```

## Run with PowerShell

From the `PowerShell` directory:

```powershell
pwsh ./page-through-results.ps1
```

To use an environment file stored elsewhere:

```powershell
pwsh ./page-through-results.ps1 -EnvPath /path/to/netld.env
```

## Output

Each request prints a short progress message. After the last page, the example
prints a JSON object containing the collected count and the complete
`changeLogs` array.

```text
Login status=200
Fetched 10 records at offset 0 (10 of 61)
...
Fetched 1 records at offset 60 (61 of 61)
{
  "total": 61,
  "changeLogs": [
    ...
  ]
}
```

The helper clients are example code, not supported SDK packages. Use them as a
starting point and adapt them to your team's automation standards.
