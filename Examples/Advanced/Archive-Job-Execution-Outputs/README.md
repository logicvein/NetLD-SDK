# Archive Job Execution Outputs

This example incrementally archives output from completed netLD or ThirdEye job
executions. It preserves the useful workflow from the historical Perl, Ruby,
and Python 2 `exportJobHistory` examples without retaining their insecure or
version-specific implementation choices.

Implementations are provided for [Python](Python/), [Node.js](nodeJS/), and
[PowerShell](PowerShell/). See the LogicVein API manual for the
[Scheduler API](https://docs.logicvein.com/manuals/logicvein-api/scheduler/),
[`Plugins.getExecutionDetails`](https://docs.logicvein.com/manuals/logicvein-api/plugins/#plugins.getexecutiondetails),
and the
[execution-detail URL endpoint](https://docs.logicvein.com/manuals/logicvein-api/plugins/#execution-detail-url-endpoint).

## What It Does

1. Authenticates with an API key and preserves the server session.
2. Pages through `Scheduler.searchExecutions`, newest execution first.
3. Selects executions newer than the saved `endTime` watermark.
4. Filters the results by job type and, optionally, exact job name.
5. Calls `Plugins.getExecutionDetails` for each selected execution.
6. Downloads each device's output from `/servlet/pluginDetail`.
7. Writes output, detail metadata, execution metadata, run status, and archive
   state atomically.

The default `NETLD_JOB_TYPE` is `Script Tool Job`, matching the behavior of the
legacy examples. Set it to an empty value to include every execution type that
provides plugin details.

## Safe Initial Run

`NETLD_INITIAL_MODE` defaults to `latest`. On the first run, the example records
the latest completed execution as its baseline and downloads nothing. Later
runs archive newly completed matching executions.

Set `NETLD_INITIAL_MODE=all` only when you intentionally want to backfill every
matching execution returned by the server. A mature system may contain
thousands of executions and substantial output data.

The state records every execution ID observed at the watermark timestamp. This
prevents duplicate timestamps from causing missed or repeated executions. The
watermark advances only after every selected execution is archived
successfully. A partial failure exits with status 2 and is retried later.

## Configuration

Copy the `.env.example` in the selected language directory to `.env` and edit
it:

```dotenv
NETLD_BASE_URL=https://netld.example.com
NETLD_API_KEY=replace-with-your-api-key
NETLD_OUTPUT_DIR=job-execution-outputs
NETLD_STATE_FILE=job-execution-output-state.json
NETLD_RUN_REPORT_FILE=job-execution-output-run.json
NETLD_PAGE_SIZE=100
NETLD_INITIAL_MODE=latest
NETLD_SEARCH_SCHEME=
NETLD_SEARCH_DATA=
NETLD_JOB_TYPE=Script Tool Job
NETLD_JOB_NAME=
```

`NETLD_BASE_URL` must not include `/rest`. Do not commit the `.env` file or
otherwise expose the API key.

`NETLD_SEARCH_SCHEME` and `NETLD_SEARCH_DATA` are passed directly to
`Scheduler.searchExecutions`. Leave both empty to search all executions. Set
`NETLD_JOB_NAME` to require an exact job-name match after the search results are
returned.

## Output

The archive layout is:

```text
job-execution-outputs/
  YYYY-MM-DD/
    <execution-id>_<job-name>/
      execution.metadata.json
      <detail-id>_<network>_<device>.log
      <detail-id>_<network>_<device>.metadata.json
```

Job output may contain commands, configurations, usernames, addresses,
credentials, and other sensitive operational information. Store the archive
accordingly.

## Compatibility Note

The Python, Node.js, and PowerShell implementations were validated end to end
against a ThirdEye Suite lab on September 2, 2026. Each implementation archived
the same completed Script Tool execution, retrieved all 29 detail records, and
produced identical output files with no failures.

The historical scripts called `Scheduler.getExecutionData`; the current system
tested for this port supports the named-parameter `Scheduler.searchExecutions`
method used here. Neither execution-history method appears in the currently
published Scheduler API chapter, so treat this portion of the example as
version-sensitive and verify it against the system where it will run.

The current Plugins API chapter documents `Plugins.getExecutionDetails` and
the `/servlet/pluginDetail` endpoint, but also warns that the Plugins API may
change incompatibly in the next major release. Test the complete workflow
against the netLD or ThirdEye version where it will run.

The helper clients are example code, not supported SDK packages. Adapt them to
your organization's automation, retention, and security requirements.
