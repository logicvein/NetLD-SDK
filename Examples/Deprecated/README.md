# Deprecated Examples

The examples in this directory are retained solely for historical inspection.
They are not maintained, tested, or recommended for use with current LogicVein
products.

These examples may depend on end-of-life runtimes, unavailable third-party
packages, deprecated product APIs, or outdated authentication and TLS practices.
They may fail without warning or make unintended changes to a system.

**LogicVein strongly recommends that you do not use these examples for new
automation or run them against a production system.**

For current, documented examples, see [Getting Started](../Getting-Started/)
and [Advanced Examples](../Advanced/).

## Create Device

The historical Python 3, Perl, and Ruby create-device demonstrations are grouped under [Create-Device](Create-Device/). Use the maintained [Create a Device](../Getting-Started/Create-Device/) example instead.

## Reimplemented Workflows

The following historical Perl and Ruby examples have maintained replacements:

- [Archive Configuration Revisions](Archive-Configuration-Revisions/) replaces the old incremental configuration exporters.
- [Export Hardware Inventory](Export-Hardware-Inventory/) replaces the old Hardware Report exporters.
- [Export Device Inventory](Export-Device-Inventory/) replaces the old CSV inventory exporters.
- [Back Up Saved Jobs](Backup-Saved-Jobs/) replaces the old saved-job JSON exporter.
- [Search Inventory](Search-Inventory/) replaces the old interactive device-search scripts.
- [Export Terminal Proxy Logs](Export-Terminal-Logs/) replaces the old incremental terminal-log exporters.

Each directory identifies the maintained example and explains why the original implementation is retained only for historical inspection. Legacy job-history, job-import, ThirdEye-violation, and static-credential workflows remain outside these groups until maintained replacements exist.

## Python 2

The `Python-2` collection requires Python 2, which is end-of-life. It is
preserved as originally organized so that related scripts, helper modules, and
sample configuration files remain together for historical reference.
