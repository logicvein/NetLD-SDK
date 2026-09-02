# Deprecated Job Execution Output Exporters

These Perl and Ruby `exportJobHistory` implementations are retained solely for
historical inspection. A related Python 2 implementation remains with its
shared legacy dependencies in [`../Python-2`](../Python-2/exportJobHistory.py).

Do not use these scripts for new automation. They rely on obsolete runtimes or
third-party packages, authenticate with a username and password in a URL, do
not consistently verify TLS certificates, retrieve only the first page of
execution history, and can advance their timestamp state after an incomplete
export.

Use the maintained [Archive Job Execution
Outputs](../../Advanced/Archive-Job-Execution-Outputs/) example instead. It is
available in Python 3, Node.js, and PowerShell and uses API-key authentication,
verified HTTPS, paging, atomic files, and failure-aware incremental state.
