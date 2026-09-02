# Deprecated ThirdEye Violation Exporter

The PowerShell files in this directory are retained solely for historical
inspection. Do not use them for new automation.

The original implementation called the legacy `/servlet/triggerEvent` CSV
endpoint, put a username and password in the request URL, disabled TLS
certificate verification, installed `PsIni` for all users at runtime, and
stored environment-specific settings and mutable state together in a tracked
file. It also did not verify that the downloaded response was actually CSV
before advancing its watermark.

Use the maintained [Export ThirdEye
Violations](../../Advanced/Export-ThirdEye-Violations/) example instead. It
uses API-key authentication and the structured, paged
`Incidents.searchTriggerEvents` contract used by ThirdEye itself.
