import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from archive_job_execution_outputs import (  # noqa: E402
    Config,
    archive_job_execution_outputs,
)


def execution(exec_id, end_time, job_type="Script Tool Job"):
    return {
        "id": exec_id,
        "endTime": end_time,
        "startTime": end_time - 100,
        "jobName": f"Job {exec_id}",
        "jobType": job_type,
    }


class FakeClient:
    def __init__(self, records, fail_detail=None):
        self.records = records
        self.fail_detail = fail_detail
        self.offsets = []

    def search_execution_page(self, offset, page_size):
        self.offsets.append(offset)
        batch = self.records[offset : offset + page_size]
        return {
            "offset": offset,
            "pageSize": page_size,
            "total": len(self.records) if offset == 0 else 0,
            "executionData": batch,
        }

    def execution_details(self, execution_id):
        return [{"id": execution_id * 10, "managedNetwork": "Default", "ipAddress": "192.0.2.10"}]

    def download_detail(self, execution_id, detail_id):
        if detail_id == self.fail_detail:
            raise RuntimeError("download failed")
        return f"output {execution_id}".encode()


class ArchiveTests(unittest.TestCase):
    def config(self, base, initial_mode="all"):
        return Config(
            "https://example.test",
            "token",
            base / "outputs",
            base / "state.json",
            base / "report.json",
            2,
            initial_mode,
            "",
            "",
            "Script Tool Job",
            "",
        )

    def test_all_mode_pages_and_archives_only_script_tool_jobs(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            client = FakeClient(
                [execution(3, 3000), execution(2, 2000, "Report Job"), execution(1, 1000)]
            )

            report = archive_job_execution_outputs(client, self.config(base), "2026-09-02T00:00:00Z")

            self.assertEqual(client.offsets, [0, 2])
            self.assertEqual(report["archivedCount"], 2)
            self.assertEqual(report["outputCount"], 2)
            self.assertEqual((base / "state.json").read_text().count('"lastEndTime": 3000'), 1)

    def test_latest_mode_baselines_then_archives_a_new_execution(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            config = self.config(base, "latest")
            first = archive_job_execution_outputs(
                FakeClient([execution(2, 2000), execution(1, 1000)]), config
            )
            second = archive_job_execution_outputs(
                FakeClient([execution(3, 3000), execution(2, 2000), execution(1, 1000)]), config
            )

            self.assertTrue(first["initialBaseline"])
            self.assertEqual(first["archivedCount"], 0)
            self.assertEqual(second["archivedCount"], 1)

    def test_failure_does_not_advance_state(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            config = self.config(base, "latest")
            archive_job_execution_outputs(FakeClient([execution(1, 1000)]), config)
            report = archive_job_execution_outputs(
                FakeClient([execution(2, 2000), execution(1, 1000)], fail_detail=20), config
            )

            self.assertEqual(report["failureCount"], 1)
            self.assertIn('"lastEndTime": 1000', (base / "state.json").read_text())


if __name__ == "__main__":
    unittest.main()
