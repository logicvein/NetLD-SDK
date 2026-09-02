# Export Terminal Proxy Logs

This example incrementally exports terminal proxy session logs stored by netLD or ThirdEye. It uses the documented `TermLogs.search` JSON-RPC method and the documented `/servlet/termlog` HTTP retrieval endpoint described in the [LogicVein API manual](https://docs.logicvein.com/manuals/logicvein-api/).

Implementations are provided for [Python](Python/), [Node.js](nodeJS/), and [PowerShell](PowerShell/). They use API-key authentication, verify TLS certificates, URL-encode retrieval parameters, write content and metadata atomically, and maintain an incremental watermark.

## Initial and incremental runs

The first run searches the period configured by `NETLD_INITIAL_LOOKBACK`, which defaults to `30d`. Optional `NETLD_NETWORKS` and `NETLD_TARGET` values restrict the search. Later runs use the documented `since` scheme from the saved `sessionEnd` watermark and retain the same filters.

The state records every log ID observed at the watermark timestamp so equal timestamps do not lose or duplicate sessions. If any download fails, the watermark is not advanced and the affected batch is retried. A partial-failure run exits with status 2; a fatal setup or search error exits with status 1.

## Output and sensitivity

Logs are written under `terminal-logs/<network>/<device>/<UTC-date>/` with a `.metadata.json` sidecar containing the corresponding `TermLogSearchResult`. With the default `NETLD_STRIP_XML=true`, content is written as plain `.log` files. Set it to `false` to retain the raw XML representation.

Terminal logs can contain commands, configuration fragments, usernames, addresses, and other sensitive operational information. Protect the output directory accordingly. Empty log files are valid: a recorded terminal session may contain no displayable text after XML markup is stripped.

`TermLogs.search` is an older JSON-RPC service whose documented positional parameter array remains required; the current server rejects named parameters.
