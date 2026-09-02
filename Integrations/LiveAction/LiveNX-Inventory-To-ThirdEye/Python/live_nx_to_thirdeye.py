#!/usr/bin/env python3

import argparse
import copy
import csv
import io
import ipaddress
import json
import os
import sys
import uuid
from dataclasses import dataclass

import requests
from dotenv import load_dotenv


class BridgeError(RuntimeError):
    pass


def env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def require_env(name):
    value = os.environ.get(name)
    if not value:
        raise BridgeError(f"Set {name} in .env before running this integration.")
    return value


def normalized_header(value):
    return "".join(character for character in value.upper() if character.isalnum())


def sorted_ip_addresses(addresses):
    return sorted(
        addresses,
        key=lambda value: (
            ipaddress.ip_address(value).version,
            ipaddress.ip_address(value),
        ),
    )


def parse_live_nx_device_ips(csv_text, require_vendor=True):
    reader = csv.DictReader(io.StringIO(csv_text.lstrip("\ufeff")))
    if not reader.fieldnames:
        raise BridgeError("The LiveNX device export did not contain a CSV header.")

    fields = {normalized_header(name): name for name in reader.fieldnames if name}
    ip_field = next(
        (
            fields[name]
            for name in ("IPADDRESS", "MANAGEMENTIPADDRESS", "MANAGEMENTIP", "IP")
            if name in fields
        ),
        None,
    )
    if ip_field is None:
        available = ", ".join(reader.fieldnames)
        raise BridgeError(
            "The LiveNX CSV does not contain a recognized IP-address column. "
            f"Available columns: {available}"
        )

    vendor_field = fields.get("VENDOR")
    if require_vendor and vendor_field is None:
        raise BridgeError(
            "LIVENX_REQUIRE_VENDOR=true, but the LiveNX CSV has no VENDOR column."
        )

    addresses = set()
    for row in reader:
        if require_vendor and not (row.get(vendor_field) or "").strip():
            continue

        candidate = (row.get(ip_field) or "").strip()
        try:
            addresses.add(str(ipaddress.ip_address(candidate)))
        except ValueError:
            continue

    return addresses


def prepare_discovery_job(job_data, network, addresses):
    prepared = copy.deepcopy(job_data)
    parameters = prepared.get("jobParameters")
    if not isinstance(parameters, dict):
        raise BridgeError("The selected job has no jobParameters object.")
    if "includedAddresses" not in parameters:
        raise BridgeError(
            "The selected job is not a compatible Discover Devices job: "
            "jobParameters.includedAddresses is missing."
        )

    if "managedNetwork" in prepared:
        prepared["managedNetwork"] = network
    if "managedNetworks" in prepared:
        current = prepared["managedNetworks"]
        prepared["managedNetworks"] = [network] if isinstance(current, list) else network
    if "managedNetwork" in parameters:
        parameters["managedNetwork"] = network

    parameters["includedAddresses"] = ",".join(sorted_ip_addresses(addresses))
    return prepared


@dataclass(frozen=True)
class BridgeConfig:
    live_nx_base_url: str
    live_nx_api_token: str
    live_nx_export_path: str
    netld_base_url: str
    netld_api_key: str
    netld_network: str
    discovery_job_name: str | None
    timeout: float
    require_vendor: bool
    debug: bool

    @classmethod
    def from_env(cls):
        load_dotenv()
        try:
            timeout = float(os.environ.get("REQUEST_TIMEOUT_SECONDS", "30"))
        except ValueError as error:
            raise BridgeError("REQUEST_TIMEOUT_SECONDS must be a number.") from error
        if timeout <= 0:
            raise BridgeError("REQUEST_TIMEOUT_SECONDS must be greater than zero.")

        return cls(
            live_nx_base_url=require_env("LIVENX_BASE_URL").rstrip("/"),
            live_nx_api_token=require_env("LIVENX_API_TOKEN"),
            live_nx_export_path=os.environ.get(
                "LIVENX_DEVICE_EXPORT_PATH", "/v1/devices/export/csv"
            ),
            netld_base_url=require_env("NETLD_BASE_URL").rstrip("/"),
            netld_api_key=require_env("NETLD_API_KEY"),
            netld_network=os.environ.get("NETLD_NETWORK", "Default"),
            discovery_job_name=os.environ.get("NETLD_DISCOVERY_JOB_NAME"),
            timeout=timeout,
            require_vendor=env_bool("LIVENX_REQUIRE_VENDOR", True),
            debug=env_bool("NETLD_DEBUG", False),
        )


class LiveNXClient:
    def __init__(self, base_url, api_token, export_path, timeout: float = 30):
        self.base_url = base_url.rstrip("/")
        self.api_token = api_token
        self.export_path = "/" + export_path.lstrip("/")
        self.timeout = timeout
        self.session = requests.Session()

    def export_devices_csv(self):
        url = f"{self.base_url}{self.export_path}"
        try:
            response = self.session.get(
                url,
                headers={
                    "Accept": "text/csv",
                    "Authorization": f"Bearer {self.api_token}",
                },
                timeout=self.timeout,
                verify=True,
                allow_redirects=False,
            )
        except requests.RequestException as error:
            raise BridgeError(
                f"Could not retrieve the LiveNX device export from {url}."
            ) from error

        if response.is_redirect:
            raise BridgeError(
                "The LiveNX export request was redirected. Confirm LIVENX_BASE_URL, "
                "LIVENX_DEVICE_EXPORT_PATH, and the API token."
            )
        try:
            response.raise_for_status()
        except requests.HTTPError as error:
            raise BridgeError(
                f"LiveNX device export failed with HTTP {response.status_code}."
            ) from error

        response.encoding = response.encoding or "utf-8"
        return response.text


class NetLDClient:
    def __init__(self, base_url, api_key, timeout: float = 30, debug=False):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.debug = debug
        self.session = requests.Session()

    @property
    def headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def login(self):
        try:
            response = self.session.get(
                f"{self.base_url}/rest",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=self.timeout,
                verify=True,
                allow_redirects=False,
            )
        except requests.RequestException as error:
            raise BridgeError(f"Could not reach {self.base_url}.") from error

        if response.is_redirect:
            raise BridgeError("ThirdEye login redirected instead of creating an API session.")
        try:
            response.raise_for_status()
        except requests.HTTPError as error:
            raise BridgeError(
                f"ThirdEye login failed with HTTP {response.status_code}."
            ) from error

    def call(self, method, **params):
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": str(uuid.uuid4()),
        }
        if self.debug:
            print(f"ThirdEye request: {json.dumps(payload, indent=2)}")

        try:
            response = self.session.post(
                f"{self.base_url}/rest",
                headers=self.headers,
                json=payload,
                timeout=self.timeout,
                verify=True,
                allow_redirects=False,
            )
        except requests.RequestException as error:
            raise BridgeError(f"ThirdEye API call {method} failed to connect.") from error

        if response.is_redirect:
            raise BridgeError(f"ThirdEye API call {method} was redirected.")
        try:
            response.raise_for_status()
        except requests.HTTPError as error:
            raise BridgeError(
                f"ThirdEye API call {method} failed with HTTP {response.status_code}."
            ) from error

        try:
            data = response.json()
        except requests.exceptions.JSONDecodeError as error:
            raise BridgeError(f"ThirdEye API call {method} returned invalid JSON.") from error
        if data.get("error"):
            raise BridgeError(f"ThirdEye API call {method} failed: {data['error']}")
        return data.get("result")

    def inventory_addresses(self, network, page_size=500):
        addresses = set()
        offset = 0

        while True:
            page = self.call(
                "Inventory.search",
                network=[network],
                scheme="ipAddress",
                query="\n",
                pageData={"offset": offset, "pageSize": page_size},
                sortColumn="ipAddress",
                descending=False,
            ) or {}
            devices = page.get("devices") or []
            for device in devices:
                candidate = device.get("ipAddress")
                try:
                    addresses.add(str(ipaddress.ip_address(candidate)))
                except (ValueError, TypeError):
                    continue

            offset += len(devices)
            total = page.get("total", offset)
            if not devices or offset >= total:
                return addresses

    def find_job(self, network, job_name, page_size=100):
        offset = 0
        matches = []

        while True:
            page = self.call(
                "Scheduler.searchJobs",
                pageData={
                    "offset": offset,
                    "jobData": [],
                    "pageSize": page_size,
                    "total": 1,
                },
                networks=[network],
                sortColumn="",
                descending=False,
            ) or {}
            jobs = page.get("jobData") or []
            matches.extend(job for job in jobs if job.get("jobName") == job_name)
            offset += len(jobs)
            total = page.get("total", offset)
            if not jobs or offset >= total:
                break

        if not matches:
            raise BridgeError(f'No available job named "{job_name}" was found.')
        if len(matches) > 1:
            ids = ", ".join(str(job.get("jobId")) for job in matches)
            raise BridgeError(f'Multiple jobs named "{job_name}" were found: {ids}')

        job_id = matches[0].get("jobId")
        job_data = self.call("Scheduler.getJob", jobId=job_id)
        if job_data is None:
            raise BridgeError(f"Scheduler.getJob returned no data for job ID {job_id}.")
        return job_data

    def run_now(self, job_data):
        return self.call("Scheduler.runNow", jobData=job_data)


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Find LiveNX devices missing from ThirdEye inventory."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Run the configured ThirdEye discovery job for the missing addresses.",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    config = BridgeConfig.from_env()

    live_nx = LiveNXClient(
        config.live_nx_base_url,
        config.live_nx_api_token,
        config.live_nx_export_path,
        config.timeout,
    )
    netld = NetLDClient(
        config.netld_base_url,
        config.netld_api_key,
        config.timeout,
        config.debug,
    )

    live_nx_addresses = parse_live_nx_device_ips(
        live_nx.export_devices_csv(),
        require_vendor=config.require_vendor,
    )
    netld.login()
    managed_addresses = netld.inventory_addresses(config.netld_network)
    missing_addresses = live_nx_addresses - managed_addresses

    print(f"LiveNX device addresses: {len(live_nx_addresses)}")
    print(f"ThirdEye managed addresses: {len(managed_addresses)}")
    print(f"Missing from ThirdEye: {len(missing_addresses)}")
    for address in sorted_ip_addresses(missing_addresses):
        print(f"  {address}")

    if not missing_addresses:
        print("No discovery is required.")
        return 0
    if not args.apply:
        print("Dry run only. Re-run with --apply to start discovery.")
        return 0
    if not config.discovery_job_name:
        raise BridgeError(
            "Set NETLD_DISCOVERY_JOB_NAME to an existing Discover Devices job "
            "before using --apply."
        )

    job_data = netld.find_job(
        config.netld_network,
        config.discovery_job_name,
    )
    prepared_job = prepare_discovery_job(
        job_data,
        config.netld_network,
        missing_addresses,
    )
    execution = netld.run_now(prepared_job)
    print("Discovery started:")
    print(json.dumps(execution, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BridgeError as error:
        print(f"Error: {error}", file=sys.stderr)
        raise SystemExit(1)
