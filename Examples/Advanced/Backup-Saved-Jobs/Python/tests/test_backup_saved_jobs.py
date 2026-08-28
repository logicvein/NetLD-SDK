import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backup_saved_jobs import Config, backup_saved_jobs  # noqa: E402


class FakeClient:
    def __init__(self):
        self.offsets = []
        self.requested_ids = []

    def search_jobs(self, networks, offset, page_size):
        self.offsets.append(offset)
        return {
            0: {"pageSize": 2, "total": 3, "jobData": [
                {"jobId": 3, "jobName": "Three"}, {"jobId": 1, "jobName": "One"},
            ]},
            2: {"pageSize": 2, "total": 0, "jobData": [
                {"jobId": 2, "jobName": "Two"},
            ]},
        }[offset]

    def get_job(self, job_id):
        self.requested_ids.append(job_id)
        if job_id == 2:
            raise RuntimeError("simulated retrieval failure")
        return {"jobId": job_id, "jobName": str(job_id), "jobParameters": {"z": "last", "a": "first"}}


class SavedJobBackupTests(unittest.TestCase):
    def test_multi_page_backup_is_sorted_versioned_and_failure_aware(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            config = Config("https://example", "key", ["Lab", "Default"],
                            base / "jobs.json", base / "failures.json", 2)
            client = FakeClient()
            counts = backup_saved_jobs(client, config, "2026-08-28T12:00:00Z")
            backup = json.loads(config.output_path.read_text(encoding="utf-8"))
            failures = json.loads(config.failure_path.read_text(encoding="utf-8"))
        self.assertEqual(counts, (2, 1))
        self.assertEqual(client.offsets, [0, 2])
        self.assertEqual([job["jobId"] for job in backup["jobs"]], [1, 3])
        self.assertEqual(backup["networks"], ["Default", "Lab"])
        self.assertFalse(backup["complete"])
        self.assertEqual(failures["failures"][0]["jobId"], 2)

    def test_duplicate_job_id_is_retrieved_once(self):
        client = FakeClient()
        client.search_jobs = lambda networks, offset, page_size: {
            "pageSize": 2, "total": 2,
            "jobData": [{"jobId": 1, "jobName": "One"}, {"jobId": 1, "jobName": "One"}],
        }
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            config = Config("https://example", "key", ["Default"], base / "jobs.json", base / "failures.json", 2)
            backup_saved_jobs(client, config, "2026-08-28T12:00:00Z")
        self.assertEqual(client.requested_ids, [1])


if __name__ == "__main__":
    unittest.main()
