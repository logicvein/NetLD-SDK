# PowerShell

Requires PowerShell 7 or later.

```powershell
Copy-Item .env.example .env
./export-device-inventory.ps1
```

Edit `.env` before running the script. `NETLD_NETWORKS` accepts a comma-separated
list such as `Default,Lab`. The completed CSV replaces the destination only after
every page has been retrieved successfully.

Run the unit tests with:

```powershell
./tests/Test-ExportDeviceInventory.ps1
```
