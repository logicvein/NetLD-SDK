# PowerShell

PowerShell 7 or later is required.

```powershell
Copy-Item .env.example .env
pwsh ./archive-job-execution-outputs.ps1
```

To use an environment file stored elsewhere:

```powershell
pwsh ./archive-job-execution-outputs.ps1 -EnvPath /path/to/netld.env
```

The script exits with status 0 on success, 1 for a fatal error, or 2 when one
or more selected executions could not be archived.
