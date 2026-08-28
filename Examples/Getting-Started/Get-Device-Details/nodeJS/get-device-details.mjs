import fs from "node:fs";
import { fileURLToPath } from "node:url";

import { NetLDClient, printDeviceDetails } from "./netld-example-client.mjs";

const envFile = fileURLToPath(new URL(".env", import.meta.url));
if (fs.existsSync(envFile)) {
  for (const raw of fs.readFileSync(envFile, "utf8").split(/\r?\n/)) {
    const match = raw.match(/^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)\s*$/);
    if (!match || raw.trimStart().startsWith("#")) continue;
    let value = match[2];
    if ((value.startsWith('"') && value.endsWith('"')) ||
        (value.startsWith("'") && value.endsWith("'"))) value = value.slice(1, -1);
    process.env[match[1]] = value;
  }
}

const client = NetLDClient.fromEnv();
await client.login();

const device = await client.getDevice({
  network: process.env.NETLD_NETWORK || "Default",
  ipAddress: process.env.NETLD_DEVICE_IP || "10.95.1.40",
});

printDeviceDetails(device);
