#!/usr/bin/env python3

import ipaddress
import json
import os
import sys
from pathlib import Path

from netld_example_client import NetLDClient, NetLDError, load_environment


def create_parameters(network, ip_address, adapter_id):
    try:
        normalized = str(ipaddress.ip_address(ip_address))
    except ValueError as exc:
        raise NetLDError(f"NETLD_DEVICE_IP is not a valid IPv4 or IPv6 address: {ip_address}") from exc
    if not network.strip():
        raise NetLDError("NETLD_NETWORK cannot be empty.")
    if not adapter_id.strip():
        raise NetLDError("NETLD_ADAPTER_ID cannot be empty.")
    return {"network": network.strip(), "ipAddress": normalized, "adapterId": adapter_id.strip()}


def main():
    load_environment(Path(__file__).with_name(".env"))
    parameters = create_parameters(
        os.getenv("NETLD_NETWORK", "Default"),
        os.getenv("NETLD_DEVICE_IP", "192.0.2.10"),
        os.getenv("NETLD_ADAPTER_ID", "Cisco::IOS"),
    )
    print(json.dumps(parameters, indent=2))
    if os.getenv("NETLD_CREATE_DEVICE", "false").lower() != "true":
        print("Dry run only. Set NETLD_CREATE_DEVICE=true after reviewing these parameters.")
        return 0

    client = NetLDClient.from_env()
    client.login()
    if client.get_device(parameters["network"], parameters["ipAddress"]) is not None:
        raise NetLDError("A device with this IP address already exists in the selected network.")
    error = client.create_device(
        parameters["network"], parameters["ipAddress"], parameters["adapterId"]
    )
    if error is not None:
        raise NetLDError(f"Inventory.createDevice returned: {error}")
    device = client.get_device(parameters["network"], parameters["ipAddress"])
    if not device:
        raise NetLDError("The create call succeeded, but Inventory.getDevice returned no device.")
    if device.get("ipAddress") != parameters["ipAddress"] or device.get("adapterId") != parameters["adapterId"]:
        raise NetLDError("The created device does not match the requested IP address and adapter ID.")
    print("Device created and verified:")
    print(json.dumps(device, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except NetLDError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
