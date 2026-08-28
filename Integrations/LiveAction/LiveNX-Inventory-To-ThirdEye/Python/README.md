# LiveAction LiveNX Inventory Bridge

This integration compares the device inventory exported by LiveAction LiveNX
with the devices managed by LogicVein netLD or ThirdEye. It reports LiveNX
addresses that are missing from the selected LogicVein managed network and can
optionally start a preconfigured **Discover Devices** job for those addresses.

The default behavior is read-only. Discovery occurs only when the script is run
with `--apply`.

## Validation Status

The Python code has automated tests for CSV parsing and discovery-job
preparation. It must still be validated end to end with the versions of LiveNX
and netLD or ThirdEye used at your site before production use.

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

## Prerequisites

- Python 3.10 or later
- Network access to the LiveNX REST API and the LogicVein API
- A LiveNX REST API token authorized to export device inventory
- A netLD or ThirdEye API key authorized to search inventory
- Trusted HTTPS certificates for both systems
- For discovery, an existing netLD or ThirdEye **Discover Devices** job

The integration verifies HTTPS certificates. For a private certificate
authority, add the CA to the operating system trust store or set the standard
`REQUESTS_CA_BUNDLE` environment variable to its certificate bundle.

## Install

From this directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
cp .env.example .env
```

On Windows, activate the virtual environment with:

```powershell
.\.venv\Scripts\Activate.ps1
```

Edit `.env` with the URLs, tokens, managed network, and discovery-job name for
your environment. Do not commit `.env` or expose either API token.

`LIVENX_REQUIRE_VENDOR=true` preserves the historical behavior of considering
only LiveNX CSV rows with a populated `VENDOR` field. Set it to `false` if your
export omits that field or if vendorless devices should be included.

## Preview Missing Devices

Run the integration without arguments:

```bash
python3 live_nx_to_thirdeye.py
```

The script downloads the LiveNX device CSV, reads all pages of the selected
LogicVein inventory, and prints the addresses that appear only in LiveNX. It
does not start discovery.

## Start Discovery

After reviewing the preview, run:

```bash
python3 live_nx_to_thirdeye.py --apply
```

The script finds the exact job named by `NETLD_DISCOVERY_JOB_NAME`, confirms
that it contains the `includedAddresses` parameter expected of a Discover
Devices job, inserts the missing addresses into a copy of that job, and calls
`Scheduler.runNow`. The saved job itself is not modified.

The script starts the job and prints the execution object; it does not wait for
discovery to finish.

## Safety Notes

- Use an API key and LiveNX token with only the permissions required.
- Always review the dry-run output before using `--apply`.
- Test discovery in a non-production managed network first.
- The integration never disables certificate validation.
- API tokens are sent in authorization headers, not URL query strings.
- Invalid IP addresses in the LiveNX CSV are ignored.

## Run the Automated Tests

```bash
python3 -m unittest discover -s tests -v
```

These tests do not contact LiveNX or a LogicVein system and do not start jobs.
