# PowerShell PRTG Configuration Change Probe

This version is intended for PRTG's **EXE/Script Advanced** sensor and emits classic PRTG XML.

## Install

1. Copy `config-change-probe.ps1` and `ConfigChangeProbe.psm1` to the PRTG probe system under:

   ```text
   C:\Program Files (x86)\PRTG Network Monitor\Custom Sensors\EXEXML
   ```

2. Copy `.env.example` to the same directory as `config-change-probe.env`, then set `NETLD_BASE_URL` and `NETLD_API_KEY`.
3. In PRTG, add an **EXE/Script Advanced** sensor and select `config-change-probe.ps1`.
4. Set the sensor's **Parameters** field to:

   ```text
   -EnvPath "C:\Program Files (x86)\PRTG Network Monitor\Custom Sensors\EXEXML\config-change-probe.env"
   ```

5. Ensure the PRTG probe service account can write to the directory configured by `PRTG_STATE_PATH`.

The first run establishes the current time as the watermark and reports zero changes. When later changes are found, the result includes `NotifyChanged`, which can trigger a PRTG change notification.

## Configuration

`NETLD_NETWORKS` is a comma-separated allowlist of managed-network names. Leave it blank to include all networks. `NETLD_REPORT_JOB_NETWORK` identifies the managed network in which the saved job is defined; it does not limit the networks checked for device changes.

Relative state-file paths are resolved from this script directory. Use a separate state file for every separately scoped sensor.

## Test

The module's transformation and output functions can be tested without netLD:

```powershell
pwsh -NoProfile -File tests/Test-ConfigChangeProbe.ps1
```
