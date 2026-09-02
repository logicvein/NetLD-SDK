# Run Commands and Export Device Logs

This example turns the useful idea behind the historical `Jp1_ShowCommand_Template.py` script into a current, product-native workflow. It does not require Hitachi JP1 or any other external scheduler.

The example:

1. Builds an ad hoc `Script Tool Job` for one managed device.
2. Shows the complete job without running it by default.
3. Calls `Scheduler.runNow` only when execution is explicitly enabled.
4. Polls `Scheduler.getExecutionDataById` until the job finishes or times out.
5. Calls `Plugins.getExecutionDetails` and downloads each device's text output from `/servlet/pluginDetail`.
6. Writes a timestamped UTF-8 log file per returned device record.

Implementations are provided for [Python](Python/), [PowerShell](PowerShell/), and [Node.js](nodeJS/).

> [!CAUTION]
> The configured commands are sent to a real managed network device. Preview mode is the default. Review the generated job and use read-only commands before setting `NETLD_RUN_JOB=true`.

## Prerequisites

- A netLD or ThirdEye URL with API access enabled and a trusted HTTPS certificate
- An API key allowed to execute script-tool jobs and retrieve their results
- A device already managed in the selected managed network
- Commands supported by that device and its LogicVein adapter
- Python 3.10+, PowerShell 7+, or Node.js 20+

## Configuration

Copy the selected implementation's `.env.example` to `.env` and provide:

```dotenv
NETLD_BASE_URL=https://netld.example.com
NETLD_API_KEY=replace-with-your-api-key
NETLD_NETWORK=Default
NETLD_TARGET=192.0.2.10
NETLD_COMMAND_FILE=commands.txt
NETLD_OUTPUT_DIR=output
NETLD_RUN_JOB=false
NETLD_POLL_SECONDS=2
NETLD_WAIT_TIMEOUT_SECONDS=300
NETLD_BACKUP_ON_COMPLETION=false
```

Copy `commands.txt.example` to `commands.txt` and place one or more commands in it. Blank lines are ignored. Keep `.env`, `commands.txt`, and generated logs out of source control.

The job targets the device using `ipCsv` data in the form `address@managed-network`. `NETLD_TARGET` should therefore be the device's management IP address, not an arbitrary interface address or hostname.

## Preview and execution

Run the selected implementation once with `NETLD_RUN_JOB=false`. It prints the exact `JobData` that would be submitted and does not contact the device.

After reviewing the target, managed network, commands, and backup setting, set `NETLD_RUN_JOB=true` and run it again. A successful run prints the final execution record and the paths of the exported logs.

## API compatibility note

The Python, PowerShell, and Node.js implementations were each validated end to end against a ThirdEye Suite lab on August 28, 2026, using a read-only Cisco IOS XE `show version` command. Each execution completed successfully and exported the expected per-device text log.

`Plugins.getExecutionDetails`, the `/servlet/pluginDetail` endpoint, and the command-runner tool identifier remain version-sensitive. The relevant repository documentation dates from 2016 and warned even then that the Plugins service would change in a future major release. Revalidate the complete workflow against the netLD or ThirdEye release where it will run.

## Historical source

The Python 2 JP1-named template remains under [`Examples/Deprecated/Python-2`](../../Deprecated/Python-2/Jp1_ShowCommand_Template.py) for historical inspection only. This example retains its workflow, not its obsolete authentication, TLS bypass, Python 2 runtime, or implied JP1 dependency.
