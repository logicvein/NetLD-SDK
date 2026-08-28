#!/usr/bin/env python3
"""Run device commands through netLD/ThirdEye and export the returned logs."""

from __future__ import annotations

import copy
import json
import os
import re
import sys
import time
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


class ExampleError(RuntimeError):
    pass


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def safe_filename(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip()).strip("._")
    return cleaned or "device"


def build_job(network: str, target: str, commands: list[str], backup: bool = False) -> dict[str, Any]:
    if not commands:
        raise ExampleError("The command file contains no commands.")
    return {
        "jobName": f"API Commands - {target}",
        "managedNetworks": [network],
        "jobType": "Script Tool Job",
        "description": "Ad hoc command execution from the NetLD SDK advanced example",
        "jobParameters": {
            "tool": "org.ziptie.tools.scripts.commandRunner",
            "managedNetwork": network,
            "ipResolutionScheme": "ipCsv",
            "ipResolutionData": f'"{target}@{network}"',
            "backupOnCompletion": str(backup).lower(),
            "input.commandList": "\n".join(commands),
        },
    }


@dataclass(frozen=True)
class Config:
    base_url: str
    api_key: str
    network: str
    target: str
    commands: list[str]
    output_dir: Path
    run_job: bool
    poll_seconds: float
    timeout_seconds: float
    backup: bool

    @classmethod
    def from_env(cls, env_path: Path) -> "Config":
        if load_dotenv is None:
            raise ExampleError("Install the Python dependencies from requirements.txt.")
        load_dotenv(env_path, override=True)
        required = {}
        for name in ("NETLD_BASE_URL", "NETLD_API_KEY", "NETLD_TARGET"):
            value = os.getenv(name, "").strip()
            if not value:
                raise ExampleError(f"Set {name} in .env before running this example.")
            required[name] = value

        command_path = Path(os.getenv("NETLD_COMMAND_FILE", "commands.txt"))
        output_dir = Path(os.getenv("NETLD_OUTPUT_DIR", "output"))
        if not command_path.is_absolute():
            command_path = env_path.parent / command_path
        if not output_dir.is_absolute():
            output_dir = env_path.parent / output_dir
        try:
            commands = [line.strip() for line in command_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        except OSError as exc:
            raise ExampleError(f"Could not read the command file: {command_path}") from exc

        return cls(
            base_url=required["NETLD_BASE_URL"].rstrip("/"),
            api_key=required["NETLD_API_KEY"],
            network=os.getenv("NETLD_NETWORK", "Default").strip() or "Default",
            target=required["NETLD_TARGET"],
            commands=commands,
            output_dir=output_dir,
            run_job=env_bool("NETLD_RUN_JOB"),
            poll_seconds=float(os.getenv("NETLD_POLL_SECONDS", "2")),
            timeout_seconds=float(os.getenv("NETLD_WAIT_TIMEOUT_SECONDS", "300")),
            backup=env_bool("NETLD_BACKUP_ON_COMPLETION"),
        )


class NetLDClient:
    def __init__(self, base_url: str, api_key: str, timeout: float = 30):
        if requests is None:
            raise ExampleError("Install the Python dependencies from requirements.txt.")
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {api_key}"})

    def login(self) -> None:
        self._request("GET", "/rest")

    def _request(self, method: str, path: str, **kwargs: Any):
        try:
            response = self.session.request(
                method,
                f"{self.base_url}{path}",
                timeout=self.timeout,
                allow_redirects=False,
                **kwargs,
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

    def call(self, method: str, **parameters: Any) -> Any:
        response = self._request(
            "POST",
            "/rest",
            headers={"Content-Type": "application/json"},
            json={"jsonrpc": "2.0", "method": method, "params": parameters, "id": str(uuid.uuid4())},
        )
        try:
            data = response.json()
        except ValueError as exc:
            raise ExampleError(f"{method} returned invalid JSON.") from exc
        if data.get("error"):
            raise ExampleError(f"{method} failed: {json.dumps(data['error'])}")
        return data.get("result")

    def download_detail(self, execution_id: int, record_id: int) -> str:
        response = self._request(
            "GET",
            "/servlet/pluginDetail",
            params={"executionId": execution_id, "recordId": record_id},
        )
        return response.content.decode("utf-8", errors="replace")


def wait_for_completion(client: NetLDClient, execution: dict[str, Any], poll: float, timeout: float):
    deadline = time.monotonic() + timeout
    current = copy.deepcopy(execution)
    while current.get("endTime") is None:
        if time.monotonic() >= deadline:
            raise ExampleError(f"Execution {execution.get('id')} did not finish within {timeout:g} seconds.")
        time.sleep(poll)
        current = client.call("Scheduler.getExecutionDataById", executionId=execution["id"])
        if not current:
            raise ExampleError(f"Scheduler returned no data for execution {execution['id']}.")
    return current


def export_details(client: NetLDClient, execution: dict[str, Any], output_dir: Path) -> list[Path]:
    details = client.call("Plugins.getExecutionDetails", executionId=execution["id"]) or []
    if not details:
        raise ExampleError(f"No device output was returned for execution {execution['id']}.")
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for detail in details:
        timestamp = datetime.fromtimestamp(
            int(detail.get("startTime") or execution.get("startTime") or 0) / 1000,
            tz=timezone.utc,
        ).strftime("%Y%m%dT%H%M%SZ")
        identity = safe_filename(
            f"{detail.get('managedNetwork', 'network')}_{detail.get('ipAddress', 'device')}"
        )
        path = output_dir / f"{timestamp}_{execution['id']}_{detail['id']}_{identity}.log"
        content = client.download_detail(execution["id"], detail["id"])
        path.write_text(content, encoding="utf-8")
        paths.append(path)
    return paths


def main() -> int:
    try:
        config = Config.from_env(Path(__file__).with_name(".env"))
        job = build_job(config.network, config.target, config.commands, config.backup)
        print(json.dumps(job, indent=2))
        if not config.run_job:
            print("Dry run only. Set NETLD_RUN_JOB=true after reviewing this job.")
            return 0

        client = NetLDClient(config.base_url, config.api_key)
        client.login()
        execution = client.call("Scheduler.runNow", jobData=job)
        final = wait_for_completion(client, execution, config.poll_seconds, config.timeout_seconds)
        print(json.dumps(final, indent=2))
        for path in export_details(client, final, config.output_dir):
            print(f"Wrote {path}")
        if final.get("status") not in (None, "OK"):
            raise ExampleError(f"Execution completed with status {final.get('status')}.")
        return 0
    except (ExampleError, OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
