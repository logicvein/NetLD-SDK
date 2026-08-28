# PowerShell

Requires PowerShell 7. Copy `.env.example` to `.env`, set the connection values, and run:

```powershell
./archive-configuration-revisions.ps1
```

Use `-EnvFile /path/to/file` to load another environment file.

Run the offline tests with `pwsh ./tests/archive-configuration-revisions.Tests.ps1`.
