# Export Hardware Inventory

This example exports the hardware components already collected for matching netLD or ThirdEye devices. It combines the documented `Inventory.search` and `Inventory.getDeviceHardware` JSON-RPC methods and does not start a discovery or contact managed devices.

Implementations are provided for [Python](Python/), [Node.js](nodeJS/), and [PowerShell](PowerShell/). All three support CSV or JSON output, inventory pagination, multiple managed networks, search filtering, atomic output replacement, and a separate CSV report for devices whose hardware lookup failed.

## Output

Each component record includes its managed network, device address, hostname, and adapter ID plus the hardware attributes returned by the API: asset type, make, model and serial numbers, part and FRU numbers, firmware and hardware versions, slot and CPU information, lifecycle dates, capture time, and parent-card relationship.

Set `NETLD_OUTPUT_FORMAT=csv` or `json`. JSON retains native values such as numbers, booleans, and nulls; CSV provides a stable column set suitable for spreadsheets. The default files are `hardware-inventory.csv` and `hardware-failures.csv`.

Use `NETLD_NETWORKS` for a comma-separated managed-network list and `NETLD_SEARCH_SCHEME` plus `NETLD_SEARCH_QUERY` to restrict the devices. A lookup failure does not discard successful records, but the process exits with status 2 after writing both files. Fatal setup and inventory errors exit with status 1.

Hardware results are stored inventory data and may be empty for devices whose adapter does not collect component details or which have not completed a successful collection.
