# PowerShell

Requires PowerShell 7 or newer and has no module dependencies.

Copy `.env.example` to `.env`, set the ThirdEye URL and API key, and run:

```powershell
./export-thirdeye-violations.ps1
```

To keep credentials in another location:

```powershell
./export-thirdeye-violations.ps1 -EnvPath /path/to/.env
```

See the [parent README](../README.md) for configuration, output, state, and API
compatibility details.
