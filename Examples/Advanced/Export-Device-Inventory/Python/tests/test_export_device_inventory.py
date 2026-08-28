import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from export_device_inventory import ExampleError, export_inventory, parse_networks  # noqa: E402


class FakeClient:
    def __init__(self):
        self.offsets = []

    def search_inventory(self, networks, scheme, query, offset, page_size):
        self.offsets.append(offset)
        return {
            0: {"offset": 0, "pageSize": 2, "total": 5, "devices": [
                {"network": "Default", "ipAddress": "192.0.2.1", "hostname": "core,one"},
                {"network": "Lab", "ipAddress": "192.0.2.2", "memoSummary": "first\nsecond"},
            ]},
            2: {"offset": 2, "pageSize": 2, "total": 0, "devices": [
                {"network": "Lab", "ipAddress": "192.0.2.3"},
                {"network": "Lab", "ipAddress": "192.0.2.4"},
            ]},
            4: {"offset": 4, "pageSize": 2, "total": 0, "devices": [
                {"network": "Lab", "ipAddress": "192.0.2.5"},
            ]},
        }[offset]


class ExportInventoryTests(unittest.TestCase):
    def test_exports_every_page_with_header_and_csv_quoting(self):
        client = FakeClient()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "inventory.csv"
            count = export_inventory(client, ["Default", "Lab"], "ipAddress", "", 2, output)
            with output.open(newline="", encoding="utf-8") as stream:
                rows = list(csv.DictReader(stream))
        self.assertEqual(count, 5)
        self.assertEqual(client.offsets, [0, 2, 4])
        self.assertEqual([row["ipAddress"] for row in rows], [
            "192.0.2.1", "192.0.2.2", "192.0.2.3", "192.0.2.4", "192.0.2.5"
        ])
        self.assertEqual(rows[0]["hostname"], "core,one")
        self.assertEqual(rows[1]["memoSummary"], "first\nsecond")

    def test_rejects_empty_network_list(self):
        with self.assertRaises(ExampleError):
            parse_networks(" , ")

    def test_json_output_is_an_array_with_native_values(self):
        client = FakeClient()
        client.search_inventory = lambda networks, scheme, query, offset, page_size: {
            "pageSize": 1, "total": 1,
            "devices": [{"network": "Default", "ipAddress": "192.0.2.1", "complianceState": 2}],
        }
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "inventory.json"
            count = export_inventory(client, ["Default"], "ipAddress", "", 1, output, "json")
            devices = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(count, 1)
        self.assertIsInstance(devices, list)
        self.assertEqual(devices[0]["complianceState"], 2)
        self.assertIsNone(devices[0]["hostname"])
        self.assertEqual(set(devices[0]), set([
            "network", "ipAddress", "hostname", "adapterId", "deviceType",
            "hardwareVendor", "model", "serialNumber", "softwareVendor", "osVersion",
            "backupStatus", "complianceState", "lastBackup", "lastTelemetry", "memoSummary",
            "custom1", "custom2", "custom3", "custom4", "custom5",
        ]))


if __name__ == "__main__":
    unittest.main()
