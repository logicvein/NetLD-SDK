# PowerShell

Requires PowerShell 7 or later.

```powershell
Copy-Item .env.example .env
./backup-saved-jobs.ps1
```

For repository testing, use `./backup-saved-jobs.ps1 -EnvPath ../../../.env.netld`.
Run tests with `./tests/Test-BackupSavedJobs.ps1`.
