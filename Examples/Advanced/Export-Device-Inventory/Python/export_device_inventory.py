#!/usr/bin/env python3
"""Export the complete netLD/ThirdEye device inventory to CSV or JSON."""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

import requests
from dotenv import load_dotenv


CSV_FIELDS = (
    "network", "ipAddress", "hostname", "adapterId", "deviceType",
    "hardwareVendor", "model", "serialNumber", "softwareVendor", "osVersion",
    "backupStatus", "complianceState", "lastBackup", "lastTelemetry", "memoSummary",
    "custom1", "custom2", "custom3", "custom4", "custom5",
)


class ExampleError(RuntimeError):
    pass


def parse_networks(value: str) -> list[str]:
    networks = [item.strip() for item in value.split(",") if item.strip()]
    if not networks:
        raise ExampleError("NETLD_NETWORKS must contain at least one managed network.")
    return networks


@dataclass(frozen=True)
class Config:
    base_url: str
    api_key: str
    networks: list[str]
    output_path: Path
    output_format: str
    page_size: int
    scheme: str
    query: str

    @classmethod
    def from_env(
        cls, env_path: Path, output_base: Path | None = None,
        format_override: str | None = None,
    ) -> "Config":
        load_dotenv(env_path, override=True)
        base_url = os.getenv("NETLD_BASE_URL", "").strip()
        api_key = os.getenv("NETLD_API_KEY", "").strip()
        if not base_url:
            raise ExampleError("Set NETLD_BASE_URL in .env before running this example.")
        if not api_key:
            raise ExampleError("Set NETLD_API_KEY in .env before running this example.")
        try:
            page_size = int(os.getenv("NETLD_PAGE_SIZE", "500"))
        except ValueError as exc:
            raise ExampleError("NETLD_PAGE_SIZE must be a positive integer.") from exc
        if page_size <= 0:
            raise ExampleError("NETLD_PAGE_SIZE must be a positive integer.")
        output_format = (format_override or os.getenv("NETLD_OUTPUT_FORMAT", "csv")).strip().lower()
        if output_format not in {"csv", "json"}:
            raise ExampleError("NETLD_OUTPUT_FORMAT must be either csv or json.")
        output_name = os.getenv("NETLD_OUTPUT_FILE", "").strip() or f"inventory.{output_format}"
        output_path = Path(output_name)
        if not output_path.is_absolute():
            output_path = (output_base or env_path.parent) / output_path
        return cls(
            base_url=base_url.rstrip("/"), api_key=api_key,
            networks=parse_networks(os.getenv("NETLD_NETWORKS", "Default")),
            output_path=output_path, output_format=output_format, page_size=page_size,
            scheme=os.getenv("NETLD_SEARCH_SCHEME", "ipAddress").strip() or "ipAddress",
            query=os.getenv("NETLD_SEARCH_QUERY", ""),
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

    def search_inventory(
        self, networks: list[str], scheme: str, query: str, offset: int, page_size: int
    ) -> dict[str, Any]:
        if not query.endswith("\n"):
            query = f"{query}\n"
        result = self.call(
            "Inventory.search", network=networks, scheme=scheme, query=query,
            pageData={"offset": offset, "pageSize": page_size},
            sortColumn="ipAddress", descending=False,
        )
        if not isinstance(result, dict):
            raise ExampleError("Inventory.search returned no page data.")
        return result


def inventory_pages(
    client: Any, networks: list[str], scheme: str, query: str, page_size: int
) -> Iterator[list[dict[str, Any]]]:
    offset = 0
    total: int | None = None
    while True:
        page = client.search_inventory(networks, scheme, query, offset, page_size)
        devices = page.get("devices") or []
        if not isinstance(devices, list):
            raise ExampleError("Inventory.search returned an invalid devices collection.")
        yield devices
        returned_page_size = int(page.get("pageSize") or page_size)
        if returned_page_size <= 0:
            raise ExampleError("Inventory.search returned an invalid page size.")
        if total is None and page.get("total") is not None:
            total = int(page["total"])
        if total is not None and offset + len(devices) >= total:
            return
        if total is None and len(devices) < returned_page_size:
            return
        if not devices:
            raise ExampleError("Inventory.search returned an empty page before the reported total.")
        offset += returned_page_size


def export_inventory(
    client: Any, networks: list[str], scheme: str, query: str,
    page_size: int, output_path: Path, output_format: str = "csv",
) -> int:
    output_format = output_format.lower()
    if output_format not in {"csv", "json"}:
        raise ExampleError("Output format must be either csv or json.")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    count = 0
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="", prefix=f".{output_path.name}.",
            suffix=".tmp", dir=output_path.parent, delete=False,
        ) as output:
            temporary_path = Path(output.name)
            writer = None
            if output_format == "csv":
                writer = csv.DictWriter(output, fieldnames=CSV_FIELDS, extrasaction="ignore")
                writer.writeheader()
            else:
                output.write("[\n")
            first_json_record = True
            for devices in inventory_pages(client, networks, scheme, query, page_size):
                for device in devices:
                    record = {field: device.get(field) for field in CSV_FIELDS}
                    if writer is not None:
                        writer.writerow(record)
                    else:
                        if not first_json_record:
                            output.write(",\n")
                        rendered = json.dumps(record, indent=2, ensure_ascii=False)
                        output.write("\n".join(f"  {line}" for line in rendered.splitlines()))
                        first_json_record = False
                    count += 1
            if output_format == "json":
                output.write("\n]\n")
        os.replace(temporary_path, output_path)
        return count
    except Exception:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--env", type=Path, default=Path(__file__).with_name(".env"))
    parser.add_argument("--format", choices=("csv", "json"))
    args = parser.parse_args()
    try:
        config = Config.from_env(args.env, Path(__file__).resolve().parent, args.format)
        client = NetLDClient(config.base_url, config.api_key)
        client.login()
        count = export_inventory(
            client, config.networks, config.scheme, config.query,
            config.page_size, config.output_path, config.output_format,
        )
        print(f"Wrote {count} devices to {config.output_path}")
        return 0
    except (ExampleError, OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
