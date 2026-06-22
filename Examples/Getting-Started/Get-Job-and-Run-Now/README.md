# Get a netLD Job and Run It Now

These examples demonstrate the complete workflow for finding and executing an
existing job:

1. Call `Scheduler.searchJobs` and select one shallow job record by exact name.
2. Pass its `jobId` to `Scheduler.getJob`.
3. Review the complete returned `JobData`.
4. Pass that full `JobData` to `Scheduler.runNow`.

> [!CAUTION]
> `Scheduler.runNow` starts a real job that may connect to or change managed
> devices. These examples run in preview mode unless `NETLD_RUN_JOB=true` is
> explicitly set.

The examples require exactly one job whose name matches `NETLD_JOB_NAME`. They
stop without executing if no match or multiple matches are found.

## API Flow

Search for available jobs:

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

Retrieve the full job using the selected ID:

```json
{
  "jsonrpc": "2.0",
  "method": "Scheduler.getJob",
  "params": {
    "jobId": 14
  },
  "id": "a-generated-guid"
}
```

Execute the full `JobData` returned by `Scheduler.getJob`:

```json
{
  "jsonrpc": "2.0",
  "method": "Scheduler.runNow",
  "params": {
    "jobData": {
      "jobName": "CH IOS Show Commands",
      "managedNetworks": [
        "AWS-CLAB"
      ],
      "jobType": "Script Tool Job",
      "description": "Interactive script tool execution",
      "jobParameters": {
        "input.showIpRoute": "true",
        "tool": "org.ziptie.tools.cisco.ios.showtool",
        "ipResolutionScheme": "ipCsv",
        "ipResolutionData": "\"172.18.19.5@AWS-CLAB\"",
        "backupOnCompletion": "false"
      }
    }
  },
  "id": "a-generated-guid"
}
```

Do not pass the shallow search result directly to `Scheduler.runNow`.
`Scheduler.getJob` supplies the complete job parameters required for execution.

## Prerequisites

- A netLD or ThirdEye URL with API access enabled and a trusted HTTPS certificate
- A valid API key with permission to view and execute the selected job
- The exact name and managed network of an existing job
- One of:
  - Python 3.10 or later
  - Node.js 20 or later
  - PowerShell 7 or later

## Configure Preview Mode

Choose a language directory and create a `.env` file in that directory:

```dotenv
NETLD_BASE_URL=https://netld.example.com
NETLD_API_KEY=replace-with-your-api-key
NETLD_NETWORK=AWS-CLAB
NETLD_JOB_NAME=CH IOS Show Commands
NETLD_JOB_PAGE_SIZE=100
NETLD_RUN_JOB=false
NETLD_DEBUG=0
```

`NETLD_JOB_NAME` must exactly match one available job. The example searches the
first page, so increase `NETLD_JOB_PAGE_SIZE` when necessary.

Keep `NETLD_RUN_JOB=false` while reviewing the selected full `JobData`.
`NETLD_BASE_URL` must be the server URL without `/rest`. Do not commit the
`.env` file or otherwise expose the API key.

## Run the Preview

### Python

From the `Python` directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install requests python-dotenv
python3 get_job_and_run_now.py
```

### Node.js

From the `nodeJS` directory:

```bash
npm install dotenv
node get-job-and-run-now.mjs
```

### PowerShell

From the `PowerShell` directory:

```powershell
pwsh ./get-job-and-run-now.ps1
```

## Execute the Job

After reviewing the full `JobData` printed by preview mode, set:

```dotenv
NETLD_RUN_JOB=true
```

Run the same entry point again. The example will repeat the search and
`Scheduler.getJob` lookup, then call `Scheduler.runNow` and print the returned
`ExecutionData`.

```text
Selected job "CH IOS Show Commands" with ID 14:
{
  "jobName": "CH IOS Show Commands",
  "managedNetworks": [
    "AWS-CLAB"
  ],
  "jobType": "Script Tool Job",
  "jobParameters": {
    "input.showIpRoute": "true",
    "tool": "org.ziptie.tools.cisco.ios.showtool",
    "ipResolutionScheme": "ipCsv",
    "ipResolutionData": "\"172.18.19.5@AWS-CLAB\"",
    "backupOnCompletion": "false"
  }
}
Execution started:
{
  "id": 123,
  "jobName": "CH IOS Show Commands",
  "managedNetworks": [
    "AWS-CLAB"
  ],
  "executor": "api-user",
  "startTime": 1781023915867,
  "endTime": null,
  "status": null
}
```

The returned `ExecutionData` confirms that execution was requested. These
examples do not wait for completion or poll execution status.

## Job Parameters

The examples execute the complete job exactly as returned by
`Scheduler.getJob`. To run a job against different devices or with different
inputs, update the relevant `jobParameters` after retrieval and review the
result before calling `Scheduler.runNow`.

Job parameter values are generally strings, including values representing
booleans or numbers.

## Troubleshooting

- **No available job found:** Confirm `NETLD_JOB_NAME`, `NETLD_NETWORK`, and the
  API user's permissions. Increase `NETLD_JOB_PAGE_SIZE` if needed.
- **Multiple jobs found:** Use a unique job name before running this example.
- **Job was not executed:** Preview mode is the default. Set
  `NETLD_RUN_JOB=true` only after reviewing the selected job.
- **Approval required or execution rejected:** Review the job's approval,
  disabled, access, and execution-state fields and the API user's permissions.
- **Connection failed:** Confirm that `NETLD_BASE_URL` is reachable and does not
  include `/rest`.
- **Login or API call redirected:** Confirm the server URL and API key.
  Redirects commonly mean the request is being sent through an SSO or browser
  login path instead of directly to the API.
- **TLS or certificate error:** Add the server certificate or its issuing CA to
  the client's trust store.

## Files

Each language directory contains two files:

- A small reusable client that handles authentication, cookies, JSON-RPC,
  `Scheduler.searchJobs`, `Scheduler.getJob`, and `Scheduler.runNow`
- A guarded entry point that selects, previews, and optionally executes a job

The client helper is example code, not a supported SDK package. Use it as a
starting point and adapt it to your team's automation and approval standards.
