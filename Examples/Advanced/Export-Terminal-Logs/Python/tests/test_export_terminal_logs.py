import json, sys, tempfile, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from export_terminal_logs import Config, export_terminal_logs


def record(log_id, start, end):
    return {
        "logId": log_id,
        "sessionStart": start,
        "sessionEnd": end,
        "ipAddress": "192.0.2.1",
        "hostname": "router",
        "managedNetwork": "Default",
        "username": "operator",
    }


class FakeClient:
    def __init__(self, fail_id=None):
        self.fail_id = fail_id
        self.searches = []

    def search(self, scheme, query):
        self.searches.append((scheme, query))
        return [record(1, 1000, 2000), record(2, 3000, 4000)]

    def retrieve(self, value):
        if value["logId"] == self.fail_id:
            raise RuntimeError("simulated download failure")
        return f"log {value['logId']}".encode()


def config(base):
    return Config(
        "https://example",
        "key",
        base / "logs",
        base / "state.json",
        base / "run.json",
        "30d",
        ["Default"],
        "",
        True,
    )


class Tests(unittest.TestCase):
    def test_initial_export_then_incremental_noop(self):
        with tempfile.TemporaryDirectory() as directory:
            cfg = config(Path(directory))
            client = FakeClient()
            first = export_terminal_logs(client, cfg, "2026-08-31T12:00:00Z")
            second = export_terminal_logs(client, cfg, "2026-08-31T12:01:00Z")
            state = json.loads(cfg.state_path.read_text())
            files = list(cfg.output_dir.glob("**/*.log"))
        self.assertEqual(first["archivedCount"], 2)
        self.assertEqual(second["archivedCount"], 0)
        self.assertEqual(state["lastSessionEnd"], 4000)
        self.assertEqual(len(files), 2)
        self.assertEqual(client.searches[0], ("session,network", "30d\nDefault"))
        self.assertTrue(client.searches[1][0].startswith("since"))

    def test_failure_does_not_advance_state(self):
        with tempfile.TemporaryDirectory() as directory:
            cfg = config(Path(directory))
            report = export_terminal_logs(FakeClient(2), cfg)
            state = json.loads(cfg.state_path.read_text())
        self.assertEqual(report["failureCount"], 1)
        self.assertNotIn("lastSessionEnd", state)


if __name__ == "__main__":
    unittest.main()
