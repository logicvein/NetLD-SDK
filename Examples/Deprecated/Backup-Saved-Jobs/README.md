# Deprecated Saved-Job Export Example

This Perl script is the original saved-job JSON export. It uses username and password values on the request URL, disabled TLS verification, a fixed managed network, and older scheduler lookup conventions.

It is retained only for historical inspection and should not be used on a current netLD or ThirdEye system.

Use the maintained [Back Up Saved Jobs](../../Advanced/Backup-Saved-Jobs/) example instead. It provides tested Python, Node.js, and PowerShell implementations with API-key authentication, multiple managed networks, complete pagination, full job definitions, versioned output, deduplication, and failure reporting.

The old `importJobs.pl` script remains outside this directory because a maintained restore/import workflow has not yet been implemented.
