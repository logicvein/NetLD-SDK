#!/usr/bin/env python3
"""Incrementally archive output from completed netLD/ThirdEye job executions."""

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

import requests
from dotenv import load_dotenv


STATE_FORMAT = "logicvein-netld-job-execution-output-state"
RUN_FORMAT = "logicvein-netld-job-execution-output-run"
FORMAT_VERSION = 1


class ExampleError(RuntimeError):
    pass


def safe_name(value: str, fallback: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip()).strip("._")
    return cleaned or fallback


def generated_at() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class Config:
    base_url: str
    api_key: str
    output_dir: Path
    state_path: Path
    report_path: Path
    page_size: int
    initial_mode: str
    search_scheme: str
    search_data: str
    job_type: str
    job_name: str

    @classmethod
    def from_env(cls, env_path: Path, base: Path) -> "Config":
        load_dotenv(env_path, override=True)
        url = os.getenv("NETLD_BASE_URL", "").strip()
        key = os.getenv("NETLD_API_KEY", "").strip()
        if not url or not key:
            raise ExampleError("Set NETLD_BASE_URL and NETLD_API_KEY in the environment file.")

        def destination(name: str, default: str) -> Path:
            value = Path(os.getenv(name, default))
            return value if value.is_absolute() else base / value

        try:
            page_size = int(os.getenv("NETLD_PAGE_SIZE", "100"))
        except ValueError as exc:
            raise ExampleError("NETLD_PAGE_SIZE must be a positive integer.") from exc
        if page_size <= 0:
            raise ExampleError("NETLD_PAGE_SIZE must be a positive integer.")
        initial_mode = os.getenv("NETLD_INITIAL_MODE", "latest").strip().lower()
        if initial_mode not in {"latest", "all"}:
            raise ExampleError("NETLD_INITIAL_MODE must be latest or all.")
        return cls(
            url.rstrip("/"),
            key,
            destination("NETLD_OUTPUT_DIR", "job-execution-outputs"),
            destination("NETLD_STATE_FILE", "job-execution-output-state.json"),
            destination("NETLD_RUN_REPORT_FILE", "job-execution-output-run.json"),
            page_size,
            initial_mode,
            os.getenv("NETLD_SEARCH_SCHEME", "").strip(),
            os.getenv("NETLD_SEARCH_DATA", "").strip(),
            os.getenv("NETLD_JOB_TYPE", "Script Tool Job").strip(),
            os.getenv("NETLD_JOB_NAME", "").strip(),
        )


class NetLDClient:
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
            raise ExampleError(f"Request redirected to {response.headers.get('Location', '')}.")
        try:
            response.raise_for_status()
        except requests.RequestException as exc:
            raise ExampleError(f"Request failed with HTTP {response.status_code}.") from exc
        return response

    def login(self) -> None:
        self.request("GET", "/rest")

    def call(self, method: str, parameters: dict[str, Any]) -> Any:
        response = self.request(
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

    def search_execution_page(self, offset: int, page_size: int) -> dict[str, Any]:
        result = self.call(
            "Scheduler.searchExecutions",
            {
                "scheme": self.config.search_scheme,
                "data": self.config.search_data,
                "pageData": {"offset": offset, "executionData": [], "pageSize": page_size, "total": 0},
                "sortColumn": "endTime",
                "descending": True,
            },
        )
        if not isinstance(result, dict) or not isinstance(result.get("executionData"), list):
            raise ExampleError("Scheduler.searchExecutions returned an invalid page.")
        return result

    def execution_details(self, execution_id: int) -> list[dict[str, Any]]:
        result = self.call("Plugins.getExecutionDetails", {"executionId": execution_id})
        if result is None:
            return []
        if not isinstance(result, list):
            raise ExampleError("Plugins.getExecutionDetails returned an invalid collection.")
        return result

    def download_detail(self, execution_id: int, record_id: int) -> bytes:
        return self.request(
            "GET",
            "/servlet/pluginDetail",
            params={"executionId": execution_id, "recordId": record_id},
        ).content


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"format": STATE_FORMAT, "formatVersion": FORMAT_VERSION}
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ExampleError(f"Could not read archive state: {path}") from exc
    if state.get("format") != STATE_FORMAT or state.get("formatVersion") != FORMAT_VERSION:
        raise ExampleError("The job-execution state file has an unsupported format.")
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
    write_atomic(path, (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode())


def execution_end(execution: dict[str, Any]) -> int | None:
    value = execution.get("endTime")
    return int(value) if value is not None else None


def execution_id(execution: dict[str, Any]) -> int:
    value = execution.get("id", execution.get("executionId"))
    if value is None:
        raise ExampleError("Scheduler.searchExecutions returned a record without an execution ID.")
    return int(value)


def eligible(config: Config, execution: dict[str, Any]) -> bool:
    return (not config.job_type or execution.get("jobType") == config.job_type) and (
        not config.job_name or execution.get("jobName") == config.job_name
    )


def is_new_execution(
    execution: dict[str, Any], watermark: int | None, watermark_ids: set[int]
) -> bool:
    end_time = execution_end(execution)
    if end_time is None:
        return False
    return (
        watermark is None
        or end_time > watermark
        or (end_time == watermark and execution_id(execution) not in watermark_ids)
    )


def collect_executions(
    client: Any, config: Config, state: dict[str, Any]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    watermark = int(state["lastEndTime"]) if state.get("lastEndTime") is not None else None
    watermark_ids = {int(value) for value in state.get("executionIdsAtLastEndTime", [])}
    observed: list[dict[str, Any]] = []
    offset = 0
    reported_total: int | None = None

    while reported_total is None or offset < reported_total:
        page = client.search_execution_page(offset, config.page_size)
        batch = page["executionData"]
        page_offset = int(page.get("offset", offset))
        page_total = int(page.get("total", page_offset + len(batch)))
        reported_total = page_total if reported_total is None else max(reported_total, page_total)
        passed_watermark = False
        for execution in batch:
            end_time = execution_end(execution)
            if end_time is None:
                continue
            if watermark is not None and end_time < watermark:
                passed_watermark = True
                break
            observed.append(execution)

        if passed_watermark or (watermark is None and config.initial_mode == "latest"):
            break
        next_offset = page_offset + len(batch)
        if next_offset >= reported_total:
            break
        if not batch or next_offset <= offset:
            raise ExampleError("Execution paging stopped before all results were returned.")
        offset = next_offset

    if watermark is None and config.initial_mode == "latest":
        return observed, []

    candidates = [
        execution
        for execution in observed
        if is_new_execution(execution, watermark, watermark_ids)
        and eligible(config, execution)
    ]
    candidates.sort(key=lambda item: (execution_end(item) or 0, execution_id(item)))
    return observed, candidates


def archive_execution(client: Any, config: Config, execution: dict[str, Any]) -> dict[str, Any]:
    exec_id = execution_id(execution)
    end_time = execution_end(execution)
    if end_time is None:
        raise ExampleError(f"Execution {exec_id} has not completed.")
    date = datetime.fromtimestamp(end_time / 1000, timezone.utc).strftime("%Y-%m-%d")
    directory = config.output_dir / date / f"{exec_id}_{safe_name(str(execution.get('jobName', 'job')), 'job')}"
    details = client.execution_details(exec_id)
    outputs = []
    for detail in details:
        detail_id = int(detail["id"])
        identity = safe_name(
            f"{detail.get('managedNetwork', 'network')}_{detail.get('ipAddress', 'device')}",
            "device",
        )
        content_path = directory / f"{detail_id}_{identity}.log"
        metadata_path = directory / f"{detail_id}_{identity}.metadata.json"
        content = client.download_detail(exec_id, detail_id)
        write_atomic(content_path, content)
        write_json(metadata_path, {"executionId": exec_id, "detail": detail, "contentFile": content_path.name})
        outputs.append(
            {
                "detailId": detail_id,
                "bytes": len(content),
                "contentFile": str(content_path.relative_to(config.output_dir)),
                "metadataFile": str(metadata_path.relative_to(config.output_dir)),
            }
        )
    execution_path = directory / "execution.metadata.json"
    write_json(execution_path, {"execution": execution, "outputCount": len(outputs)})
    return {
        "executionId": exec_id,
        "endTime": end_time,
        "jobName": execution.get("jobName"),
        "outputCount": len(outputs),
        "metadataFile": str(execution_path.relative_to(config.output_dir)),
        "outputs": outputs,
    }


def advance_state(state: dict[str, Any], observed: list[dict[str, Any]]) -> None:
    completed = [execution for execution in observed if execution_end(execution) is not None]
    if not completed:
        return
    newest = max(execution_end(execution) or 0 for execution in completed)
    ids = {execution_id(execution) for execution in completed if execution_end(execution) == newest}
    if state.get("lastEndTime") is not None and newest == int(state["lastEndTime"]):
        ids.update(int(value) for value in state.get("executionIdsAtLastEndTime", []))
    state.update(lastEndTime=newest, executionIdsAtLastEndTime=sorted(ids))


def archive_job_execution_outputs(
    client: Any, config: Config, timestamp: str | None = None
) -> dict[str, Any]:
    state = load_state(config.state_path)
    initial_baseline = state.get("lastEndTime") is None and config.initial_mode == "latest"
    observed, candidates = collect_executions(client, config, state)
    archived, failures = [], []
    for execution in candidates:
        try:
            archived.append(archive_execution(client, config, execution))
        except Exception as exc:
            failures.append({"executionId": execution.get("id"), "error": str(exc)})
    if not failures:
        advance_state(state, observed)
    report = {
        "format": RUN_FORMAT,
        "formatVersion": FORMAT_VERSION,
        "generatedAt": timestamp or generated_at(),
        "initialBaseline": initial_baseline,
        "observedCount": len(observed),
        "candidateCount": len(candidates),
        "archivedCount": len(archived),
        "outputCount": sum(item["outputCount"] for item in archived),
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
        base = Path(__file__).resolve().parent
        config = Config.from_env(args.env, base)
        client = NetLDClient(config)
        client.login()
        report = archive_job_execution_outputs(client, config)
        if report["initialBaseline"]:
            print("Recorded the latest completed execution as the initial baseline.")
        print(
            f"Archived {report['archivedCount']} executions and {report['outputCount']} outputs; "
            f"recorded {report['failureCount']} failures in {config.report_path}"
        )
        return 2 if report["failureCount"] else 0
    except (ExampleError, OSError, ValueError, KeyError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
