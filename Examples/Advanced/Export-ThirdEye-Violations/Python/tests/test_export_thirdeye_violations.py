import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from export_thirdeye_violations import (
    Config,
    ExampleError,
    export_violations,
    parse_queries,
)


def event(event_id, updated, severity="ERROR"):
    return {
        "eventId": event_id,
        "incidentId": 1,
        "severity": severity,
        "clearState": "ACTIVE",
        "eventType": "THRESHOLD",
        "network": "Default",
        "ipAddress": "192.0.2.1",
        "hostname": "router",
        "deviceId": 7,
        "hostUuid": "host-7",
        "measurement": "CPU",
        "measurementIndex": None,
        "message": "Test, with comma",
        "occurrences": 1,
        "triggerId": "trigger-1",
        "created": updated - 1000,
        "updated": updated,
    }


class FakeClient:
    def __init__(self, pages):
        self.pages = pages
        self.calls = []

    def search_page(self, queries, offset, page_size):
        self.calls.append((queries, offset, page_size))
        return self.pages[offset]


def config(base, output_format="csv"):
    return Config(
        "https://example",
        "key",
        base / "output",
        output_format,
        base / "state.json",
        base / "run.json",
        2,
        24,
        ["incidentId=1"],
    )


class Tests(unittest.TestCase):
    def test_pages_csv_and_incremental_tie_breaker(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            cfg = config(base)
            pages = {
                0: {
                    "offset": 0,
                    "pageSize": 2,
                    "total": 3,
                    "violations": [event(3, 3000), event(2, 2000)],
                },
                2: {
                    "offset": 2,
                    "pageSize": 2,
                    "total": 0,
                    "violations": [event(1, 2000)],
                },
            }
            first = export_violations(
                FakeClient(pages), cfg, 4_000, "1970-01-01T00:00:04Z"
            )
            with Path(first["outputFile"]).open(newline="", encoding="utf-8") as stream:
                rows = list(csv.DictReader(stream))
            state = json.loads(cfg.state_path.read_text())
            second_pages = {
                0: {
                    "offset": 0,
                    "pageSize": 2,
                    "total": 2,
                    "violations": [event(4, 3000), event(3, 3000)],
                }
            }
            second = export_violations(
                FakeClient(second_pages), cfg, 5_000, "1970-01-01T00:00:05Z"
            )
        self.assertEqual(first["pageCount"], 2)
        self.assertEqual(first["exportedCount"], 3)
        self.assertEqual([row["eventId"] for row in rows], ["1", "2", "3"])
        self.assertEqual(rows[0]["message"], "Test, with comma")
        self.assertEqual(state["lastUpdated"], 3000)
        self.assertEqual(second["exportedCount"], 1)

    def test_json_preserves_api_values(self):
        with tempfile.TemporaryDirectory() as directory:
            cfg = config(Path(directory), "json")
            pages = {
                0: {
                    "offset": 0,
                    "pageSize": 2,
                    "total": 1,
                    "violations": [event(1, 2000)],
                }
            }
            report = export_violations(FakeClient(pages), cfg, 3_000)
            result = json.loads(Path(report["outputFile"]).read_text())
        self.assertEqual(result[0]["updated"], 2000)
        self.assertIsNone(result[0]["measurementIndex"])

    def test_query_validation(self):
        self.assertEqual(parse_queries('["incidentId=1"]'), ["incidentId=1"])
        with self.assertRaises(ExampleError):
            parse_queries('["start=2026-01-01T00:00:00Z"]')


if __name__ == "__main__":
    unittest.main()
