import "dotenv/config";

import {
  NetLDClient,
  printConfigurationHistory,
} from "./netld-example-client.mjs";

const client = NetLDClient.fromEnv();
await client.login();

const pageData = await client.getConfigurationHistory({
  networks: [process.env.NETLD_NETWORK || "Default"],
  scheme: process.env.NETLD_HISTORY_SCHEME || "ipAddress",
  data: process.env.NETLD_HISTORY_DATA || "10.95.1.40",
  offset: Number.parseInt(process.env.NETLD_HISTORY_OFFSET || "0", 10),
  pageSize: Number.parseInt(process.env.NETLD_HISTORY_PAGE_SIZE || "100", 10),
  sortColumn: process.env.NETLD_HISTORY_SORT_COLUMN || "session",
  descending: (process.env.NETLD_HISTORY_DESCENDING || "true").toLowerCase() === "true",
});

printConfigurationHistory(pageData);
