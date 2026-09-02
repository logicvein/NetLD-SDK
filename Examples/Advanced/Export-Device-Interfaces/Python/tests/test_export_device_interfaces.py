import csv
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from export_device_interfaces import Config, export_interfaces, flatten_ip_addresses  # noqa: E402


class FakeClient:
    def __init__(self):
        self.offsets = []

    def search_inventory(self, networks, scheme, query, offset, page_size):
        self.offsets.append(offset)
        return {
            0: {"pageSize": 2, "total": 3, "devices": [
                {"network": "Default", "ipAddress": "192.0.2.1", "hostname": "one"},
                {"network": "Lab", "ipAddress": "192.0.2.2", "hostname": "two"},
            ]},
            2: {"pageSize": 2, "total": 0, "devices": [
                {"network": "Lab", "ipAddress": "192.0.2.3", "hostname": "three"},
            ]},
        }[offset]

    def get_device_interfaces(self, network, ip_address):
        if ip_address == "192.0.2.2":
            raise RuntimeError("simulated lookup failure")
        if ip_address == "192.0.2.3":
            return []
        return [{
            "id": 7, "index": 1, "name": "Ethernet1", "adminUp": True,
            "ipAddresses": [{"ipAddress": "192.0.2.10", "cidrPrefix": 24},
                            {"ipAddress": "2001:db8::10", "cidrPrefix": 64}],
        }]


class InterfaceExportTests(unittest.TestCase):
    def test_multi_page_export_preserves_successes_and_records_failures(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            config = Config("https://example", "key", ["Default", "Lab"],
                            base / "interfaces.csv", base / "failures.csv", 2, "ipAddress", "")
            client = FakeClient()
            counts = export_interfaces(client, config)
            with config.output_path.open(encoding="utf-8", newline="") as stream:
                rows = list(csv.DictReader(stream))
            with config.failure_path.open(encoding="utf-8", newline="") as stream:
                failures = list(csv.DictReader(stream))
        self.assertEqual(counts, (3, 1, 1))
        self.assertEqual(client.offsets, [0, 2])
        self.assertEqual(rows[0]["ipAddresses"], "192.0.2.10/24;2001:db8::10/64")
        self.assertEqual(rows[0]["adminUp"], "true")
        self.assertEqual(failures[0]["deviceIpAddress"], "192.0.2.2")

    def test_flattens_empty_addresses(self):
        self.assertEqual(flatten_ip_addresses({"ipAddresses": []}), "")


if __name__ == "__main__":
    unittest.main()
