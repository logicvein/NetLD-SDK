# LiveAction LiveNX Inventory to ThirdEye

This integration compares the device inventory exported by LiveAction LiveNX
with the devices managed by LogicVein netLD or ThirdEye. It reports LiveNX
addresses that are missing from a selected LogicVein managed network and can
optionally start a preconfigured **Discover Devices** job for those addresses.

Choose an implementation:

- [Python 3](Python/)
- [PowerShell 7](PowerShell/)
- [Node.js 20](nodeJS/)

All three implementations use the same environment-variable names and follow
the same safety model. A normal run is read-only. Discovery occurs only when
the language-specific apply option is supplied.

## Validation Status

Each implementation has passed offline tests for CSV parsing, IPv4 and IPv6
normalization, discovery-job validation, and non-mutating job preparation. The
Python and Node.js suites also exercise inventory pagination and LiveNX token
placement.

The integration must still be validated end to end with the versions of LiveNX
and netLD or ThirdEye used at your site before production use.

## LiveNX API Endpoint

LiveNX exposes its REST API on TCP port 8093 in standard deployments, as listed
in LiveAction's
[Network Port Requirements](https://documentation.liveaction.com/LiveNX/LiveNX%20Hardening%20Document/LiveNX%20Hardening%20Document_2420a.1.09/).
Current LiveAction
[API-token guidance](https://documentation.liveaction.com/LiveNX/LiveNX%2025.1.0%20New%20Features/LiveNX%2025.1.0%20New%20Features.1.14/)
directs administrators to the Swagger page on their LiveNX system to obtain a
REST API token and inspect the available endpoints.

The historical integration used `/v1/devices/export/csv`. That path remains the
default for compatibility, but it is configurable because it is not documented
in LiveAction's public current manuals. Confirm the device-export path in your
LiveNX Swagger UI and set `LIVENX_DEVICE_EXPORT_PATH` if it differs.

## Common Configuration

Each language directory contains an `.env.example` with these settings:

- `LIVENX_BASE_URL`: LiveNX REST API URL, commonly using port 8093
- `LIVENX_API_TOKEN`: LiveNX token authorized to export device inventory
- `LIVENX_DEVICE_EXPORT_PATH`: CSV export path
- `LIVENX_REQUIRE_VENDOR`: whether rows without a `VENDOR` value are ignored
- `NETLD_BASE_URL`: netLD or ThirdEye base URL without `/rest`
- `NETLD_API_KEY`: LogicVein API key authorized to search inventory
- `NETLD_NETWORK`: managed network to compare and discover into
- `NETLD_DISCOVERY_JOB_NAME`: exact name of an existing Discover Devices job
- `NETLD_DEBUG`: enables LogicVein JSON-RPC request logging
- `REQUEST_TIMEOUT_SECONDS`: HTTP request timeout

The vendor requirement defaults to `true` to preserve the historical bridge's
behavior. Set it to `false` if the LiveNX export omits that field or vendorless
devices should be considered.

## Discovery Behavior

The integration reads every page of the LogicVein inventory and compares
canonical IPv4 and IPv6 addresses. Invalid CSV addresses are ignored.

When discovery is explicitly requested, the integration:

1. Finds the exact job named by `NETLD_DISCOVERY_JOB_NAME`.
2. Confirms that it has the `includedAddresses` parameter expected of a
   Discover Devices job.
3. Inserts the missing addresses into an in-memory copy of that job.
4. Calls `Scheduler.runNow` and prints the returned execution object.

The saved job itself is not modified, and the integration does not wait for the
discovery execution to finish.

## Safety Notes

- Use tokens with only the permissions required.
- Always review dry-run output before starting discovery.
- Test discovery in a non-production managed network first.
- All implementations verify HTTPS certificates.
- Tokens are sent in authorization headers, not URL query strings.
- For a private certificate authority, configure the runtime or operating
  system trust store rather than disabling certificate validation.
