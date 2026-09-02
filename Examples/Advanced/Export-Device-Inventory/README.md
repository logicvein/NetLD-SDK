# Export Device Inventory

These examples export all devices returned by `Inventory.search` to UTF-8 CSV
or JSON. Implementations are provided for [Python](Python/),
[PowerShell](PowerShell/), and [Node.js](nodeJS/).

The examples:

1. Authenticate to netLD or ThirdEye with an API key.
2. Search one or more managed networks.
3. Retrieve every result page, rather than only the first page.
4. Write a consistent set of documented device fields to CSV or JSON.
5. Replace the destination only after the complete export succeeds.

The export is read-only. It does not contact managed devices or modify the
inventory.

## CSV columns

The CSV contains these fields:

```text
network,ipAddress,hostname,adapterId,deviceType,hardwareVendor,model,
serialNumber,softwareVendor,osVersion,backupStatus,complianceState,lastBackup,
lastTelemetry,memoSummary,custom1,custom2,custom3,custom4,custom5
```

`network` is included because the same IP address can appear in more than one
managed network. `lastBackup` and `lastTelemetry` are Unix epoch timestamps in
milliseconds, as returned by the API.

## JSON output

Set `NETLD_OUTPUT_FORMAT=json` or use the language-specific `--format json` or
`-Format json` option. JSON output is an array of device objects containing the
same 20 fields as the CSV export:

```json
[
  {
    "network": "Default",
    "ipAddress": "192.0.2.10",
    "hostname": "router-1",
    "adapterId": "CiscoIOS",
    "complianceState": 0,
    "lastBackup": 1787932800000,
    "memoSummary": null
  }
]
```

The actual object also contains the remaining documented fields. Unlike CSV,
JSON preserves numeric values and `null` values as native JSON types.

Set `NETLD_OUTPUT_FORMAT` to `csv` or `json`. If `NETLD_OUTPUT_FILE` is empty or
unset, the default filename follows the format: `inventory.csv` or
`inventory.json`. An explicit output filename takes precedence.

## Filtering and pagination

Set `NETLD_NETWORKS` to a comma-separated list of managed network names. By
default, `NETLD_SEARCH_SCHEME=ipAddress` and `NETLD_SEARCH_QUERY` is empty, which
selects all devices in those networks. Other search schemes and queries follow
the `Inventory.search` documentation.

`NETLD_PAGE_SIZE` controls the requested page size. The scripts retain the
`total` reported on the first page because some releases return zero for that
field on later pages. They continue until the number of returned records reaches
that first-page total. A short or empty intermediate page is treated as an error
rather than silently producing an incomplete export.

## Output safety

Each implementation writes to a temporary file in the destination directory.
The requested output file is replaced only after all API pages and records have
been written successfully. Existing output therefore remains intact if a later
page fails.

API keys belong only in the untracked `.env` file. Do not put credentials in a
script, URL, or committed settings file. TLS certificate verification remains
enabled.
