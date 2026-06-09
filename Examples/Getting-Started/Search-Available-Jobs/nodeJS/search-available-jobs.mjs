import "dotenv/config";

import { NetLDClient, printAvailableJobs } from "./netld-example-client.mjs";

const client = NetLDClient.fromEnv();
await client.login();

const pageData = await client.searchAvailableJobs({
  networks: [process.env.NETLD_NETWORK || "Default"],
  offset: Number.parseInt(process.env.NETLD_JOB_OFFSET || "0", 10),
  pageSize: Number.parseInt(process.env.NETLD_JOB_PAGE_SIZE || "100", 10),
  sortColumn: process.env.NETLD_JOB_SORT_COLUMN || "",
  descending: (process.env.NETLD_JOB_DESCENDING || "false").toLowerCase() === "true",
});

printAvailableJobs(pageData);
