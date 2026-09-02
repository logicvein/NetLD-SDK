import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config_change_probe import (  # noqa: E402
    Config,
    ProbeError,
    StateStore,
    error_result,
    prepare_report_job,
    success_result,
    summarize_changes,
    run,
)


class FakeClient:
    instances = []
    changes = [
        {"managedNetwork": "East", "ipAddress": "192.0.2.1", "lastChanged": 1000},
        {"managedNetwork": "West", "ipAddress": "198.51.100.1", "lastChanged": 2000},
    ]
    fail_after = None

    def __init__(self, *_args):
        self.started = []
        FakeClient.instances.append(self)

    def connect(self):
        pass

    def job_by_name(self, _network, _job_name):
        return {
            "managedNetwork": "Default",
            "jobParameters": {
                "managedNetwork": "Default",
                "input.start_date": "",
                "input.end_date": "",
                "ipResolutionData": "",
            },
        }

    def call(self, method, parameters):
        if method == "Configuration.retrieveConfigsSince":
            return self.changes
        if method == "Scheduler.runNow":
            if self.fail_after is not None and len(self.started) >= self.fail_after:
                raise ProbeError("report failed")
            self.started.append(parameters["jobData"])
            return {"executionId": len(self.started)}
        raise AssertionError(method)


class ConfigChangeProbeTests(unittest.TestCase):
    def setUp(self):
        FakeClient.instances.clear()

    def config(self, state_path):
        return Config(
            base_url="https://netld.example.com",
            api_key="test-key",
            networks=(),
            report_job_name="PRTG Realtime Changes",
            report_job_network="Default",
            state_path=state_path,
            timeout=30,
            warning_on_change=True,
        )

    def test_summary_filters_and_deduplicates(self):
        summary = summarize_changes(
            [
                {"managedNetwork": "East", "ipAddress": "192.0.2.2", "lastChanged": 2000},
                {"managedNetwork": "East", "ipAddress": "192.0.2.1", "lastChanged": 1000},
                {"managedNetwork": "East", "ipAddress": "192.0.2.1", "lastChanged": 1500},
                {"managedNetwork": "West", "ipAddress": "198.51.100.1", "lastChanged": 3000},
            ],
            ["East"],
        )
        self.assertEqual(summary["device_count"], 2)
        self.assertEqual(summary["earliest"], 1000)
        self.assertEqual(summary["latest"], 2000)

    def test_report_job_is_copied_and_prepared(self):
        original = {
            "managedNetwork": "Default",
            "jobParameters": {
                "managedNetwork": "Default",
                "input.start_date": "",
                "input.end_date": "",
                "ipResolutionData": "",
            },
        }
        prepared = prepare_report_job(
            original, "East", ["192.0.2.2", "192.0.2.1", "192.0.2.1"], 1000, 2000
        )
        self.assertEqual(original["managedNetwork"], "Default")
        self.assertEqual(prepared["managedNetwork"], "East")
        self.assertEqual(
            prepared["jobParameters"]["ipResolutionData"],
            "192.0.2.1@East,192.0.2.2@East",
        )

    def test_prtg_results_use_schema_version_three(self):
        result = success_result(2)
        self.assertEqual(result["version"], 3)
        self.assertEqual(result["status"], "warning")
        self.assertEqual(result["channels"][0]["id"], 10)
        self.assertEqual(error_result("bad"), {"version": 3, "status": "error", "message": "bad"})

    def test_state_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            store = StateStore(Path(directory) / "state.json")
            store.write("2026-01-01T00:00:00-00:00")
            self.assertEqual(store.read_or_initialize(), "2026-01-01T00:00:00-00:00")
            self.assertEqual(json.loads(store.path.read_text())["lastRun"], "2026-01-01T00:00:00-00:00")

    def test_run_starts_one_report_per_network_then_advances_state(self):
        with tempfile.TemporaryDirectory() as directory:
            state_path = Path(directory) / "state.json"
            StateStore(state_path).write("1970-01-01T00:00:00-00:00")
            with patch("config_change_probe.NetLDClient", FakeClient):
                result = run(self.config(state_path))
            self.assertEqual(result["channels"][0]["value"], 2)
            self.assertEqual(
                [job["managedNetwork"] for job in FakeClient.instances[-1].started],
                ["East", "West"],
            )
            self.assertEqual(StateStore(state_path).read_or_initialize(), "1970-01-01T00:00:02-00:00")

    def test_run_does_not_advance_state_when_a_report_fails(self):
        class FailingClient(FakeClient):
            fail_after = 1

        with tempfile.TemporaryDirectory() as directory:
            state_path = Path(directory) / "state.json"
            initial = "1970-01-01T00:00:00-00:00"
            StateStore(state_path).write(initial)
            with patch("config_change_probe.NetLDClient", FailingClient):
                with self.assertRaisesRegex(ProbeError, "report failed"):
                    run(self.config(state_path))
            self.assertEqual(StateStore(state_path).read_or_initialize(), initial)


if __name__ == "__main__":
    unittest.main()
