# PRTG Configuration Change Probe

This integration checks netLD for device configurations changed since the previous successful run. It reports the number of unique changed devices to PRTG and launches a saved netLD report job once for each affected managed network.

Two implementations are provided:

- [PowerShell](PowerShell/) for an **EXE/Script Advanced** sensor. It returns the classic PRTG XML format and uses `NotifyChanged` when changes are found.
- [Python 3](Python/) for a **Script v2** sensor. It returns PRTG Script v2 JSON schema version 3 and, by default, places the sensor in a warning state when changes are found.

Deploy only one implementation for a given netLD instance and scope. Both implementations can launch report jobs, so running both against the same scope would duplicate that work.

## How it works

On its first run, the probe records the current time as its starting watermark. It does not replay historical changes. On later runs it:

1. Calls `Configuration.retrieveConfigsSince` with the saved watermark.
2. Optionally restricts the results to configured managed networks.
3. Counts each changed device IP address once, even if the device has multiple changed configurations.
4. Launches the configured saved report job once per affected managed network. The job receives the affected devices and the observed change-time range.
5. Advances the watermark only after all required report jobs have started successfully.

This last step is intentional: if netLD or a report job fails, the probe reports the error and retries the same change window on its next run.

## netLD prerequisites

- A netLD API key with permission to retrieve configuration changes, search and retrieve saved jobs, and run the selected job.
- A saved report job named `PRTG Realtime Changes` by default. Its job parameters must include:
  - `input.start_date`
  - `input.end_date`
  - `ipResolutionData`
- Network access from the PRTG probe system to the netLD REST endpoint.
- A trusted TLS certificate for the netLD endpoint. Certificate verification remains enabled.

The report-job name, report-job network, monitored networks, request timeout, and state-file path are configurable in each implementation's `.env` file.

## PRTG deployment

Follow the implementation-specific README for installation. The PowerShell entry point and module belong in PRTG's `Custom Sensors\EXEXML` directory and are selected through an EXE/Script Advanced sensor. The Python entry point belongs directly in `Custom Sensors\scripts` and is selected through a Script v2 sensor.

Give each deployed sensor its own writable state-file path. PRTG runs custom scripts using the probe service account, so that account needs read access to the script and `.env` file and write access to the state-file directory.

For PRTG's current sensor requirements, see Paessler's documentation for [EXE/Script Advanced and custom XML output](https://www.paessler.com/manuals/prtg/custom_sensors) and the [Script v2 sensor](https://www.paessler.com/manuals/prtg/script_v2_sensor).

## Historical version

The original Windows PowerShell implementation is retained under [`Examples/Deprecated/PRTG-Config-Change-Probe`](../../../Examples/Deprecated/PRTG-Config-Change-Probe/) for historical inspection. It contains embedded credentials and disables TLS certificate validation, and should not be deployed.
