#!/usr/bin/env node

import { config as loadDotEnv } from "dotenv";
import { isIP } from "node:net";
import process from "node:process";
import { fileURLToPath, pathToFileURL } from "node:url";

import { NetLDClient, NetLDError } from "./netld-example-client.mjs";

loadDotEnv({ path: fileURLToPath(new URL(".env", import.meta.url)), override: true, quiet: true });

export function createParameters(network, ipAddress, adapterId) {
  const address = ipAddress.trim();
  const family = isIP(address);
  if (!family) throw new NetLDError(`NETLD_DEVICE_IP is not a valid IPv4 or IPv6 address: ${ipAddress}`);
  if (!network.trim()) throw new NetLDError("NETLD_NETWORK cannot be empty.");
  if (!adapterId.trim()) throw new NetLDError("NETLD_ADAPTER_ID cannot be empty.");
  const normalizedAddress =
    family === 6 ? new URL(`http://[${address}]`).hostname.slice(1, -1) : address;
  return { network: network.trim(), ipAddress: normalizedAddress, adapterId: adapterId.trim() };
}

export async function main() {
  const parameters = createParameters(
    process.env.NETLD_NETWORK || "Default",
    process.env.NETLD_DEVICE_IP || "192.0.2.10",
    process.env.NETLD_ADAPTER_ID || "Cisco::IOS",
  );
  console.log(JSON.stringify(parameters, null, 2));
  if (process.env.NETLD_CREATE_DEVICE?.toLowerCase() !== "true") {
    console.log("Dry run only. Set NETLD_CREATE_DEVICE=true after reviewing these parameters.");
    return;
  }
  if (!process.env.NETLD_BASE_URL) throw new NetLDError("Set NETLD_BASE_URL in .env before running this example.");
  if (!process.env.NETLD_API_KEY) throw new NetLDError("Set NETLD_API_KEY in .env before running this example.");
  const client = new NetLDClient(process.env.NETLD_BASE_URL, process.env.NETLD_API_KEY);
  await client.login();
  if (await client.getDevice(parameters)) {
    throw new NetLDError("A device with this IP address already exists in the selected network.");
  }
  const error = await client.createDevice(parameters);
  if (error != null) throw new NetLDError(`Inventory.createDevice returned: ${error}`);
  const device = await client.getDevice(parameters);
  if (!device) throw new NetLDError("The create call succeeded, but Inventory.getDevice returned no device.");
  if (device.ipAddress !== parameters.ipAddress || device.adapterId !== parameters.adapterId) {
    throw new NetLDError("The created device does not match the requested IP address and adapter ID.");
  }
  console.log("Device created and verified:");
  console.log(JSON.stringify(device, null, 2));
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error) => {
    console.error(`Error: ${error.message}`);
    process.exitCode = 1;
  });
}
