import os

from netld_example_client import NetLDClient, print_device_hardware


client = NetLDClient.from_env()
client.login()

hardware = client.get_device_hardware(
    ip_address=os.environ.get("NETLD_DEVICE_IP", "10.95.1.40"),
    network=os.environ.get("NETLD_NETWORK", "Default"),
)

print_device_hardware(hardware)
