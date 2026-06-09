import os

from netld_example_client import NetLDClient, print_configuration_history


client = NetLDClient.from_env()
client.login()

page_data = client.get_configuration_history(
    networks=[os.environ.get("NETLD_NETWORK", "Default")],
    scheme=os.environ.get("NETLD_HISTORY_SCHEME", "ipAddress"),
    data=os.environ.get("NETLD_HISTORY_DATA", "10.95.1.40"),
    offset=int(os.environ.get("NETLD_HISTORY_OFFSET", "0")),
    page_size=int(os.environ.get("NETLD_HISTORY_PAGE_SIZE", "100")),
    sort_column=os.environ.get("NETLD_HISTORY_SORT_COLUMN", "session"),
    descending=os.environ.get("NETLD_HISTORY_DESCENDING", "true").lower() == "true",
)

print_configuration_history(page_data)
