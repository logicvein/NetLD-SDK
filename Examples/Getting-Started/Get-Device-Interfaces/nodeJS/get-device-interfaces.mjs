import "dotenv/config";

import { NetLDClient, printDeviceInterfaces } from "./netld-example-client.mjs";

const client = NetLDClient.fromEnv();
await client.login();

const interfaces = await client.getDeviceInterfaces({
  network: process.env.NETLD_NETWORK || "Default",
  ipAddress: process.env.NETLD_DEVICE_IP || "10.95.1.40",
});

printDeviceInterfaces(interfaces);
