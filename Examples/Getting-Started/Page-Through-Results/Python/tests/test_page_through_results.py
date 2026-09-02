import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from page_through_results import NetLDError, get_all_change_logs  # noqa: E402


class FakeClient:
    def __init__(self, total: int = 61):
        self.total = total
        self.offsets: list[int] = []

    def get_configuration_change_log_page(
        self, network: str, ip_address: str, offset: int, page_size: int
    ) -> dict:
        self.offsets.append(offset)
        count = min(page_size, self.total - offset)
        return {
            "offset": offset,
            "pageSize": page_size,
            "total": self.total if offset == 0 else 0,
            "changeLogs": [{"index": value} for value in range(offset, offset + count)],
        }


class PagingTests(unittest.TestCase):
    def test_retrieves_all_pages_including_partial_final_page(self):
        client = FakeClient()

        results = get_all_change_logs(client, "Default", "192.0.2.10", 10)

        self.assertEqual(len(results), 61)
        self.assertEqual(client.offsets, [0, 10, 20, 30, 40, 50, 60])

    def test_rejects_non_positive_page_size(self):
        with self.assertRaises(NetLDError):
            get_all_change_logs(FakeClient(), "Default", "192.0.2.10", 0)


if __name__ == "__main__":
    unittest.main()
