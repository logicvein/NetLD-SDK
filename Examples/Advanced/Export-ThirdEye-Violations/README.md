# Export ThirdEye Violations

This example incrementally exports ThirdEye trigger events, which the API
returns in a `violations` collection. It uses the structured
`Incidents.searchTriggerEvents` JSON-RPC method used by ThirdEye itself rather
than the historical `/servlet/triggerEvent` CSV endpoint.

This is a **ThirdEye and ThirdEye Suite example**. It is not an exporter for
netLD configuration-compliance violations. For those objects, see the
[Compliance API](https://docs.logicvein.com/manuals/logicvein-api/compliance/).

Implementations are provided for [Python](Python/), [Node.js](nodeJS/), and
[PowerShell](PowerShell/).

## What It Does

1. Authenticates with an API key and establishes a server session.
2. Searches a bounded `start`/`end` window using
   `Incidents.searchTriggerEvents`.
3. Retrieves every result page, sorted by the `updated` timestamp.
4. Removes records already represented by the saved watermark.
5. Writes the new batch atomically as CSV or JSON.
6. Advances the watermark only after the batch is safely written.

The first run searches the preceding 24 hours by default. Later runs begin at
the newest `updated` timestamp saved in the state file. Every `eventId` seen at
that exact timestamp is also saved, preventing equal timestamps from dropping
or duplicating records.

## Configuration

Copy the `.env.example` from the selected language directory to `.env`:

```dotenv
NETLD_BASE_URL=https://thirdeye.example.com
NETLD_API_KEY=replace-with-your-api-key
NETLD_OUTPUT_DIR=violation-exports
NETLD_OUTPUT_FORMAT=csv
NETLD_STATE_FILE=violation-export-state.json
NETLD_RUN_REPORT_FILE=violation-export-run.json
NETLD_PAGE_SIZE=100
NETLD_INITIAL_LOOKBACK_HOURS=24
NETLD_SEARCH_QUERIES=[]
```

`NETLD_BASE_URL` must not include `/rest`. Do not commit `.env`, the generated
exports, or the state and run-report files.

`NETLD_OUTPUT_FORMAT` may be `csv` or `json`. CSV includes a stable set of 17
columns and converts the `created` and `updated` millisecond values to UTC ISO
8601 timestamps. JSON preserves the values returned by the API.

`NETLD_SEARCH_QUERIES` is a JSON array containing additional exact API query
strings. For example:

```dotenv
NETLD_SEARCH_QUERIES='["incidentId=1"]'
```

Leave it as `[]` to export all trigger events in the time window. The exporter
owns the `start` and `end` queries; do not include them in this setting.

## Output and State

Each non-empty run creates one UTC-stamped file under `violation-exports/`, for
example `violations-20260902T170000Z.csv`. An empty run creates no export file
but still writes a run report.

Deleting the state file intentionally starts a new initial-lookback export.
Increasing `NETLD_INITIAL_LOOKBACK_HOURS` before that run can produce a large
batch. Protect the output directory: violation messages, device identities,
addresses, measurements, and incident metadata may be operationally sensitive.

## API Compatibility

The published [Incidents API
chapter](https://docs.logicvein.com/manuals/logicvein-api/incidents/) describes
the ThirdEye incidents service, but does not currently list
`Incidents.searchTriggerEvents`. The method is used by the product and was
validated with API-key authentication, filtering, and paging against a
ThirdEye Suite lab on September 2, 2026. The three implementations reproduced
the same two-event result for a bounded test window.

Treat this example as version-sensitive and test it against the ThirdEye release
where it will run.
