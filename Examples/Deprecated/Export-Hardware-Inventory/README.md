# Deprecated Hardware Export Examples

These Perl and Ruby scripts generate and run the old Hardware Report job, poll its execution, and download its CSV result through `servlet/pluginDetail`. They use username-and-password authentication, disabled TLS verification, hard-coded defaults, and version-sensitive report internals.

They are retained only for historical inspection and should not be used on a current netLD or ThirdEye system.

Use the maintained [Export Hardware Inventory](../../Advanced/Export-Hardware-Inventory/) example instead. It provides tested Python, Node.js, and PowerShell implementations using `Inventory.search` and `Inventory.getDeviceHardware`, with CSV or JSON output and per-device failure reporting.

Related Python 2 material remains in the consolidated [Python 2](../Python-2/) historical collection.
