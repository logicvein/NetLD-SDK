# Advanced Examples

These examples combine multiple LogicVein APIs into complete operational workflows. They assume familiarity with the examples under [Getting Started](../Getting-Started/) and include safeguards around actions that contact managed devices.

- [Run Commands and Export Logs](Run-Cmd-And-Export-Log/) starts an ad hoc command-runner job, waits for it to finish, and saves the per-device output.
- [Export Device Inventory](Export-Device-Inventory/) retrieves every inventory page across one or more managed networks and writes a complete CSV export.
- [Export Device Interfaces](Export-Device-Interfaces/) retrieves the stored interfaces for every matching device and records per-device lookup failures separately.
- [Back Up Saved Jobs](Backup-Saved-Jobs/) retrieves complete saved-job definitions and writes a versioned JSON backup without modifying the scheduler.
