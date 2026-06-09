import "dotenv/config";

import { NetLDClient, printDeviceHardware } from "./netld-example-client.mjs";

const client = NetLDClient.fromEnv();
await client.login();

const hardware = await client.getDeviceHardware({
  ipAddress: process.env.NETLD_DEVICE_IP || "10.95.1.40",
  network: process.env.NETLD_NETWORK || "Default",
});

printDeviceHardware(hardware);
