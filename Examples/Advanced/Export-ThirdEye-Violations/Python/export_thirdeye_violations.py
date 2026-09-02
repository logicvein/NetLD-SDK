#!/usr/bin/env python3
"""Incrementally export ThirdEye trigger-event violations to CSV or JSON."""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
import sys
import tempfile
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv


STATE_FORMAT = "logicvein-thirdeye-violation-export-state"
RUN_FORMAT = "logicvein-thirdeye-violation-export-run"
FORMAT_VERSION = 1
CSV_FIELDS: tuple[str, ...] = (
    "eventId", "incidentId", "severity", "clearState", "eventType", "network",
    "ipAddress", "hostname", "deviceId", "hostUuid", "measurement",
    "measurementIndex", "message", "occurrences", "triggerId", "created", "updated",
)


class ExampleError(RuntimeError):
    pass


def parse_queries(value: str) -> list[str]:
    try:
        parsed = json.loads(value or "[]")
    except json.JSONDecodeError as exc:
        raise ExampleError("NETLD_SEARCH_QUERIES must be a JSON array of strings.") from exc
    if not isinstance(parsed, list) or any(
        not isinstance(item, str) or not item.strip() for item in parsed
    ):
        raise ExampleError("NETLD_SEARCH_QUERIES must be a JSON array of non-empty strings.")
    queries = [item.strip() for item in parsed]
    if any(item.lower().startswith(("start=", "end=")) for item in queries):
        raise ExampleError(
            "NETLD_SEARCH_QUERIES must not contain start or end; the exporter controls its time window."
        )
    return queries


def iso_utc(milliseconds: int) -> str:
    return (
        datetime.fromtimestamp(milliseconds / 1000, timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def event_id(event: dict[str, Any]) -> int:
    value = event.get("eventId")
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise ExampleError("Incidents.searchTriggerEvents returned an event without an eventId.")
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ExampleError("Incidents.searchTriggerEvents returned an invalid eventId.") from exc


def event_updated(event: dict[str, Any]) -> int:
    value = event.get("updated")
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise ExampleError(
            "Incidents.searchTriggerEvents returned an event without an updated timestamp."
        )
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ExampleError(
            "Incidents.searchTriggerEvents returned an invalid updated timestamp."
        ) from exc


@dataclass(frozen=True)
class Config:
    base_url: str
    api_key: str
    output_dir: Path
    output_format: str
    state_path: Path
    report_path: Path
    page_size: int
    initial_lookback_hours: int
    search_queries: list[str]

    @classmethod
    def from_env(cls, env_path: Path, base: Path) -> "Config":
        load_dotenv(env_path, override=True)
        url = os.getenv("NETLD_BASE_URL", "").strip()
        key = os.getenv("NETLD_API_KEY", "").strip()
        if not url or not key:
            raise ExampleError(
                "Set NETLD_BASE_URL and NETLD_API_KEY in the environment file."
            )

        def destination(name: str, default: str) -> Path:
            value = Path(os.getenv(name, default))
            return value if value.is_absolute() else base / value

        output_format = os.getenv("NETLD_OUTPUT_FORMAT", "csv").strip().lower()
        if output_format not in {"csv", "json"}:
            raise ExampleError("NETLD_OUTPUT_FORMAT must be csv or json.")
        try:
            page_size = int(os.getenv("NETLD_PAGE_SIZE", "100"))
            lookback = int(os.getenv("NETLD_INITIAL_LOOKBACK_HOURS", "24"))
        except ValueError as exc:
            raise ExampleError(
                "NETLD_PAGE_SIZE and NETLD_INITIAL_LOOKBACK_HOURS must be positive integers."
            ) from exc
        if page_size <= 0 or lookback <= 0:
            raise ExampleError(
                "NETLD_PAGE_SIZE and NETLD_INITIAL_LOOKBACK_HOURS must be positive integers."
            )
        return cls(
            url.rstrip("/"),
            key,
            destination("NETLD_OUTPUT_DIR", "violation-exports"),
            output_format,
            destination("NETLD_STATE_FILE", "violation-export-state.json"),
            destination("NETLD_RUN_REPORT_FILE", "violation-export-run.json"),
            page_size,
            lookback,
            parse_queries(os.getenv("NETLD_SEARCH_QUERIES", "[]")),
        )


class ThirdEyeClient:
    def __init__(self, config: Config, timeout: float = 30):
        self.config = config
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {config.api_key}"})

    def request(self, method: str, endpoint: str, **kwargs: Any):
        try:
            response = self.session.request(
                method,
                f"{self.config.base_url}{endpoint}",
                timeout=self.timeout,
                allow_redirects=False,
                **kwargs,
            )
        except requests.RequestException as exc:
            raise ExampleError(f"Could not reach {self.config.base_url}.") from exc
        if 300 <= response.status_code < 400:
            raise ExampleError(
                f"Request redirected to {response.headers.get('Location', '')}."
            )
        try:
            response.raise_for_status()
        except requests.RequestException as exc:
            raise ExampleError(
                f"Request failed with HTTP {response.status_code}."
            ) from exc
        return response

    def login(self) -> None:
        self.request("GET", "/rest")

    def search_page(
        self, queries: list[str], offset: int, page_size: int
    ) -> dict[str, Any]:
        response = self.request(
            "POST",
            "/rest",
            headers={"Content-Type": "application/json"},
            json={
                "jsonrpc": "2.0",
                "method": "Incidents.searchTriggerEvents",
                "params": {
                    "pageData": {
                        "offset": offset,
                        "total": 0,
                        "pageSize": page_size,
                        "violations": [],
                    },
                    "queries": queries,
                    "sortColumn": "updated",
                    "descending": True,
                },
                "id": str(uuid.uuid4()),
            },
        )
        try:
            data = response.json()
        except ValueError as exc:
            raise ExampleError(
                "Incidents.searchTriggerEvents returned invalid JSON."
            ) from exc
        if data.get("error"):
            raise ExampleError(
                f"Incidents.searchTriggerEvents failed: {json.dumps(data['error'])}"
            )
        result = data.get("result")
        if not isinstance(result, dict) or not isinstance(
            result.get("violations"), list
        ):
            raise ExampleError(
                "Incidents.searchTriggerEvents returned invalid page data."
            )
        return result


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"format": STATE_FORMAT, "formatVersion": FORMAT_VERSION}
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ExampleError(f"Could not read export state: {path}") from exc
    if (
        state.get("format") != STATE_FORMAT
        or state.get("formatVersion") != FORMAT_VERSION
    ):
        raise ExampleError("The violation-export state file has an unsupported format.")
    return state


def write_atomic(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as stream:
            temporary = Path(stream.name)
            stream.write(content)
        os.replace(temporary, path)
    except Exception:
        if temporary:
            temporary.unlink(missing_ok=True)
        raise


def write_json(path: Path, value: Any) -> None:
    write_atomic(
        path, (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode()
    )


def build_queries(config: Config, state: dict[str, Any], now_ms: int) -> list[str]:
    start = (
        int(state["lastUpdated"])
        if state.get("lastUpdated") is not None
        else now_ms - config.initial_lookback_hours * 60 * 60 * 1000
    )
    return [
        *config.search_queries,
        f"start={iso_utc(start)}",
        f"end={iso_utc(now_ms)}",
    ]


def collect_events(
    client: Any, queries: list[str], page_size: int
) -> tuple[list[dict[str, Any]], int]:
    offset = 0
    total: int | None = None
    pages = 0
    events: list[dict[str, Any]] = []
    while total is None or offset < total:
        page = client.search_page(queries, offset, page_size)
        batch = page["violations"]
        page_offset = int(page.get("offset", offset))
        page_total = int(page.get("total", page_offset + len(batch)))
        total = page_total if total is None else max(total, page_total)
        pages += 1
        for event in batch:
            if not isinstance(event, dict):
                raise ExampleError(
                    "Incidents.searchTriggerEvents returned a non-object violation."
                )
            event_id(event)
            event_updated(event)
            events.append(event)
        next_offset = page_offset + len(batch)
        if next_offset >= total:
            break
        if not batch or next_offset <= offset:
            raise ExampleError(
                "Violation paging stopped before all reported results were returned."
            )
        offset = next_offset
    unique = {(event_updated(item), event_id(item)): item for item in events}
    return sorted(
        unique.values(), key=lambda item: (event_updated(item), event_id(item))
    ), pages


def select_events(
    events: list[dict[str, Any]], state: dict[str, Any]
) -> list[dict[str, Any]]:
    if state.get("lastUpdated") is None:
        return events
    watermark = int(state["lastUpdated"])
    ids = {int(value) for value in state.get("eventIdsAtLastUpdated", [])}
    return [
        event
        for event in events
        if event_updated(event) > watermark
        or (event_updated(event) == watermark and event_id(event) not in ids)
    ]


def csv_value(field: str, value: Any) -> Any:
    if field in {"created", "updated"} and value is not None:
        return iso_utc(int(value))
    return "" if value is None else value


def render_export(events: list[dict[str, Any]], output_format: str) -> bytes:
    if output_format == "json":
        return (json.dumps(events, indent=2, ensure_ascii=False) + "\n").encode()
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream, fieldnames=CSV_FIELDS, extrasaction="ignore", lineterminator="\n"
    )
    writer.writeheader()
    for event in events:
        writer.writerow(
            {field: csv_value(field, event.get(field)) for field in CSV_FIELDS}
        )
    return stream.getvalue().encode("utf-8")


def advance_state(state: dict[str, Any], events: list[dict[str, Any]]) -> None:
    if not events:
        return
    newest = max(event_updated(event) for event in events)
    ids = {event_id(event) for event in events if event_updated(event) == newest}
    if state.get("lastUpdated") is not None and int(state["lastUpdated"]) == newest:
        ids.update(int(value) for value in state.get("eventIdsAtLastUpdated", []))
    state.update(lastUpdated=newest, eventIdsAtLastUpdated=sorted(ids))


def export_violations(
    client: Any, config: Config, now_ms: int, timestamp: str | None = None
) -> dict[str, Any]:
    state = load_state(config.state_path)
    queries = build_queries(config, state, now_ms)
    events, page_count = collect_events(client, queries, config.page_size)
    selected = select_events(events, state)
    output_path: Path | None = None
    if selected:
        stamp = datetime.fromtimestamp(now_ms / 1000, timezone.utc).strftime(
            "%Y%m%dT%H%M%SZ"
        )
        output_path = config.output_dir / (
            f"violations-{stamp}.{config.output_format}"
        )
        write_atomic(output_path, render_export(selected, config.output_format))
        advance_state(state, selected)
    report = {
        "format": RUN_FORMAT,
        "formatVersion": FORMAT_VERSION,
        "generatedAt": timestamp or iso_utc(now_ms),
        "queries": queries,
        "pageCount": page_count,
        "resultCount": len(events),
        "exportedCount": len(selected),
        "outputFormat": config.output_format,
        "outputFile": str(output_path) if output_path else None,
    }
    write_json(config.state_path, state)
    write_json(config.report_path, report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--env", type=Path, default=Path(__file__).with_name(".env"))
    args = parser.parse_args()
    try:
        config = Config.from_env(args.env, Path(__file__).resolve().parent)
        client = ThirdEyeClient(config)
        client.login()
        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        report = export_violations(client, config, now_ms)
        print(
            f"Found {report['resultCount']} violations and exported {report['exportedCount']}."
        )
        print(f"Run report: {config.report_path}")
        return 0
    except (ExampleError, OSError, ValueError, KeyError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
