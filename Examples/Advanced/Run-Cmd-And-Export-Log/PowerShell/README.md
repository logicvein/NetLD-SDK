# PowerShell implementation

```powershell
Copy-Item .env.example .env
Copy-Item commands.txt.example commands.txt
pwsh ./run-cmd-and-export-log.ps1
```

Set `NETLD_RUN_JOB=true` only after reviewing the preview. Run tests with:

```powershell
pwsh -NoProfile -File tests/Test-RunCmdAndExportLog.ps1
```

