#!/usr/bin/env python3
"""Export collected device interfaces from netLD/ThirdEye to CSV."""

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


INTERFACE_FIELDS = (
    "network", "deviceIpAddress", "hostname", "interfaceId", "interfaceIndex",
    "name", "ifName", "type", "description", "comment", "macAddress", "mtu",
    "speed", "adminUp", "vrfName", "ipAddresses",
)
FAILURE_FIELDS = ("network", "deviceIpAddress", "hostname", "error")


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
    failure_path: Path
    page_size: int
    scheme: str
    query: str

    @classmethod
    def from_env(cls, env_path: Path, output_base: Path) -> "Config":
        load_dotenv(env_path, override=True)
        base_url = os.getenv("NETLD_BASE_URL", "").strip()
        api_key = os.getenv("NETLD_API_KEY", "").strip()
        if not base_url:
            raise ExampleError("Set NETLD_BASE_URL in the environment file.")
        if not api_key:
            raise ExampleError("Set NETLD_API_KEY in the environment file.")
        try:
            page_size = int(os.getenv("NETLD_PAGE_SIZE", "500"))
        except ValueError as exc:
            raise ExampleError("NETLD_PAGE_SIZE must be a positive integer.") from exc
        if page_size <= 0:
            raise ExampleError("NETLD_PAGE_SIZE must be a positive integer.")

        def output_path(name: str, default: str) -> Path:
            value = Path(os.getenv(name, default))
            return value if value.is_absolute() else output_base / value

        return cls(
            base_url=base_url.rstrip("/"), api_key=api_key,
            networks=parse_networks(os.getenv("NETLD_NETWORKS", "Default")),
            output_path=output_path("NETLD_OUTPUT_FILE", "interfaces.csv"),
            failure_path=output_path("NETLD_FAILURE_FILE", "interface-failures.csv"),
            page_size=page_size,
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

    def search_inventory(self, networks: list[str], scheme: str, query: str, offset: int, page_size: int):
        result = self.call(
            "Inventory.search", network=networks, scheme=scheme,
            query=query if query.endswith("\n") else f"{query}\n",
            pageData={"offset": offset, "pageSize": page_size},
            sortColumn="ipAddress", descending=False,
        )
        if not isinstance(result, dict):
            raise ExampleError("Inventory.search returned no page data.")
        return result

    def get_device_interfaces(self, network: str, ip_address: str):
        result = self.call("Inventory.getDeviceInterfaces", network=network, ipAddress=ip_address)
        if result is None:
            return []
        if not isinstance(result, list):
            raise ExampleError("Inventory.getDeviceInterfaces returned an invalid collection.")
        return result


def inventory_pages(client: Any, config: Config) -> Iterator[list[dict[str, Any]]]:
    offset = 0
    total: int | None = None
    while True:
        page = client.search_inventory(config.networks, config.scheme, config.query, offset, config.page_size)
        devices = page.get("devices") or []
        if not isinstance(devices, list):
            raise ExampleError("Inventory.search returned an invalid devices collection.")
        yield devices
        returned_page_size = int(page.get("pageSize") or config.page_size)
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


def flatten_ip_addresses(interface: dict[str, Any]) -> str:
    values = []
    for address in interface.get("ipAddresses") or []:
        value = str(address.get("ipAddress") or "").strip()
        if not value:
            continue
        prefix = address.get("cidrPrefix")
        values.append(f"{value}/{prefix}" if prefix is not None else value)
    return ";".join(values)


def interface_row(device: dict[str, Any], interface: dict[str, Any]) -> dict[str, Any]:
    admin_up = interface.get("adminUp")
    if isinstance(admin_up, bool):
        admin_up = str(admin_up).lower()
    return {
        "network": device.get("network"), "deviceIpAddress": device.get("ipAddress"),
        "hostname": device.get("hostname"), "interfaceId": interface.get("id"),
        "interfaceIndex": interface.get("index"), "name": interface.get("name"),
        "ifName": interface.get("ifName"), "type": interface.get("type"),
        "description": interface.get("description"), "comment": interface.get("comment"),
        "macAddress": interface.get("macAddress"), "mtu": interface.get("mtu"),
        "speed": interface.get("speed"), "adminUp": admin_up,
        "vrfName": interface.get("vrfName"), "ipAddresses": flatten_ip_addresses(interface),
    }


def export_interfaces(client: Any, config: Config) -> tuple[int, int, int]:
    for destination in (config.output_path, config.failure_path):
        destination.parent.mkdir(parents=True, exist_ok=True)
    temporary_paths: list[Path] = []
    device_count = interface_count = failure_count = 0
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="", dir=config.output_path.parent,
            prefix=f".{config.output_path.name}.", suffix=".tmp", delete=False,
        ) as interface_output, tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="", dir=config.failure_path.parent,
            prefix=f".{config.failure_path.name}.", suffix=".tmp", delete=False,
        ) as failure_output:
            temporary_paths = [Path(interface_output.name), Path(failure_output.name)]
            interface_writer = csv.DictWriter(interface_output, fieldnames=INTERFACE_FIELDS)
            failure_writer = csv.DictWriter(failure_output, fieldnames=FAILURE_FIELDS)
            interface_writer.writeheader()
            failure_writer.writeheader()
            for devices in inventory_pages(client, config):
                for device in devices:
                    device_count += 1
                    try:
                        interfaces = client.get_device_interfaces(device["network"], device["ipAddress"])
                    except Exception as exc:  # Preserve other devices when one lookup fails.
                        failure_writer.writerow({
                            "network": device.get("network"), "deviceIpAddress": device.get("ipAddress"),
                            "hostname": device.get("hostname"), "error": str(exc),
                        })
                        failure_count += 1
                        continue
                    for interface in interfaces:
                        interface_writer.writerow(interface_row(device, interface))
                        interface_count += 1
        os.replace(temporary_paths[0], config.output_path)
        os.replace(temporary_paths[1], config.failure_path)
        return device_count, interface_count, failure_count
    except Exception:
        for temporary_path in temporary_paths:
            temporary_path.unlink(missing_ok=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--env", type=Path, default=Path(__file__).with_name(".env"))
    args = parser.parse_args()
    try:
        base = Path(__file__).resolve().parent
        config = Config.from_env(args.env, base)
        client = NetLDClient(config.base_url, config.api_key)
        client.login()
        devices, interfaces, failures = export_interfaces(client, config)
        print(f"Processed {devices} devices and wrote {interfaces} interfaces to {config.output_path}")
        print(f"Wrote {failures} device lookup failures to {config.failure_path}")
        return 2 if failures else 0
    except (ExampleError, OSError, ValueError, KeyError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
