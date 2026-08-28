# Archive Configuration Revisions

This example makes a filesystem archive of the configuration revisions already stored by netLD or ThirdEye. It uses only the documented `Inventory.search`, `Configuration.retrieveConfigHistory`, and `Configuration.retrieveRevision` JSON-RPC methods. It does not use the private `inventoryServlet` export or the older undocumented `retrieveConfigsSince` method.

Implementations are provided for [Python](Python/), [Node.js](nodeJS/), and [PowerShell](PowerShell/). All three use the same environment settings, directory layout, state format, and run-report format.

## What it writes

Each revision is stored under `configuration-archive/<network>/<device>/` as its decoded `.txt` or `.bin` content plus a `.metadata.json` sidecar. File names include the revision timestamp, a safe form of the configuration path, and a short path hash. The sidecar retains the original network, device, path, history record, and revision metadata.

The tool also maintains:

- `configuration-archive-state.json`, a per-device watermark used for incremental runs.
- `configuration-archive-run.json`, a report listing archived revisions and failures from the latest run.

These files and the archive are ignored by Git. Device configurations may contain credentials or other sensitive material; protect the output directory as you would protect a device backup.

## Initial and incremental runs

`NETLD_INITIAL_MODE=latest` is the default. On the first run, it archives only the newest stored revision of each configuration path for each matching device. This establishes a useful baseline without downloading years of history. Set `NETLD_INITIAL_MODE=all` before the first run to backfill every stored revision instead.

Later runs retrieve revisions newer than the saved watermark. History is requested newest-first, so an incremental scan stops after it passes that watermark. If any revision for a device fails, that device's watermark is not advanced and the failed work is retried on the next run. A partial-failure run exits with status 2; a fatal setup or request error exits with status 1.

Use `NETLD_SEARCH_SCHEME` and `NETLD_SEARCH_QUERY` to restrict the inventory selection. For example, setting `NETLD_SEARCH_QUERY=192.0.2.10` with the default `ipAddress` scheme limits a test to that address. Inventory and history calls are paginated.

## Configuration

Start with the `.env.example` in the implementation directory. Required settings are `NETLD_BASE_URL`, `NETLD_API_KEY`, and `NETLD_NETWORKS`. The optional output paths are resolved relative to the implementation directory.

Run the tool periodically with your operating system's scheduler or another automation service. Retain or copy the state file along with the archive; deleting it deliberately starts a new initial run.
