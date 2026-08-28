import base64
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from archive_configuration_revisions import Config, archive_configuration_revisions  # noqa: E402


class FakeClient:
    def __init__(self, fail_path=None):
        self.fail_path = fail_path

    def search_inventory(self, config, offset):
        return {"pageSize": 10, "total": 1, "devices": [
            {"network": "Default", "ipAddress": "192.0.2.1", "hostname": "router"},
        ]}

    def configuration_history(self, device, offset, page_size):
        items = [
            self.item("/running-config", 300), self.item("/startup-config", 200),
            self.item("/running-config", 100),
        ]
        return {"pageSize": 10, "total": 3, "configHistoryItems": items}

    @staticmethod
    def item(path, timestamp):
        return {"managedNetwork": "Default", "ipAddress": "192.0.2.1", "path": path,
                "lastChanged": timestamp, "mimeType": "text/plain", "size": 4}

    def retrieve_revision(self, item):
        if item["path"] == self.fail_path:
            raise RuntimeError("simulated revision failure")
        return {"path": item["path"], "lastChanged": item["lastChanged"],
                "mimeType": "text/plain", "size": 4,
                "content": base64.b64encode(b"test").decode("ascii")}


def config(base, mode="latest"):
    return Config("https://example", "key", ["Default"], base / "archive",
                  base / "state.json", base / "run.json", 10, 10,
                  "ipAddress", "", mode)


class ArchiveTests(unittest.TestCase):
    def test_latest_baseline_then_incremental_noop(self):
        with tempfile.TemporaryDirectory() as directory:
            cfg = config(Path(directory))
            first = archive_configuration_revisions(FakeClient(), cfg, "2026-08-28T12:00:00Z")
            second = archive_configuration_revisions(FakeClient(), cfg, "2026-08-28T12:01:00Z")
            state = json.loads(cfg.state_path.read_text(encoding="utf-8"))
            content_file_count = len(list(cfg.archive_dir.glob("**/*.txt")))
        self.assertEqual(first["archivedCount"], 2)
        self.assertEqual(second["archivedCount"], 0)
        self.assertEqual(state["devices"]["Default@192.0.2.1"]["lastChanged"], 300)
        self.assertEqual(content_file_count, 2)

    def test_failure_does_not_advance_device_state(self):
        with tempfile.TemporaryDirectory() as directory:
            cfg = config(Path(directory))
            report = archive_configuration_revisions(FakeClient("/startup-config"), cfg)
            state = json.loads(cfg.state_path.read_text(encoding="utf-8"))
        self.assertEqual(report["failureCount"], 1)
        self.assertNotIn("Default@192.0.2.1", state["devices"])

    def test_all_mode_archives_every_revision(self):
        with tempfile.TemporaryDirectory() as directory:
            cfg = config(Path(directory), "all")
            report = archive_configuration_revisions(FakeClient(), cfg)
        self.assertEqual(report["archivedCount"], 3)


if __name__ == "__main__":
    unittest.main()
