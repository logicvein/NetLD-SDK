# PowerShell

Requires PowerShell 7 or later.

```powershell
Copy-Item .env.example .env
./export-device-interfaces.ps1
```

For repository testing, point directly to the shared environment file:

```powershell
./export-device-interfaces.ps1 -EnvPath ../../../.env.netld
```

Run tests with `./tests/Test-ExportDeviceInterfaces.ps1`.
