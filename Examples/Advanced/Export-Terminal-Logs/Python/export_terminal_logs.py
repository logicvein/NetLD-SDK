#!/usr/bin/env python3
"""Incrementally export documented netLD/ThirdEye terminal proxy logs."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import requests
except ModuleNotFoundError:
    requests = None  # type: ignore[assignment]
try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    load_dotenv = None  # type: ignore[assignment]

STATE_FORMAT = "logicvein-netld-terminal-log-export-state"
RUN_FORMAT = "logicvein-netld-terminal-log-export-run"
FORMAT_VERSION = 1


class ExampleError(RuntimeError):
    pass


def parse_bool(value: str, name: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ExampleError(f"{name} must be true or false.")


def safe_name(value: str, fallback: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip()).strip("._")
    return cleaned or fallback


def iso_utc(milliseconds: int) -> str:
    return datetime.fromtimestamp(milliseconds / 1000, timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%S"
    )


def generated_at() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


@dataclass(frozen=True)
class Config:
    base_url: str
    api_key: str
    output_dir: Path
    state_path: Path
    report_path: Path
    initial_lookback: str
    networks: list[str]
    target: str
    strip_xml: bool

    @classmethod
    def from_env(cls, env_path: Path, base: Path) -> "Config":
        if load_dotenv is None:
            raise ExampleError("Install the Python dependencies from requirements.txt.")
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

        networks = sorted(
            {
                part.strip()
                for part in os.getenv("NETLD_NETWORKS", "").split(",")
                if part.strip()
            }
        )
        lookback = os.getenv("NETLD_INITIAL_LOOKBACK", "30d").strip()
        if not lookback:
            raise ExampleError("NETLD_INITIAL_LOOKBACK cannot be empty.")
        return cls(
            url.rstrip("/"),
            key,
            destination("NETLD_OUTPUT_DIR", "terminal-logs"),
            destination("NETLD_STATE_FILE", "terminal-log-export-state.json"),
            destination("NETLD_RUN_REPORT_FILE", "terminal-log-export-run.json"),
            lookback,
            networks,
            os.getenv("NETLD_TARGET", "").strip(),
            parse_bool(os.getenv("NETLD_STRIP_XML", "true"), "NETLD_STRIP_XML"),
        )


class NetLDClient:
    def __init__(self, config: Config, timeout: float = 30):
        if requests is None:
            raise ExampleError("Install the Python dependencies from requirements.txt.")
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

    def search(self, scheme: str, query: str) -> list[dict[str, Any]]:
        response = self.request(
            "POST",
            "/rest",
            headers={"Content-Type": "application/json"},
            json={
                "jsonrpc": "2.0",
                "method": "TermLogs.search",
                "params": [scheme, query, "sessionEnd", False],
                "id": str(uuid.uuid4()),
            },
        )
        try:
            data = response.json()
        except ValueError as exc:
            raise ExampleError("TermLogs.search returned invalid JSON.") from exc
        if data.get("error"):
            raise ExampleError(f"TermLogs.search failed: {json.dumps(data['error'])}")
        result = data.get("result")
        if not isinstance(result, list):
            raise ExampleError("TermLogs.search returned an invalid collection.")
        return result

    def retrieve(self, record: dict[str, Any]) -> bytes:
        response = self.request(
            "GET",
            "/servlet/termlog",
            params={
                "op": "content",
                "stripXml": str(self.config.strip_xml).lower(),
                "sessionStart": iso_utc(int(record["sessionStart"])),
                "ipAddress": record["ipAddress"],
                "managedNetwork": record["managedNetwork"],
            },
        )
        return response.content


def build_search(config: Config, state: dict[str, Any]) -> tuple[str, str]:
    schemes = ["since" if state.get("lastSessionEnd") is not None else "session"]
    queries = [
        iso_utc(int(state["lastSessionEnd"]))
        if state.get("lastSessionEnd") is not None
        else config.initial_lookback
    ]
    if config.networks:
        schemes.append("network")
        queries.append(",".join(config.networks))
    if config.target:
        schemes.append("target")
        queries.append(config.target)
    return ",".join(schemes), "\n".join(queries)


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
        raise ExampleError("The terminal-log state file has an unsupported format.")
    return state


def write_atomic(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", delete=False
        ) as stream:
            temporary = Path(stream.name)
            stream.write(content)
        os.replace(temporary, path)
    except Exception:
        if temporary:
            temporary.unlink(missing_ok=True)
        raise


def write_json(path: Path, value: dict[str, Any]) -> None:
    write_atomic(
        path,
        (
            json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
        ).encode(),
    )


def select_records(
    records: list[dict[str, Any]], state: dict[str, Any]
) -> list[dict[str, Any]]:
    if state.get("lastSessionEnd") is None:
        selected = records
    else:
        watermark = int(state["lastSessionEnd"])
        ids = {int(value) for value in state.get("logIdsAtLastSessionEnd", [])}
        selected = [
            record
            for record in records
            if int(record["sessionEnd"]) > watermark
            or (
                int(record["sessionEnd"]) == watermark
                and int(record["logId"]) not in ids
            )
        ]
    unique = {int(record["logId"]): record for record in selected}
    return sorted(
        unique.values(),
        key=lambda record: (int(record["sessionEnd"]), int(record["logId"])),
    )


def archive_record(
    config: Config, record: dict[str, Any], content: bytes
) -> dict[str, Any]:
    start = int(record["sessionStart"])
    date = datetime.fromtimestamp(start / 1000, timezone.utc).strftime("%Y-%m-%d")
    extension = ".log" if config.strip_xml else ".xml"
    directory = (
        config.output_dir
        / safe_name(str(record["managedNetwork"]), "network")
        / safe_name(str(record["ipAddress"]), "device")
        / date
    )
    stem = f"{datetime.fromtimestamp(start / 1000, timezone.utc).strftime('%Y%m%dT%H%M%SZ')}_log-{int(record['logId'])}"
    content_path = directory / f"{stem}{extension}"
    metadata_path = directory / f"{stem}.metadata.json"
    write_atomic(content_path, content)
    write_json(
        metadata_path,
        {
            "record": record,
            "contentFile": content_path.name,
            "stripXml": config.strip_xml,
        },
    )
    return {
        "logId": int(record["logId"]),
        "sessionStart": start,
        "sessionEnd": int(record["sessionEnd"]),
        "bytes": len(content),
        "contentFile": str(content_path.relative_to(config.output_dir)),
        "metadataFile": str(metadata_path.relative_to(config.output_dir)),
    }


def export_terminal_logs(
    client: Any, config: Config, timestamp: str | None = None
) -> dict[str, Any]:
    state = load_state(config.state_path)
    scheme, query = build_search(config, state)
    records = client.search(scheme, query)
    candidates = select_records(records, state)
    archived, failures = [], []
    for record in candidates:
        try:
            archived.append(archive_record(config, record, client.retrieve(record)))
        except Exception as exc:
            failures.append(
                {
                    "logId": record.get("logId"),
                    "sessionStart": record.get("sessionStart"),
                    "error": str(exc),
                }
            )
    if candidates and not failures:
        newest = max(int(record["sessionEnd"]) for record in candidates)
        ids = {
            int(record["logId"])
            for record in candidates
            if int(record["sessionEnd"]) == newest
        }
        if state.get("lastSessionEnd") is not None and newest == int(
            state["lastSessionEnd"]
        ):
            ids.update(int(value) for value in state.get("logIdsAtLastSessionEnd", []))
        state.update(lastSessionEnd=newest, logIdsAtLastSessionEnd=sorted(ids))
    report = {
        "format": RUN_FORMAT,
        "formatVersion": FORMAT_VERSION,
        "generatedAt": timestamp or generated_at(),
        "scheme": scheme,
        "resultCount": len(records),
        "archivedCount": len(archived),
        "failureCount": len(failures),
        "archived": archived,
        "failures": failures,
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
        client = NetLDClient(config)
        client.login()
        report = export_terminal_logs(client, config)
        print(
            f"Found {report['resultCount']} terminal logs and archived {report['archivedCount']} to {config.output_dir}"
        )
        print(f"Recorded {report['failureCount']} failures in {config.report_path}")
        return 2 if report["failureCount"] else 0
    except (ExampleError, OSError, ValueError, KeyError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
