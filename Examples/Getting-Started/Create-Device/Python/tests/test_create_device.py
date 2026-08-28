import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from create_device import create_parameters  # noqa: E402
from netld_example_client import NetLDError  # noqa: E402


class CreateDeviceTests(unittest.TestCase):
    def test_builds_named_parameters(self):
        self.assertEqual(
            create_parameters("Default", "2001:0db8::10", "Cisco::IOS"),
            {"network": "Default", "ipAddress": "2001:db8::10", "adapterId": "Cisco::IOS"},
        )

    def test_rejects_invalid_ip_address(self):
        with self.assertRaises(NetLDError):
            create_parameters("Default", "not-an-address", "Cisco::IOS")


if __name__ == "__main__":
    unittest.main()

