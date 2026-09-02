# Back Up Saved Jobs

These examples create a read-only JSON backup of saved netLD or ThirdEye jobs.
Implementations are provided for [Python](Python/), [PowerShell](PowerShell/),
and [Node.js](nodeJS/).

The workflow:

1. Pages through `Scheduler.searchJobs` across one or more managed networks.
2. Uses each shallow record's `jobId` with `Scheduler.getJob`.
3. Deduplicates and sorts the complete definitions by `jobId`.
4. Writes a versioned backup document and a separate failure report.

The operation does not run, save, replace, or delete jobs. A future restore
example should treat identifiers and other read-only fields separately and must
provide explicit collision safeguards.

## Backup format

The main document has this shape:

```json
{
  "format": "logicvein-netld-saved-job-backup",
  "formatVersion": 1,
  "exportedAt": "2026-08-28T12:00:00Z",
  "networks": ["Default"],
  "complete": true,
  "jobCount": 1,
  "jobs": [
    {
      "jobId": 14,
      "jobName": "Example",
      "jobType": "Report",
      "managedNetworks": ["Default"],
      "jobParameters": {}
    }
  ]
}
```

The examples preserve the complete object returned by `Scheduler.getJob`, not
only the fields shown above. The server URL and API credentials are deliberately
excluded from the backup.

The saved `jobParameters` can nevertheless contain sensitive operational data,
including commands, device selectors, notification destinations, or credentials
entered into a job. Treat the backup as sensitive, restrict its filesystem
permissions, and do not commit it to source control. The default output names
are ignored by this repository.

Global jobs visible in the selected networks are retained. Duplicate job IDs
are written only once. The selected network names are metadata describing the
scope searched; they do not replace each job's own `managedNetworks` value.

## Failure report and exit status

If one complete job cannot be retrieved, the remaining jobs are still backed
up. The main document sets `complete` to `false`, and
`saved-job-failures.json` records the job ID, shallow job name, and error.

- Exit status `0`: complete backup
- Exit status `2`: backup written with one or more retrieval failures
- Exit status `1`: authentication, pagination, validation, or output failure

Both JSON documents are written through temporary files so a failed write does
not truncate an existing destination.

## Configuration

`NETLD_NETWORKS` accepts comma-separated managed network names.
`NETLD_JOB_PAGE_SIZE` controls pagination. Later result pages may report
`total=0`, so the scripts retain the total from the first page.

API keys belong only in an ignored environment file. TLS certificate
verification remains enabled.
