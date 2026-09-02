# PowerShell

Requires PowerShell 7 or later.

```powershell
Copy-Item .env.example .env
./export-device-inventory.ps1
```

Edit `.env` before running the script. `NETLD_NETWORKS` accepts a comma-separated
list such as `Default,Lab`. The completed output replaces the destination only after
every page has been retrieved successfully.

Use JSON or the shared repository test environment with:

```powershell
./export-device-inventory.ps1 -Format json -EnvPath ../../../.env.netld
```

Run the unit tests with:

```powershell
./tests/Test-ExportDeviceInventory.ps1
```
