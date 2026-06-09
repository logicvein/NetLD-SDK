import "dotenv/config";

import { NetLDClient, printDevices } from "./netld-example-client.mjs";

const client = NetLDClient.fromEnv();
await client.login();

const pageData = await client.searchInventory({
  networks: [process.env.NETLD_NETWORK || "Default"],
  schemes: process.env.NETLD_SEARCH_SCHEME || "ipAddress",
  queries: process.env.NETLD_SEARCH_QUERY || "10.95.1.0/24",
});

printDevices(pageData);
