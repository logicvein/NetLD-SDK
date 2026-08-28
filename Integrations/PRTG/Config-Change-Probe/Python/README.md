# Python 3 PRTG Configuration Change Probe

This version is intended for PRTG's **Script v2** sensor and emits schema-version 3 JSON.

## Install

1. Install Python 3 for the PRTG probe service account and install the dependencies:

   ```powershell
   py -3 -m pip install -r requirements.txt
   ```

2. Copy `config_change_probe.py` directly to the PRTG probe system's scripts directory:

   ```text
   C:\Program Files (x86)\PRTG Network Monitor\Custom Sensors\scripts
   ```

3. Copy `.env.example` to the same directory as `config-change-probe.env`, then set `NETLD_BASE_URL` and `NETLD_API_KEY`.
4. In PRTG, add a **Script v2** sensor and select `config_change_probe.py`.
5. Set the sensor's **Parameters** field to:

   ```text
   --env-path "C:\Program Files (x86)\PRTG Network Monitor\Custom Sensors\scripts\config-change-probe.env"
   ```

6. Ensure the PRTG probe service account can write to the directory configured by `PRTG_STATE_PATH`.

The first run establishes the current time as the watermark and reports zero changes. By default, later changes return PRTG status `warning`; set `PRTG_WARNING_ON_CHANGE=false` if the sensor should remain OK and only expose the change count.

## Configuration

`NETLD_NETWORKS` is a comma-separated allowlist of managed-network names. Leave it blank to include all networks. `NETLD_REPORT_JOB_NETWORK` identifies the managed network in which the saved job is defined; it does not limit the networks checked for device changes.

Relative state-file paths are resolved from this script directory. Use a separate state file for every separately scoped sensor.

## Test

Run the unit tests without a PRTG or netLD installation:

```shell
python3 -m unittest discover -s tests -v
```

The current Script v2 output schema is documented by Paessler in its [JSON schema reference](https://helpdesk.paessler.com/en/support/solutions/articles/76000063370-where-can-i-find-the-json-schema-against-which-the-script-v2-sensor-validates-my-output-).
