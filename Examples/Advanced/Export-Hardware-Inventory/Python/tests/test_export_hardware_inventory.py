import csv, json, sys, tempfile, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from export_hardware_inventory import Config, export_hardware


class FakeClient:
    def __init__(self):
        self.offsets = []

    def search_inventory(self, config, offset):
        self.offsets.append(offset)
        return {
            0: {
                "pageSize": 2,
                "total": 3,
                "devices": [
                    {
                        "network": "Default",
                        "ipAddress": "192.0.2.1",
                        "hostname": "one",
                        "adapterId": "Cisco::IOS",
                    },
                    {"network": "Lab", "ipAddress": "192.0.2.2", "hostname": "two"},
                ],
            },
            2: {
                "pageSize": 2,
                "total": 0,
                "devices": [
                    {"network": "Lab", "ipAddress": "192.0.2.3", "hostname": "three"}
                ],
            },
        }[offset]

    def get_device_hardware(self, device):
        if device["ipAddress"] == "192.0.2.2":
            raise RuntimeError("simulated lookup failure")
        if device["ipAddress"] == "192.0.2.3":
            return []
        return [
            {
                "hardwareId": 7,
                "assetType": "CHASSIS",
                "make": "Acme",
                "modelNumber": "R1",
                "latest": True,
                "cardParentId": -1,
            }
        ]


def config(base, fmt):
    return Config(
        "https://example",
        "key",
        ["Default", "Lab"],
        base / f"hardware.{fmt}",
        base / "failures.csv",
        fmt,
        2,
        "ipAddress",
        "",
    )


class Tests(unittest.TestCase):
    def test_csv_pagination_and_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            cfg = config(Path(directory), "csv")
            client = FakeClient()
            counts = export_hardware(client, cfg)
            with cfg.output_path.open() as stream:
                rows = list(csv.DictReader(stream))
            with cfg.failure_path.open() as stream:
                failures = list(csv.DictReader(stream))
        self.assertEqual(counts, (3, 1, 1))
        self.assertEqual(client.offsets, [0, 2])
        self.assertEqual(rows[0]["assetType"], "CHASSIS")
        self.assertEqual(rows[0]["latest"], "true")
        self.assertEqual(failures[0]["deviceIpAddress"], "192.0.2.2")

    def test_json_preserves_native_values(self):
        with tempfile.TemporaryDirectory() as directory:
            cfg = config(Path(directory), "json")
            export_hardware(FakeClient(), cfg)
            rows = json.loads(cfg.output_path.read_text())
        self.assertIs(rows[0]["latest"], True)
        self.assertEqual(rows[0]["hardwareId"], 7)


if __name__ == "__main__":
    unittest.main()
