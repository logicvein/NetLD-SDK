# Deprecated PRTG Configuration Change Probe

These Windows PowerShell scripts are retained only for historical inspection. They are not maintained, have not been validated against current PRTG or netLD releases, and are strongly recommended **not** to be used.

The original implementation passes a username and password in the request URL and globally disables TLS certificate validation. Those practices are unsafe for a production deployment.

Use the maintained [PRTG Configuration Change Probe](../../../Integrations/PRTG/Config-Change-Probe/) instead. It provides current PowerShell and Python 3 implementations with API-key authentication, TLS verification, atomic state handling, tests, and deployment instructions.

## Historical files

- `NLD-Configuration-Sensor.ps1` is the original PRTG sensor entry point.
- `NLDService.ps1` is its original netLD JSON-RPC helper.

