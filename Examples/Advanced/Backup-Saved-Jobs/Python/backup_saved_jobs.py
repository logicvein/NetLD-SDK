#!/usr/bin/env python3
"""Back up complete netLD/ThirdEye saved-job definitions to JSON."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

import requests
from dotenv import load_dotenv


FORMAT_NAME = "logicvein-netld-saved-job-backup"
FAILURE_FORMAT_NAME = "logicvein-netld-saved-job-backup-failures"
FORMAT_VERSION = 1


class ExampleError(RuntimeError):
    pass


def parse_networks(value: str) -> list[str]:
    networks = sorted({item.strip() for item in value.split(",") if item.strip()})
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
            page_size = int(os.getenv("NETLD_JOB_PAGE_SIZE", "100"))
        except ValueError as exc:
            raise ExampleError("NETLD_JOB_PAGE_SIZE must be a positive integer.") from exc
        if page_size <= 0:
            raise ExampleError("NETLD_JOB_PAGE_SIZE must be a positive integer.")

        def destination(name: str, default: str) -> Path:
            value = Path(os.getenv(name, default))
            return value if value.is_absolute() else output_base / value

        return cls(
            base_url.rstrip("/"), api_key,
            parse_networks(os.getenv("NETLD_NETWORKS", "Default")),
            destination("NETLD_OUTPUT_FILE", "saved-jobs.json"),
            destination("NETLD_FAILURE_FILE", "saved-job-failures.json"),
            page_size,
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

    def search_jobs(self, networks: list[str], offset: int, page_size: int):
        result = self.call(
            "Scheduler.searchJobs",
            pageData={"offset": offset, "jobData": [], "pageSize": page_size, "total": 1},
            networks=networks, sortColumn="", descending=False,
        )
        if not isinstance(result, dict):
            raise ExampleError("Scheduler.searchJobs returned no page data.")
        return result

    def get_job(self, job_id: int):
        result = self.call("Scheduler.getJob", jobId=job_id)
        if not isinstance(result, dict):
            raise ExampleError(f"Scheduler.getJob returned no data for job ID {job_id}.")
        return result


def shallow_job_pages(client: Any, config: Config) -> Iterator[list[dict[str, Any]]]:
    offset = 0
    total: int | None = None
    while True:
        page = client.search_jobs(config.networks, offset, config.page_size)
        jobs = page.get("jobData") or []
        if not isinstance(jobs, list):
            raise ExampleError("Scheduler.searchJobs returned an invalid jobData collection.")
        yield jobs
        returned_page_size = int(page.get("pageSize") or config.page_size)
        if returned_page_size <= 0:
            raise ExampleError("Scheduler.searchJobs returned an invalid page size.")
        if total is None and page.get("total") is not None:
            total = int(page["total"])
        if total is not None and offset + len(jobs) >= total:
            return
        if total is None and len(jobs) < returned_page_size:
            return
        if not jobs:
            raise ExampleError("Scheduler.searchJobs returned an empty page before the reported total.")
        offset += returned_page_size


def collect_jobs(client: Any, config: Config) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    jobs: dict[int, dict[str, Any]] = {}
    failures: dict[int, dict[str, Any]] = {}
    for shallow_jobs in shallow_job_pages(client, config):
        for shallow in shallow_jobs:
            job_id = shallow.get("jobId")
            if not isinstance(job_id, int):
                raise ExampleError("Scheduler.searchJobs returned a job without an integer jobId.")
            if job_id in jobs or job_id in failures:
                continue
            try:
                jobs[job_id] = client.get_job(job_id)
            except Exception as exc:  # Preserve the remaining readable jobs.
                failures[job_id] = {
                    "jobId": job_id,
                    "jobName": shallow.get("jobName"),
                    "error": str(exc),
                }
    return [jobs[key] for key in sorted(jobs)], [failures[key] for key in sorted(failures)]


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_documents(
    jobs: list[dict[str, Any]], failures: list[dict[str, Any]],
    networks: list[str], exported_at: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    timestamp = exported_at or utc_timestamp()
    backup = {
        "format": FORMAT_NAME,
        "formatVersion": FORMAT_VERSION,
        "exportedAt": timestamp,
        "networks": sorted(networks),
        "complete": not failures,
        "jobCount": len(jobs),
        "jobs": jobs,
    }
    failure_report = {
        "format": FAILURE_FORMAT_NAME,
        "formatVersion": FORMAT_VERSION,
        "exportedAt": timestamp,
        "failureCount": len(failures),
        "failures": failures,
    }
    return backup, failure_report


def write_json_atomic(path: Path, document: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent,
            prefix=f".{path.name}.", suffix=".tmp", delete=False,
        ) as output:
            temporary_path = Path(output.name)
            json.dump(document, output, indent=2, sort_keys=True, ensure_ascii=False)
            output.write("\n")
        os.replace(temporary_path, path)
    except Exception:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
        raise


def backup_saved_jobs(client: Any, config: Config, exported_at: str | None = None) -> tuple[int, int]:
    jobs, failures = collect_jobs(client, config)
    backup, failure_report = build_documents(jobs, failures, config.networks, exported_at)
    write_json_atomic(config.output_path, backup)
    write_json_atomic(config.failure_path, failure_report)
    return len(jobs), len(failures)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--env", type=Path, default=Path(__file__).with_name(".env"))
    args = parser.parse_args()
    try:
        base = Path(__file__).resolve().parent
        config = Config.from_env(args.env, base)
        client = NetLDClient(config.base_url, config.api_key)
        client.login()
        jobs, failures = backup_saved_jobs(client, config)
        print(f"Wrote {jobs} complete saved jobs to {config.output_path}")
        print(f"Wrote {failures} retrieval failures to {config.failure_path}")
        return 2 if failures else 0
    except (ExampleError, OSError, ValueError, KeyError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
