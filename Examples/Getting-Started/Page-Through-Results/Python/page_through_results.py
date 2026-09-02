import json
import os
from typing import Protocol

from netld_example_client import NetLDClient, NetLDError


class ChangeLogPager(Protocol):
    def get_configuration_change_log_page(
        self, network: str, ip_address: str, offset: int, page_size: int
    ) -> dict: ...


def get_all_change_logs(
    client: ChangeLogPager, network: str, ip_address: str, page_size: int
) -> list[dict]:
    if page_size <= 0:
        raise NetLDError("NETLD_PAGE_SIZE must be a positive integer.")

    change_logs: list[dict] = []
    offset = 0
    total: int | None = None

    while total is None or offset < total:
        page = client.get_configuration_change_log_page(
            network, ip_address, offset, page_size
        )
        page_logs = page["changeLogs"]
        page_offset = int(page.get("offset", offset))
        reported_total = int(page.get("total", page_offset + len(page_logs)))
        total = reported_total if total is None else max(total, reported_total)
        change_logs.extend(page_logs)
        next_offset = page_offset + len(page_logs)

        print(
            f"Fetched {len(page_logs)} records at offset {page_offset} "
            f"({next_offset} of {total})"
        )

        if next_offset >= total:
            break
        if not page_logs or next_offset <= offset:
            raise NetLDError("Paging stopped before all results were returned.")
        offset = next_offset

    return change_logs


def main() -> None:
    client = NetLDClient.from_env()
    network = os.environ.get("NETLD_NETWORK", "Default")
    ip_address = os.environ.get("NETLD_DEVICE_IP", "").strip()
    if not ip_address:
        raise NetLDError("Set NETLD_DEVICE_IP in .env before running this example.")
    try:
        page_size = int(os.environ.get("NETLD_PAGE_SIZE", "10"))
    except ValueError as error:
        raise NetLDError("NETLD_PAGE_SIZE must be a positive integer.") from error

    client.login()
    change_logs = get_all_change_logs(client, network, ip_address, page_size)
    print(json.dumps({"total": len(change_logs), "changeLogs": change_logs}, indent=2))


if __name__ == "__main__":
    main()
