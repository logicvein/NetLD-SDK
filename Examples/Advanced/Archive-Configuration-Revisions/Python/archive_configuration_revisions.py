#!/usr/bin/env python3
"""Archive netLD/ThirdEye configuration revisions using documented JSON-RPC APIs."""

from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import json
import os
import re
import sys
import tempfile
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

import requests
from dotenv import load_dotenv


STATE_FORMAT = "logicvein-netld-configuration-archive-state"
RUN_FORMAT = "logicvein-netld-configuration-archive-run"
FORMAT_VERSION = 1


class ExampleError(RuntimeError):
    pass


def parse_networks(value: str) -> list[str]:
    networks = sorted({item.strip() for item in value.split(",") if item.strip()})
    if not networks:
        raise ExampleError("NETLD_NETWORKS must contain at least one managed network.")
    return networks


def safe_name(value: str, fallback: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip()).strip("._")
    return cleaned or fallback


def path_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:8]


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class Config:
    base_url: str
    api_key: str
    networks: list[str]
    archive_dir: Path
    state_path: Path
    run_report_path: Path
    inventory_page_size: int
    history_page_size: int
    search_scheme: str
    search_query: str
    initial_mode: str

    @classmethod
    def from_env(cls, env_path: Path, output_base: Path) -> "Config":
        load_dotenv(env_path, override=True)
        base_url = os.getenv("NETLD_BASE_URL", "").strip()
        api_key = os.getenv("NETLD_API_KEY", "").strip()
        if not base_url or not api_key:
            raise ExampleError("Set NETLD_BASE_URL and NETLD_API_KEY in the environment file.")
        try:
            inventory_page_size = int(os.getenv("NETLD_INVENTORY_PAGE_SIZE", "500"))
            history_page_size = int(os.getenv("NETLD_HISTORY_PAGE_SIZE", "500"))
        except ValueError as exc:
            raise ExampleError("Page sizes must be positive integers.") from exc
        if inventory_page_size <= 0 or history_page_size <= 0:
            raise ExampleError("Page sizes must be positive integers.")
        initial_mode = os.getenv("NETLD_INITIAL_MODE", "latest").strip().lower()
        if initial_mode not in {"latest", "all"}:
            raise ExampleError("NETLD_INITIAL_MODE must be either latest or all.")

        def destination(name: str, default: str) -> Path:
            value = Path(os.getenv(name, default))
            return value if value.is_absolute() else output_base / value

        return cls(
            base_url.rstrip("/"), api_key,
            parse_networks(os.getenv("NETLD_NETWORKS", "Default")),
            destination("NETLD_ARCHIVE_DIR", "configuration-archive"),
            destination("NETLD_STATE_FILE", "configuration-archive-state.json"),
            destination("NETLD_RUN_REPORT_FILE", "configuration-archive-run.json"),
            inventory_page_size, history_page_size,
            os.getenv("NETLD_SEARCH_SCHEME", "ipAddress").strip() or "ipAddress",
            os.getenv("NETLD_SEARCH_QUERY", ""), initial_mode,
        )


class NetLDClient:
    def __init__(self, base_url: str, api_key: str, timeout: float = 30):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {api_key}"})

    def _request(self, method: str, **kwargs: Any):
        try:
            response = self.session.request(
                method, f"{self.base_url}/rest", timeout=self.timeout,
                allow_redirects=False, **kwargs,
            )
        except requests.RequestException as exc:
            raise ExampleError(f"Could not reach {self.base_url}.") from exc
        if 300 <= response.status_code < 400:
            raise ExampleError(f"Request redirected to {response.headers.get('Location', '')}.")
        try:
            response.raise_for_status()
        except requests.RequestException as exc:
            raise ExampleError(f"Request failed with HTTP {response.status_code}.") from exc
        return response

    def login(self) -> None:
        self._request("GET")

    def call(self, method: str, **parameters: Any) -> Any:
        response = self._request(
            "POST", headers={"Content-Type": "application/json"},
            json={"jsonrpc": "2.0", "method": method, "params": parameters, "id": str(uuid.uuid4())},
        )
        try:
            data = response.json()
        except ValueError as exc:
            raise ExampleError(f"{method} returned invalid JSON.") from exc
        if data.get("error"):
            raise ExampleError(f"{method} failed: {json.dumps(data['error'])}")
        return data.get("result")

    def search_inventory(self, config: Config, offset: int):
        query = config.search_query
        result = self.call(
            "Inventory.search", network=config.networks, scheme=config.search_scheme,
            query=query if query.endswith("\n") else f"{query}\n",
            pageData={"offset": offset, "pageSize": config.inventory_page_size},
            sortColumn="ipAddress", descending=False,
        )
        if not isinstance(result, dict):
            raise ExampleError("Inventory.search returned no page data.")
        return result

    def configuration_history(self, device: dict[str, Any], offset: int, page_size: int):
        result = self.call(
            "Configuration.retrieveConfigHistory",
            pageData={"offset": offset, "pageSize": page_size, "total": 0, "configHistoryItems": []},
            networks=[device["network"]], scheme="ipAddress", data=device["ipAddress"],
            sortColumn="session", descending=True,
        )
        if not isinstance(result, dict):
            raise ExampleError("Configuration.retrieveConfigHistory returned no page data.")
        return result

    def retrieve_revision(self, item: dict[str, Any]):
        result = self.call(
            "Configuration.retrieveRevision", network=item["managedNetwork"],
            ipAddress=item["ipAddress"], configPath=item["path"], timestamp=item["lastChanged"],
        )
        if not isinstance(result, dict):
            raise ExampleError("Configuration.retrieveRevision returned no revision.")
        return result


def inventory_devices(client: Any, config: Config) -> Iterator[dict[str, Any]]:
    offset = 0
    total: int | None = None
    while True:
        page = client.search_inventory(config, offset)
        devices = page.get("devices") or []
        for device in devices:
            yield device
        page_size = int(page.get("pageSize") or config.inventory_page_size)
        if total is None and page.get("total") is not None:
            total = int(page["total"])
        if total is not None and offset + len(devices) >= total:
            return
        if total is None and len(devices) < page_size:
            return
        if not devices:
            raise ExampleError("Inventory.search returned an empty page before the reported total.")
        offset += page_size


def history_items(
    client: Any, config: Config, device: dict[str, Any], stop_before: int | None = None,
) -> Iterator[dict[str, Any]]:
    offset = 0
    total: int | None = None
    while True:
        page = client.configuration_history(device, offset, config.history_page_size)
        items = page.get("configHistoryItems") or []
        for item in items:
            # Results are requested newest-first. Once an incremental scan passes
            # its watermark, no later page can contain a candidate.
            if stop_before is not None and int(item["lastChanged"]) < stop_before:
                return
            yield item
        page_size = int(page.get("pageSize") or config.history_page_size)
        if total is None and page.get("total") is not None:
            total = int(page["total"])
        if total is not None and offset + len(items) >= total:
            return
        if total is None and len(items) < page_size:
            return
        if not items:
            raise ExampleError("Configuration history returned an empty page before the reported total.")
        offset += page_size


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"format": STATE_FORMAT, "formatVersion": FORMAT_VERSION, "devices": {}}
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ExampleError(f"Could not read archive state: {path}") from exc
    if state.get("format") != STATE_FORMAT or state.get("formatVersion") != FORMAT_VERSION:
        raise ExampleError("The archive state file has an unsupported format.")
    if not isinstance(state.get("devices"), dict):
        raise ExampleError("The archive state file has an invalid devices object.")
    return state


def write_atomic(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", delete=False) as output:
            temporary_path = Path(output.name)
            output.write(content)
        os.replace(temporary_path, path)
    except Exception:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
        raise


def write_json_atomic(path: Path, document: dict[str, Any]) -> None:
    write_atomic(path, (json.dumps(document, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8"))


def select_candidates(
    items: list[dict[str, Any]], state_entry: dict[str, Any] | None, initial_mode: str,
) -> list[dict[str, Any]]:
    if state_entry is None:
        if initial_mode == "all":
            selected = items
        else:
            newest_by_path: dict[str, dict[str, Any]] = {}
            for item in items:
                newest_by_path.setdefault(item["path"], item)
            selected = list(newest_by_path.values())
    else:
        watermark = int(state_entry["lastChanged"])
        paths_at_watermark = set(state_entry.get("pathsAtLastChanged") or [])
        selected = [
            item for item in items
            if int(item["lastChanged"]) > watermark
            or (int(item["lastChanged"]) == watermark and item["path"] not in paths_at_watermark)
        ]
    unique = {(int(item["lastChanged"]), item["path"]): item for item in selected}
    return [unique[key] for key in sorted(unique)]


def archive_one_revision(config: Config, item: dict[str, Any], revision: dict[str, Any]) -> dict[str, Any]:
    try:
        content = base64.b64decode(revision.get("content") or "", validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ExampleError("Configuration revision content is not valid Base64.") from exc
    network = item["managedNetwork"]
    ip_address = item["ipAddress"]
    config_path = item["path"]
    stem = f"{int(item['lastChanged'])}_{safe_name(config_path, 'config')}_{path_hash(config_path)}"
    extension = ".txt" if (revision.get("mimeType") or item.get("mimeType") or "").startswith("text/") else ".bin"
    directory = config.archive_dir / safe_name(network, "network") / safe_name(ip_address, "device")
    content_path = directory / f"{stem}{extension}"
    metadata_path = directory / f"{stem}.metadata.json"
    write_atomic(content_path, content)
    metadata = {
        "network": network, "ipAddress": ip_address, "configPath": config_path,
        "lastChanged": int(item["lastChanged"]),
        "history": item,
        "revision": {key: value for key, value in revision.items() if key != "content"},
        "contentFile": content_path.name,
    }
    write_json_atomic(metadata_path, metadata)
    return {
        "network": network, "ipAddress": ip_address, "configPath": config_path,
        "lastChanged": int(item["lastChanged"]), "mimeType": revision.get("mimeType"),
        "size": len(content),
        "contentFile": str(content_path.relative_to(config.archive_dir)),
        "metadataFile": str(metadata_path.relative_to(config.archive_dir)),
    }


def archive_configuration_revisions(
    client: Any, config: Config, generated_at: str | None = None,
) -> dict[str, Any]:
    state = load_state(config.state_path)
    archived: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    device_count = 0
    for device in inventory_devices(client, config):
        device_count += 1
        key = f"{device['network']}@{device['ipAddress']}"
        old_entry = state["devices"].get(key)
        try:
            stop_before = int(old_entry["lastChanged"]) if old_entry else None
            all_items = list(history_items(client, config, device, stop_before))
            candidates = select_candidates(all_items, old_entry, config.initial_mode)
        except Exception as exc:
            failures.append({
                "stage": "history", "network": device.get("network"),
                "ipAddress": device.get("ipAddress"), "error": str(exc),
            })
            continue
        device_archived = []
        device_failed = False
        for item in candidates:
            try:
                revision = client.retrieve_revision(item)
                record = archive_one_revision(config, item, revision)
                archived.append(record)
                device_archived.append(record)
            except Exception as exc:
                device_failed = True
                failures.append({
                    "stage": "revision", "network": item.get("managedNetwork"),
                    "ipAddress": item.get("ipAddress"), "configPath": item.get("path"),
                    "lastChanged": item.get("lastChanged"), "error": str(exc),
                })
        if candidates and not device_failed:
            newest = max(int(item["lastChanged"]) for item in candidates)
            paths = sorted({item["path"] for item in candidates if int(item["lastChanged"]) == newest})
            if old_entry and newest == int(old_entry["lastChanged"]):
                paths = sorted(set(paths) | set(old_entry.get("pathsAtLastChanged") or []))
            state["devices"][key] = {"lastChanged": newest, "pathsAtLastChanged": paths}
    report = {
        "format": RUN_FORMAT, "formatVersion": FORMAT_VERSION,
        "generatedAt": generated_at or utc_timestamp(), "initialMode": config.initial_mode,
        "deviceCount": device_count, "archivedCount": len(archived),
        "failureCount": len(failures), "archived": archived, "failures": failures,
    }
    write_json_atomic(config.state_path, state)
    write_json_atomic(config.run_report_path, report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--env", type=Path, default=Path(__file__).with_name(".env"))
    args = parser.parse_args()
    try:
        config = Config.from_env(args.env, Path(__file__).resolve().parent)
        client = NetLDClient(config.base_url, config.api_key)
        client.login()
        report = archive_configuration_revisions(client, config)
        print(f"Processed {report['deviceCount']} devices and archived {report['archivedCount']} revisions")
        print(f"Recorded {report['failureCount']} failures in {config.run_report_path}")
        return 2 if report["failureCount"] else 0
    except (ExampleError, OSError, ValueError, KeyError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
