import os

from netld_example_client import NetLDClient, print_incidents


client = NetLDClient.from_env()
client.login()

page_data = client.search_open_incidents(
    network=os.environ.get("NETLD_NETWORK", "Default"),
    offset=int(os.environ.get("NETLD_INCIDENT_OFFSET", "0")),
    page_size=int(os.environ.get("NETLD_INCIDENT_PAGE_SIZE", "100")),
    sort_column=os.environ.get("NETLD_INCIDENT_SORT_COLUMN", "modified"),
    descending=os.environ.get("NETLD_INCIDENT_DESCENDING", "false").lower() == "true",
)

print_incidents(page_data)
