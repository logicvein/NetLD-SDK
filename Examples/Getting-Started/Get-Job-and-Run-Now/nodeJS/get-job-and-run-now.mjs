import "dotenv/config";

import { NetLDClient, NetLDError, printJson } from "./netld-example-client.mjs";

const jobName = process.env.NETLD_JOB_NAME;
if (!jobName) {
  throw new NetLDError("Set NETLD_JOB_NAME to the exact name of the job to run.");
}

const client = NetLDClient.fromEnv();
await client.login();

const pageData = await client.searchAvailableJobs({
  networks: [process.env.NETLD_NETWORK || "Default"],
  pageSize: Number.parseInt(process.env.NETLD_JOB_PAGE_SIZE || "100", 10),
});

const matches = (pageData?.jobData || []).filter((job) => job.jobName === jobName);

if (matches.length === 0) {
  throw new NetLDError(`No available job named "${jobName}" was found.`);
}
if (matches.length > 1) {
  throw new NetLDError(
    `Multiple jobs named "${jobName}" were found: ${matches.map((job) => job.jobId).join(", ")}`,
  );
}

const jobId = matches[0].jobId;
const jobData = await client.getJob(jobId);
if (!jobData) {
  throw new NetLDError(`Scheduler.getJob returned no data for job ID ${jobId}.`);
}

console.log(`Selected job "${jobName}" with ID ${jobId}:`);
printJson(jobData);

if ((process.env.NETLD_RUN_JOB || "false").toLowerCase() !== "true") {
  console.log("Dry run only. Set NETLD_RUN_JOB=true to execute this job.");
} else {
  const execution = await client.runNow(jobData);
  console.log("Execution started:");
  printJson(execution);
}
