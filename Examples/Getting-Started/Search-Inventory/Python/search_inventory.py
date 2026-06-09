import os

from netld_example_client import NetLDClient, print_devices


client = NetLDClient.from_env()
client.login()

page_data = client.search_inventory(
    networks=[os.environ.get("NETLD_NETWORK", "Default")],
    schemes=os.environ.get("NETLD_SEARCH_SCHEME", "ipAddress"),
    queries=os.environ.get("NETLD_SEARCH_QUERY", "10.95.1.0/24"),
)

print_devices(page_data)
