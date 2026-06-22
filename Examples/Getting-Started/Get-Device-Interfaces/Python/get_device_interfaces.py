import os

from netld_example_client import NetLDClient, print_device_interfaces


client = NetLDClient.from_env()
client.login()

interfaces = client.get_device_interfaces(
    network=os.environ.get("NETLD_NETWORK", "Default"),
    ip_address=os.environ.get("NETLD_DEVICE_IP", "10.95.1.40"),
)

print_device_interfaces(interfaces)
