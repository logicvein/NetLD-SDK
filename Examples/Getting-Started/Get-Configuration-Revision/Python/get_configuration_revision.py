import json
import os

from netld_example_client import NetLDClient, NetLDError, decode_revision_content


network = os.environ.get("NETLD_NETWORK", "Default")
device_ip = os.environ.get("NETLD_DEVICE_IP", "10.95.1.40")
config_path = os.environ.get("NETLD_CONFIG_PATH", "/running-config")

client = NetLDClient.from_env()
client.login()

page_data = client.get_configuration_history(
    networks=[network],
    scheme="ipAddress",
    data=device_ip,
)

matches = [
    item
    for item in (page_data or {}).get("configHistoryItems", [])
    if item.get("path") == config_path
]
if not matches:
    raise NetLDError(
        f'No configuration history item for "{config_path}" was found on {device_ip}@{network}.'
    )

history_item = matches[0]
revision = client.retrieve_revision(
    network=history_item["managedNetwork"],
    ip_address=history_item["ipAddress"],
    config_path=history_item["path"],
    timestamp=history_item["lastChanged"],
)
if revision is None:
    raise NetLDError("Configuration.retrieveRevision returned no revision.")

metadata = {key: value for key, value in revision.items() if key != "content"}
print("Revision metadata:")
print(json.dumps(metadata, indent=2))

decoded_content = decode_revision_content(revision)
if decoded_content is None:
    print("Revision content is empty or binary; Base64 content was not printed.")
else:
    print("Decoded revision content:")
    print(decoded_content)
