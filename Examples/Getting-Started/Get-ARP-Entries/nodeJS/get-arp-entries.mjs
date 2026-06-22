import "dotenv/config";

import { NetLDClient, printArpEntries } from "./netld-example-client.mjs";

const client = NetLDClient.fromEnv();
await client.login();

const pageData = await client.getArpEntries({
  networkAddress: process.env.NETLD_ARP_NETWORK_ADDRESS || "10.95.1.0/24",
  networks: [process.env.NETLD_NETWORK || "Default"],
  offset: Number.parseInt(process.env.NETLD_ARP_OFFSET || "0", 10),
  pageSize: Number.parseInt(process.env.NETLD_ARP_PAGE_SIZE || "100", 10),
  sort: process.env.NETLD_ARP_SORT || "ipAddress",
  descending: (process.env.NETLD_ARP_DESCENDING || "true").toLowerCase() === "true",
});

printArpEntries(pageData);
