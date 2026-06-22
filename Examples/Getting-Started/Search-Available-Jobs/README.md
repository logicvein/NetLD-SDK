# Search Available netLD Jobs

These examples search the jobs available in one or more managed networks by
calling `Scheduler.searchJobs`.

The examples authenticate with an API key, preserve the netLD session, send a
JSON-RPC request to `POST /rest`, and print the complete paged job search result
as formatted JSON.

For an introduction to the API, see
[Getting Started with the netLD API](https://logicvein.com/netld-api-get-started/).
The complete method reference is available in the
[netLD SDK API documentation](https://netld-sdk.readthedocs.io/en/latest/Scheduler.html).

## Request Shape

```json
{
  "jsonrpc": "2.0",
  "method": "Scheduler.searchJobs",
  "params": {
    "pageData": {
      "offset": 0,
      "jobData": [],
      "pageSize": 100,
      "total": 1
    },
    "networks": [
      "Default"
    ],
    "sortColumn": "",
    "descending": false
  },
  "id": "a-generated-guid"
}
```

`networks` is always an array, even when searching only one managed network. An
empty `sortColumn` lets the server use its default job ordering.

## Prerequisites

- A netLD or ThirdEye URL with API access enabled and a trusted HTTPS certificate
- A valid API key
- The name of a managed network, such as `Default`
- Permission to view jobs available in that network
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
NETLD_JOB_OFFSET=0
NETLD_JOB_PAGE_SIZE=100
NETLD_JOB_SORT_COLUMN=
NETLD_JOB_DESCENDING=false
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
python3 search_available_jobs.py
```

On Windows, activate the virtual environment with:

```powershell
.\.venv\Scripts\Activate.ps1
```

## Run with Node.js

From the `nodeJS` directory:

```bash
npm install dotenv
node search-available-jobs.mjs
```

## Run with PowerShell

From the `PowerShell` directory:

```powershell
pwsh ./search-available-jobs.ps1
```

To use an environment file stored elsewhere:

```powershell
pwsh ./search-available-jobs.ps1 -EnvPath /path/to/netld.env
```

## Example Output

The result contains paging information and a `jobData` array:

```text
Login status=200
{
  "offset": 0,
  "pageSize": 100,
  "total": 5,
  "jobData": [
    {
      "jobId": 14,
      "jobName": "Devel",
      "description": "",
      "managedNetworks": [
        "Default"
      ],
      "jobType": "Playbook",
      "approvalRequired": true,
      "jobParameters": {},
      "disabled": false,
      "accessLimited": false,
      "executing": false
    }
  ]
}
```

The actual output contains up to `pageSize` jobs and is not limited to these
fields. Review fields such as `approvalRequired`, `approvalStatus`, `disabled`,
`accessLimited`, and `executing` before treating a returned job as runnable.

## Shallow Job Records

`Scheduler.searchJobs` is intended for finding jobs. The API documentation
describes its returned `JobData` objects as shallow records that may not contain
the full parameters required to run a job.

Use the returned `jobId` with `Scheduler.getJob` to retrieve the complete
`JobData` before passing it to `Scheduler.runNow`.

## Paging and Sorting

- Increase `NETLD_JOB_OFFSET` by `NETLD_JOB_PAGE_SIZE` to retrieve the next
  page.
- When `offset + pageSize` is greater than or equal to `total`, there are no
  more results.
- Set `NETLD_JOB_SORT_COLUMN` to a `JobData` field when explicit sorting is
  needed.
- `NETLD_JOB_DESCENDING` controls ascending or descending order.

The reusable client methods accept multiple networks even though the entry
points read one `NETLD_NETWORK` value.

## Troubleshooting

- **No jobs returned:** Confirm the selected network has jobs and the API user
  has permission to view them.
- **Job cannot be executed:** Retrieve the full job with `Scheduler.getJob`,
  then review approval, disabled, access, and execution-state fields.
- **Connection failed:** Confirm that `NETLD_BASE_URL` is reachable and does not
  include `/rest`.
- **Login or API call redirected:** Confirm the server URL and API key.
  Redirects commonly mean the request is being sent through an SSO or browser
  login path instead of directly to the API.
- **TLS or certificate error:** These examples verify HTTPS certificates. Add
  the server certificate or its issuing CA to the client's trust store.
- **More detail needed:** Set `NETLD_DEBUG=1` and rerun the example. Debug output
  includes session cookies and request/response data, so handle it carefully.

## Files

Each language directory contains two files:

- A small reusable netLD client that handles authentication, cookies, JSON-RPC,
  errors, and `Scheduler.searchJobs`
- A language-specific entry point that loads configuration and prints the
  returned job page

The client helper is example code, not a supported SDK package. Use it as a
starting point and adapt it to your team's automation standards.
