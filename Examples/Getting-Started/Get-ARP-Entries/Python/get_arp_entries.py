import os

from netld_example_client import NetLDClient, print_arp_entries


client = NetLDClient.from_env()
client.login()

page_data = client.get_arp_entries(
    network_address=os.environ.get("NETLD_ARP_NETWORK_ADDRESS", "10.95.1.0/24"),
    networks=[os.environ.get("NETLD_NETWORK", "Default")],
    offset=int(os.environ.get("NETLD_ARP_OFFSET", "0")),
    page_size=int(os.environ.get("NETLD_ARP_PAGE_SIZE", "100")),
    sort=os.environ.get("NETLD_ARP_SORT", "ipAddress"),
    descending=os.environ.get("NETLD_ARP_DESCENDING", "true").lower() == "true",
)

print_arp_entries(page_data)
