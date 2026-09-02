#!/usr/bin/env python3
"""Report netLD configuration changes through a PRTG Script v2 sensor."""

from __future__ import annotations

import argparse
import copy
import json
import os
import shlex
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

import requests
from dotenv import load_dotenv


class ProbeError(RuntimeError):
    """A safe, user-facing integration error."""


def utc_string(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S-00:00")


def from_epoch_milliseconds(value: int) -> datetime:
    return datetime.fromtimestamp(value / 1000, tz=timezone.utc)


def env_bool(value: str | None, default: bool = False) -> bool:
    if value is None or not value.strip():
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Config:
    base_url: str
    api_key: str
    networks: tuple[str, ...]
    report_job_name: str
    report_job_network: str
    state_path: Path
    timeout: int
    warning_on_change: bool

    @classmethod
    def from_env(cls, env_path: Path) -> "Config":
        load_dotenv(env_path, override=True)
        base_url = os.getenv("NETLD_BASE_URL", "").strip()
        api_key = os.getenv("NETLD_API_KEY", "").strip()
        if not base_url:
            raise ProbeError("Set NETLD_BASE_URL in .env before running this integration.")
        if not api_key:
            raise ProbeError("Set NETLD_API_KEY in .env before running this integration.")

        state_path = Path(os.getenv("PRTG_STATE_PATH", "config-change-probe-state.json"))
        if not state_path.is_absolute():
            state_path = env_path.parent / state_path
        networks = tuple(
            item.strip() for item in os.getenv("NETLD_NETWORKS", "").split(",") if item.strip()
        )
        try:
            timeout = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "30"))
        except ValueError as exc:
            raise ProbeError("REQUEST_TIMEOUT_SECONDS must be an integer.") from exc
        return cls(
            base_url=base_url.rstrip("/"),
            api_key=api_key,
            networks=networks,
            report_job_name=os.getenv("NETLD_REPORT_JOB_NAME", "PRTG Realtime Changes"),
            report_job_network=os.getenv("NETLD_REPORT_JOB_NETWORK", "Default"),
            state_path=state_path,
            timeout=timeout,
            warning_on_change=env_bool(os.getenv("PRTG_WARNING_ON_CHANGE"), True),
        )


class StateStore:
    def __init__(self, path: Path):
        self.path = path

    def read_or_initialize(self) -> str:
        if not self.path.exists():
            initial = utc_string(datetime.now(timezone.utc))
            self.write(initial)
            return initial
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))["lastRun"]
            datetime.fromisoformat(value)
            return value
        except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise ProbeError(f"The probe state file is invalid: {self.path}") from exc

    def write(self, last_run: str) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                "w", encoding="utf-8", dir=self.path.parent, delete=False
            ) as handle:
                temporary = Path(handle.name)
                json.dump({"lastRun": last_run}, handle, indent=2)
                handle.write("\n")
            os.replace(temporary, self.path)
        except OSError as exc:
            raise ProbeError(f"Could not write the probe state file: {self.path}") from exc
        finally:
            if temporary and temporary.exists():
                temporary.unlink()


class NetLDClient:
    def __init__(self, base_url: str, api_key: str, timeout: int):
        self.url = f"{base_url.rstrip('/')}/rest"
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {"Authorization": f"Bearer {api_key}", "Accept": "application/json"}
        )

    def connect(self) -> None:
        try:
            response = self.session.get(self.url, timeout=self.timeout, allow_redirects=False)
            response.raise_for_status()
        except requests.RequestException as exc:
            status = getattr(exc.response, "status_code", None)
            detail = f" with HTTP {status}" if status else ""
            raise ProbeError(f"netLD login failed{detail}.") from exc

    def call(self, method: str, parameters: dict[str, Any] | list[Any]) -> Any:
        payload = {"jsonrpc": "2.0", "method": method, "params": parameters, "id": method}
        try:
            response = self.session.post(self.url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as exc:
            status = getattr(exc.response, "status_code", None)
            detail = f" with HTTP {status}" if status else ""
            raise ProbeError(f"netLD API call {method} failed{detail}.") from exc
        except ValueError as exc:
            raise ProbeError(f"netLD API call {method} returned invalid JSON.") from exc
        if data.get("error"):
            raise ProbeError(f"netLD API call {method} failed: {json.dumps(data['error'])}")
        return data.get("result")

    def job_by_name(self, network: str, job_name: str) -> dict[str, Any]:
        matches: list[dict[str, Any]] = []
        offset = 0
        while True:
            page = self.call(
                "Scheduler.searchJobs",
                {
                    "pageData": {"offset": offset, "jobData": [], "pageSize": 100, "total": 1},
                    "networks": [network],
                    "sortColumn": "",
                    "descending": False,
                },
            )
            jobs = page.get("jobData", [])
            matches.extend(job for job in jobs if job.get("jobName") == job_name)
            offset += len(jobs)
            if not jobs or offset >= int(page.get("total", offset)):
                break
        if len(matches) != 1:
            raise ProbeError(
                f'Expected one available job named "{job_name}"; found {len(matches)}.'
            )
        job_id = matches[0].get("jobId")
        job = self.call("Scheduler.getJob", {"jobId": job_id})
        if not job:
            raise ProbeError(f"Scheduler.getJob returned no data for job ID {job_id}.")
        return job


def summarize_changes(
    changes: Iterable[dict[str, Any]], networks: Iterable[str] = ()
) -> dict[str, Any]:
    allowed = set(networks)
    by_network: dict[str, set[str]] = {}
    timestamps: list[int] = []
    for change in changes:
        network = str(change.get("managedNetwork", ""))
        address = str(change.get("ipAddress", ""))
        if not network or not address or (allowed and network not in allowed):
            continue
        try:
            changed = int(change["lastChanged"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ProbeError("A configuration-change record has an invalid lastChanged value.") from exc
        by_network.setdefault(network, set()).add(address)
        timestamps.append(changed)
    return {
        "by_network": by_network,
        "device_count": sum(len(addresses) for addresses in by_network.values()),
        "earliest": min(timestamps) if timestamps else None,
        "latest": max(timestamps) if timestamps else None,
    }


def prepare_report_job(
    job_data: dict[str, Any], network: str, addresses: Iterable[str], earliest: int, latest: int
) -> dict[str, Any]:
    prepared = copy.deepcopy(job_data)
    parameters = prepared.get("jobParameters")
    if not isinstance(parameters, dict):
        raise ProbeError("The selected report job has no jobParameters object.")
    for name in ("input.start_date", "input.end_date", "ipResolutionData"):
        if name not in parameters:
            raise ProbeError(f"The selected report job is missing jobParameters.{name}.")
    if "managedNetwork" in prepared:
        prepared["managedNetwork"] = network
    if "managedNetwork" in parameters:
        parameters["managedNetwork"] = network
    parameters["input.start_date"] = utc_string(
        from_epoch_milliseconds(earliest) - timedelta(seconds=1)
    )
    parameters["input.end_date"] = utc_string(
        from_epoch_milliseconds(latest) + timedelta(seconds=1)
    )
    parameters["ipResolutionData"] = ",".join(
        f"{address}@{network}" for address in sorted(set(addresses))
    )
    return prepared


def success_result(device_count: int, warning_on_change: bool = True) -> dict[str, Any]:
    word = "device" if device_count == 1 else "devices"
    message = (
        f"Configuration changes on {device_count} {word}." if device_count else "OK"
    )
    return {
        "version": 3,
        "status": "warning" if device_count and warning_on_change else "ok",
        "message": message,
        "channels": [
            {
                "id": 10,
                "name": "Configuration Changes",
                "type": "integer",
                "kind": "count",
                "value": device_count,
            }
        ],
    }


def error_result(message: str) -> dict[str, Any]:
    return {"version": 3, "status": "error", "message": message}


def run(config: Config) -> dict[str, Any]:
    state = StateStore(config.state_path)
    last_run = state.read_or_initialize()
    client = NetLDClient(config.base_url, config.api_key, config.timeout)
    client.connect()
    changes = client.call("Configuration.retrieveConfigsSince", [last_run]) or []
    summary = summarize_changes(changes, config.networks)
    if summary["device_count"]:
        job = client.job_by_name(config.report_job_network, config.report_job_name)
        for network in sorted(summary["by_network"]):
            prepared = prepare_report_job(
                job,
                network,
                summary["by_network"][network],
                summary["earliest"],
                summary["latest"],
            )
            client.call("Scheduler.runNow", {"jobData": prepared})
        state.write(utc_string(from_epoch_milliseconds(summary["latest"])))
    return success_result(summary["device_count"], config.warning_on_change)


def input_arguments() -> list[str]:
    if len(sys.argv) > 1:
        return sys.argv[1:]
    if not sys.stdin.isatty():
        return shlex.split(sys.stdin.read().strip())
    return []


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--env-path", type=Path, default=Path(__file__).with_name(".env"))
    try:
        args = parser.parse_args(input_arguments())
        result = run(Config.from_env(args.env_path.resolve()))
    except Exception as exc:  # PRTG must always receive valid sensor JSON.
        result = error_result(str(exc))
    print(json.dumps(result, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
