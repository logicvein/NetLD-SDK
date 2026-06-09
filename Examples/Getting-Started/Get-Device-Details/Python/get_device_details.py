import os

from netld_example_client import NetLDClient, print_device_details


client = NetLDClient.from_env()
client.login()

device = client.get_device(
    network=os.environ.get("NETLD_NETWORK", "Default"),
    ip_address=os.environ.get("NETLD_DEVICE_IP", "10.95.1.40"),
)

print_device_details(device)
