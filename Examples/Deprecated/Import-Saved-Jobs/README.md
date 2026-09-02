# Deprecated Saved-Job Importer

The Perl files in this directory are retained solely for historical inspection.
Do not run the importer against a current netLD or ThirdEye system.

`importJobs.pl` changes the appliance's saved-job registry. It calls the old,
undocumented `Scheduler.addJob` method with replacement enabled, so a matching
job can be overwritten without a preview, collision report, confirmation, or
rollback path. It also hard-codes username-and-password authentication in the
request URL and disables TLS certificate verification.

The accompanying `settings.conf` is an orphaned sample from the former Perl
collection; `importJobs.pl` does not read it.

There is no maintained replacement for this importer. The current
[Scheduler API](https://docs.logicvein.com/manuals/logicvein-api/scheduler/)
documents `Scheduler.saveJob`, but any future restore example should be
preview-only by default, validate every target managed network, report name and
ID collisions, and require an explicit execution option before making changes.

For a read-only export of saved job definitions, use [Back Up Saved
Jobs](../../Advanced/Backup-Saved-Jobs/).
