import pathlib
import sys
import unittest


sys.path.insert(0, str(pathlib.Path(__file__).parents[1]))
import live_nx_to_thirdeye as bridge


class ParseLiveNXDeviceIPsTests(unittest.TestCase):
    def test_parses_valid_vendor_devices_and_normalizes_addresses(self):
        content = (
            "\ufeffIP ADDRESS,VENDOR,NAME\n"
            "192.0.2.10,Cisco,router-1\n"
            "2001:0db8::1,Juniper,router-2\n"
            "not-an-address,Cisco,bad-row\n"
            "192.0.2.20,,vendorless\n"
        )

        result = bridge.parse_live_nx_device_ips(content)

        self.assertEqual(result, {"192.0.2.10", "2001:db8::1"})

    def test_can_include_vendorless_devices(self):
        content = "Management IP,Name\n192.0.2.20,router-1\n"

        result = bridge.parse_live_nx_device_ips(content, require_vendor=False)

        self.assertEqual(result, {"192.0.2.20"})

    def test_rejects_unknown_csv_shape(self):
        with self.assertRaises(bridge.BridgeError):
            bridge.parse_live_nx_device_ips("HOSTNAME,VENDOR\nrouter-1,Cisco\n")


class PrepareDiscoveryJobTests(unittest.TestCase):
    def test_updates_a_copy_of_a_compatible_job(self):
        source = {
            "managedNetwork": "Old",
            "jobParameters": {
                "managedNetwork": "Old",
                "includedAddresses": "192.0.2.1",
            },
        }

        prepared = bridge.prepare_discovery_job(
            source,
            "Default",
            {"2001:db8::1", "192.0.2.20"},
        )

        self.assertEqual(source["managedNetwork"], "Old")
        self.assertEqual(prepared["managedNetwork"], "Default")
        self.assertEqual(prepared["jobParameters"]["managedNetwork"], "Default")
        self.assertEqual(
            prepared["jobParameters"]["includedAddresses"],
            "192.0.2.20,2001:db8::1",
        )

    def test_rejects_a_non_discovery_job(self):
        with self.assertRaises(bridge.BridgeError):
            bridge.prepare_discovery_job(
                {"jobParameters": {}},
                "Default",
                {"192.0.2.1"},
            )


class LiveNXClientTests(unittest.TestCase):
    def test_sends_token_in_header_and_verifies_tls(self):
        class Response:
            is_redirect = False
            encoding = None
            text = "IP ADDRESS,VENDOR\n192.0.2.10,Cisco\n"

            @staticmethod
            def raise_for_status():
                return None

        class Session:
            def get(self, url, **kwargs):
                self.url = url
                self.kwargs = kwargs
                return Response()

        client = bridge.LiveNXClient(
            "https://livenx.example.com:8093",
            "secret-token",
            "/v1/devices/export/csv",
        )
        client.session = Session()

        client.export_devices_csv()

        self.assertNotIn("secret-token", client.session.url)
        self.assertEqual(
            client.session.kwargs["headers"]["Authorization"],
            "Bearer secret-token",
        )
        self.assertTrue(client.session.kwargs["verify"])
        self.assertFalse(client.session.kwargs["allow_redirects"])


class NetLDClientTests(unittest.TestCase):
    def test_inventory_addresses_reads_every_page(self):
        class Client(bridge.NetLDClient):
            def __init__(self):
                self.offsets = []

            def call(self, method, **params):
                self.offsets.append(params["pageData"]["offset"])
                if len(self.offsets) == 1:
                    return {
                        "devices": [
                            {"ipAddress": "192.0.2.10"},
                            {"ipAddress": "not-an-address"},
                        ],
                        "total": 3,
                    }
                return {
                    "devices": [{"ipAddress": "2001:0db8::1"}],
                    "total": 3,
                }

        client = Client()

        result = client.inventory_addresses("Default")

        self.assertEqual(result, {"192.0.2.10", "2001:db8::1"})
        self.assertEqual(client.offsets, [0, 2])


if __name__ == "__main__":
    unittest.main()
