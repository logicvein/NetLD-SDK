# PowerShell

## Prerequisites

- PowerShell 7 or later
- Network access, API tokens, certificates, and a discovery job as described in
  the [integration README](../README.md)

Copy `.env.example` to `.env` and enter the values for your environment.

Preview missing devices without starting discovery:

```powershell
pwsh ./live-nx-to-thirdeye.ps1
```

After reviewing the preview, start discovery with:

```powershell
pwsh ./live-nx-to-thirdeye.ps1 -Apply
```

To use an environment file stored elsewhere:

```powershell
pwsh ./live-nx-to-thirdeye.ps1 -EnvPath /path/to/live-nx.env
```

Run the offline tests with:

```powershell
pwsh ./tests/Test-LiveNXBridge.ps1
```
