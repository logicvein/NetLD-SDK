# Deprecated Terminal-Log Export Examples

These Perl and Ruby scripts are the original incremental terminal proxy log exporters. Although `TermLogs.search` and `/servlet/termlog` are documented, these implementations use username-and-password authentication in URLs, disable TLS certificate verification, mutate INI files directly, and do not provide atomic state or partial-failure handling.

They are retained only for historical inspection and should not be used on a current netLD or ThirdEye system.

Use the maintained [Export Terminal Proxy Logs](../../Advanced/Export-Terminal-Logs/) example instead. It provides tested Python, Node.js, and PowerShell implementations with API-key authentication, TLS verification, encoded retrieval parameters, stable filenames, metadata sidecars, atomic state, filtering, and failure reporting.

The related Python 2 implementation remains in the consolidated [Python 2](../Python-2/) historical collection.
