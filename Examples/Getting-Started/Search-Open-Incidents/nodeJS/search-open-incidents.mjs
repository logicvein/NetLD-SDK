import "dotenv/config";

import { NetLDClient, printIncidents } from "./netld-example-client.mjs";

const client = NetLDClient.fromEnv();
await client.login();

const pageData = await client.searchOpenIncidents({
  network: process.env.NETLD_NETWORK || "Default",
  offset: Number.parseInt(process.env.NETLD_INCIDENT_OFFSET || "0", 10),
  pageSize: Number.parseInt(process.env.NETLD_INCIDENT_PAGE_SIZE || "100", 10),
  sortColumn: process.env.NETLD_INCIDENT_SORT_COLUMN || "modified",
  descending: (process.env.NETLD_INCIDENT_DESCENDING || "false").toLowerCase() === "true",
});

printIncidents(pageData);
