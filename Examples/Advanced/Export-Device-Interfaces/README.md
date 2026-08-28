# Export Device Interfaces

These examples export the interface data already collected for every matching
inventory device. Implementations are provided for [Python](Python/),
[PowerShell](PowerShell/), and [Node.js](nodeJS/).

The workflow is read-only:

1. Call `Inventory.search` across one or more managed networks.
2. Retain the first page's `total` and retrieve every inventory page.
3. Call `Inventory.getDeviceInterfaces` once for each returned device.
4. Write one CSV row for each interface.
5. Record any per-device lookup failures in a companion CSV.

The APIs return stored inventory and telemetry data; running the export does not
log in to or otherwise contact managed devices. Because interface retrieval is
one API call per device, large inventories can take substantially longer than a
device inventory export.

## Interface CSV

The main CSV contains:

```text
network,deviceIpAddress,hostname,interfaceId,interfaceIndex,name,ifName,type,
description,comment,macAddress,mtu,speed,adminUp,vrfName,ipAddresses
```

`ipAddresses` contains zero or more `address/prefix` values separated by
semicolons. Keeping `network` and `deviceIpAddress` in every row makes interface
records unambiguous when the same management address exists in multiple managed
networks.

Interface fields can vary by device adapter. Missing values are written as
empty CSV fields. Boolean values such as `adminUp` are written as lowercase
`true` or `false` consistently across all three implementations.

## Failure CSV and exit status

Failure rows contain `network`, `deviceIpAddress`, `hostname`, and `error`. A
device with no collected interfaces is not a failure and produces no interface
rows.

Successful device results are preserved when another device lookup fails. The
scripts return exit status `2` after writing both CSVs when one or more device
lookups fail. Authentication, inventory pagination, or output-file failures
return exit status `1` and leave existing output files intact.

## Configuration

`NETLD_NETWORKS` accepts comma-separated managed network names. An empty
`NETLD_SEARCH_QUERY` with the default `ipAddress` scheme selects every device in
those networks. `NETLD_PAGE_SIZE` controls inventory pagination.

The output files are replaced only after their complete temporary files have
been written. API keys belong only in an ignored environment file, and TLS
certificate verification remains enabled.
