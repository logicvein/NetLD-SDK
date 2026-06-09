import "dotenv/config";

import { NetLDClient, printDeviceDetails } from "./netld-example-client.mjs";

const client = NetLDClient.fromEnv();
await client.login();

const device = await client.getDevice({
  network: process.env.NETLD_NETWORK || "Default",
  ipAddress: process.env.NETLD_DEVICE_IP || "10.95.1.40",
});

printDeviceDetails(device);
