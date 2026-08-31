#!/usr/bin/env python3
"""Export collected netLD/ThirdEye device hardware to CSV or JSON."""

from __future__ import annotations
import argparse, csv, json, os, sys, tempfile, uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

import requests
from dotenv import load_dotenv

HARDWARE_FIELDS = (
    "network",
    "deviceIpAddress",
    "hostname",
    "adapterId",
    "hardwareId",
    "deviceId",
    "assetType",
    "make",
    "modelNumber",
    "serialNumber",
    "partNumber",
    "fruPartNumber",
    "firmwareVersion",
    "hardwareVersion",
    "revisionNumber",
    "rmaNumber",
    "description",
    "slotNumber",
    "slotType",
    "cpuType",
    "cpuDescription",
    "endOfSale",
    "endOfLife",
    "captureTime",
    "latest",
    "cardParentId",
)
FAILURE_FIELDS = ("network", "deviceIpAddress", "hostname", "error")


class ExampleError(RuntimeError):
    pass


def parse_networks(value: str) -> list[str]:
    result = sorted({part.strip() for part in value.split(",") if part.strip()})
    if not result:
        raise ExampleError("NETLD_NETWORKS must contain at least one managed network.")
    return result


@dataclass(frozen=True)
class Config:
    base_url: str
    api_key: str
    networks: list[str]
    output_path: Path
    failure_path: Path
    output_format: str
    page_size: int
    scheme: str
    query: str

    @classmethod
    def from_env(cls, env_path: Path, base: Path, format_override: str | None = None):
        load_dotenv(env_path, override=True)
        url, key = (
            os.getenv("NETLD_BASE_URL", "").strip(),
            os.getenv("NETLD_API_KEY", "").strip(),
        )
        if not url or not key:
            raise ExampleError(
                "Set NETLD_BASE_URL and NETLD_API_KEY in the environment file."
            )
        try:
            page_size = int(os.getenv("NETLD_PAGE_SIZE", "500"))
        except ValueError as exc:
            raise ExampleError("NETLD_PAGE_SIZE must be a positive integer.") from exc
        if page_size <= 0:
            raise ExampleError("NETLD_PAGE_SIZE must be a positive integer.")
        output_format = (
            (format_override or os.getenv("NETLD_OUTPUT_FORMAT", "csv")).strip().lower()
        )
        if output_format not in {"csv", "json"}:
            raise ExampleError("NETLD_OUTPUT_FORMAT must be either csv or json.")

        def destination(name: str, default: str) -> Path:
            value = Path(os.getenv(name, "").strip() or default)
            return value if value.is_absolute() else base / value

        return cls(
            url.rstrip("/"),
            key,
            parse_networks(os.getenv("NETLD_NETWORKS", "Default")),
            destination("NETLD_OUTPUT_FILE", f"hardware-inventory.{output_format}"),
            destination("NETLD_FAILURE_FILE", "hardware-failures.csv"),
            output_format,
            page_size,
            os.getenv("NETLD_SEARCH_SCHEME", "ipAddress").strip() or "ipAddress",
            os.getenv("NETLD_SEARCH_QUERY", ""),
        )


class NetLDClient:
    def __init__(self, base_url, api_key, timeout=30):
        self.base_url, self.timeout, self.session = (
            base_url,
            timeout,
            requests.Session(),
        )
        self.session.headers.update({"Authorization": f"Bearer {api_key}"})

    def request(self, method, **kwargs):
        try:
            response = self.session.request(
                method,
                f"{self.base_url}/rest",
                timeout=self.timeout,
                allow_redirects=False,
                **kwargs,
            )
        except requests.RequestException as exc:
            raise ExampleError(f"Could not reach {self.base_url}.") from exc
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

    def login(self):
        self.request("GET")

    def call(self, method, **params):
        response = self.request(
            "POST",
            headers={"Content-Type": "application/json"},
            json={
                "jsonrpc": "2.0",
                "method": method,
                "params": params,
                "id": str(uuid.uuid4()),
            },
        )
        try:
            data = response.json()
        except ValueError as exc:
            raise ExampleError(f"{method} returned invalid JSON.") from exc
        if data.get("error"):
            raise ExampleError(f"{method} failed: {json.dumps(data['error'])}")
        return data.get("result")

    def search_inventory(self, config, offset):
        query = config.query if config.query.endswith("\n") else config.query + "\n"
        result = self.call(
            "Inventory.search",
            network=config.networks,
            scheme=config.scheme,
            query=query,
            pageData={"offset": offset, "pageSize": config.page_size},
            sortColumn="ipAddress",
            descending=False,
        )
        if not isinstance(result, dict):
            raise ExampleError("Inventory.search returned no page data.")
        return result

    def get_device_hardware(self, device):
        result = self.call(
            "Inventory.getDeviceHardware",
            network=device["network"],
            ipAddress=device["ipAddress"],
        )
        if result is None:
            return []
        if not isinstance(result, list):
            raise ExampleError(
                "Inventory.getDeviceHardware returned an invalid collection."
            )
        return result


def inventory_devices(client: Any, config: Config) -> Iterator[dict[str, Any]]:
    offset, total = 0, None
    while True:
        page = client.search_inventory(config, offset)
        devices = page.get("devices") or []
        if not isinstance(devices, list):
            raise ExampleError(
                "Inventory.search returned an invalid devices collection."
            )
        yield from devices
        page_size = int(page.get("pageSize") or config.page_size)
        if page_size <= 0:
            raise ExampleError("Inventory.search returned an invalid page size.")
        if total is None and page.get("total") is not None:
            total = int(page["total"])
        if total is not None and offset + len(devices) >= total:
            return
        if total is None and len(devices) < page_size:
            return
        if not devices:
            raise ExampleError(
                "Inventory.search returned an empty page before the reported total."
            )
        offset += page_size


def hardware_row(device, hardware):
    row = {field: hardware.get(field) for field in HARDWARE_FIELDS}
    row.update(
        network=device.get("network"),
        deviceIpAddress=device.get("ipAddress"),
        hostname=device.get("hostname"),
        adapterId=device.get("adapterId"),
    )
    return row


def export_hardware(client: Any, config: Config) -> tuple[int, int, int]:
    for path in (config.output_path, config.failure_path):
        path.parent.mkdir(parents=True, exist_ok=True)
    temporary: list[Path] = []
    device_count = hardware_count = failure_count = 0
    try:
        with (
            tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                newline="",
                dir=config.output_path.parent,
                prefix=f".{config.output_path.name}.",
                suffix=".tmp",
                delete=False,
            ) as output,
            tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                newline="",
                dir=config.failure_path.parent,
                prefix=f".{config.failure_path.name}.",
                suffix=".tmp",
                delete=False,
            ) as failures,
        ):
            temporary = [Path(output.name), Path(failures.name)]
            failure_writer = csv.DictWriter(failures, fieldnames=FAILURE_FIELDS)
            failure_writer.writeheader()
            writer = (
                csv.DictWriter(output, fieldnames=HARDWARE_FIELDS)
                if config.output_format == "csv"
                else None
            )
            if writer:
                writer.writeheader()
            else:
                output.write("[\n")
            first = True
            for device in inventory_devices(client, config):
                device_count += 1
                try:
                    items = client.get_device_hardware(device)
                except Exception as exc:
                    failure_writer.writerow(
                        {
                            "network": device.get("network"),
                            "deviceIpAddress": device.get("ipAddress"),
                            "hostname": device.get("hostname"),
                            "error": str(exc),
                        }
                    )
                    failure_count += 1
                    continue
                for item in items:
                    row = hardware_row(device, item)
                    if writer:
                        csv_row = dict(row)
                        if isinstance(csv_row.get("latest"), bool):
                            csv_row["latest"] = str(csv_row["latest"]).lower()
                        writer.writerow(csv_row)
                    else:
                        if not first:
                            output.write(",\n")
                        output.write(
                            "\n".join(
                                "  " + line
                                for line in json.dumps(
                                    row, indent=2, ensure_ascii=False
                                ).splitlines()
                            )
                        )
                        first = False
                    hardware_count += 1
            if not writer:
                output.write("\n]\n")
        os.replace(temporary[0], config.output_path)
        os.replace(temporary[1], config.failure_path)
        return device_count, hardware_count, failure_count
    except Exception:
        for path in temporary:
            path.unlink(missing_ok=True)
        raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--env", type=Path, default=Path(__file__).with_name(".env"))
    parser.add_argument("--format", choices=("csv", "json"))
    args = parser.parse_args()
    try:
        config = Config.from_env(args.env, Path(__file__).resolve().parent, args.format)
        client = NetLDClient(config.base_url, config.api_key)
        client.login()
        devices, items, failures = export_hardware(client, config)
        print(
            f"Processed {devices} devices and wrote {items} hardware records to {config.output_path}"
        )
        print(f"Wrote {failures} device lookup failures to {config.failure_path}")
        return 2 if failures else 0
    except (ExampleError, OSError, ValueError, KeyError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
