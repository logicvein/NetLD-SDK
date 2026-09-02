#!/usr/bin/env node

import { randomUUID } from "node:crypto";
import { mkdir, readFile, rename, rm, writeFile } from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { fileURLToPath, pathToFileURL } from "node:url";

export const FORMAT_NAME = "logicvein-netld-saved-job-backup";
export const FAILURE_FORMAT_NAME = "logicvein-netld-saved-job-backup-failures";
export const FORMAT_VERSION = 1;

export class ExampleError extends Error {}

export function parseNetworks(value) {
  const networks = [...new Set(value.split(",").map((item) => item.trim()).filter(Boolean))].sort();
  if (!networks.length) throw new ExampleError("NETLD_NETWORKS must contain at least one managed network.");
  return networks;
}

async function loadDotEnv(file) {
  let text;
  try { text = await readFile(file, "utf8"); }
  catch (error) { if (error.code === "ENOENT") return; throw error; }
  for (const raw of text.split(/\r?\n/)) {
    const line = raw.trim();
    if (!line || line.startsWith("#") || !line.includes("=")) continue;
    const offset = line.indexOf("=");
    process.env[line.slice(0, offset).trim()] = line.slice(offset + 1).trim().replace(/^(['"])(.*)\1$/, "$2");
  }
}

async function loadConfig(directory, envFile) {
  await loadDotEnv(envFile);
  for (const name of ["NETLD_BASE_URL", "NETLD_API_KEY"]) {
    if (!process.env[name]?.trim()) throw new ExampleError(`Set ${name} in the environment file.`);
  }
  const pageSize = Number.parseInt(process.env.NETLD_JOB_PAGE_SIZE || "100", 10);
  if (!Number.isInteger(pageSize) || pageSize <= 0) throw new ExampleError("NETLD_JOB_PAGE_SIZE must be a positive integer.");
  return {
    baseUrl: process.env.NETLD_BASE_URL.replace(/\/$/, ""), apiKey: process.env.NETLD_API_KEY,
    networks: parseNetworks(process.env.NETLD_NETWORKS || "Default"), pageSize,
    outputFile: path.resolve(directory, process.env.NETLD_OUTPUT_FILE || "saved-jobs.json"),
    failureFile: path.resolve(directory, process.env.NETLD_FAILURE_FILE || "saved-job-failures.json"),
  };
}

class NetLDClient {
  constructor(baseUrl, apiKey, timeout = 30000) {
    this.baseUrl = baseUrl; this.apiKey = apiKey; this.timeout = timeout; this.cookies = "";
  }
  headers(extra = {}) {
    return { Authorization: `Bearer ${this.apiKey}`, ...(this.cookies ? { Cookie: this.cookies } : {}), ...extra };
  }
  async request(options = {}) {
    let response;
    try {
      response = await fetch(`${this.baseUrl}/rest`, {
        redirect: "manual", signal: AbortSignal.timeout(this.timeout), ...options,
        headers: this.headers(options.headers),
      });
    } catch { throw new ExampleError(`Could not reach ${this.baseUrl}.`); }
    if (response.status >= 300 && response.status < 400) {
      throw new ExampleError(`Request redirected to ${response.headers.get("location") || ""}.`);
    }
    if (!response.ok) throw new ExampleError(`Request failed with HTTP ${response.status}.`);
    const setCookies = response.headers.getSetCookie?.() || splitSetCookie(response.headers.get("set-cookie") || "");
    if (setCookies.length) this.cookies = setCookies.map((item) => item.split(";", 1)[0]).join("; ");
    return response;
  }
  async login() { await this.request(); }
  async call(method, parameters = {}) {
    const response = await this.request({
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ jsonrpc: "2.0", method, params: parameters, id: randomUUID() }),
    });
    const data = await response.json();
    if (data.error) throw new ExampleError(`${method} failed: ${JSON.stringify(data.error)}`);
    return data.result;
  }
  async searchJobs(networks, offset, pageSize) {
    const result = await this.call("Scheduler.searchJobs", {
      pageData: { offset, jobData: [], pageSize, total: 1 },
      networks, sortColumn: "", descending: false,
    });
    if (!result || typeof result !== "object") throw new ExampleError("Scheduler.searchJobs returned no page data.");
    return result;
  }
  async getJob(jobId) {
    const result = await this.call("Scheduler.getJob", { jobId });
    if (!result || typeof result !== "object") throw new ExampleError(`Scheduler.getJob returned no data for job ID ${jobId}.`);
    return result;
  }
}

function splitSetCookie(header) { return header ? header.split(/,(?=\s*[^;=]+=[^;]+)/) : []; }

export async function collectJobs(client, config) {
  const jobs = new Map();
  const failures = new Map();
  let offset = 0;
  let total;
  while (true) {
    const page = await client.searchJobs(config.networks, offset, config.pageSize);
    const shallowJobs = page.jobData || [];
    if (!Array.isArray(shallowJobs)) throw new ExampleError("Scheduler.searchJobs returned an invalid jobData collection.");
    for (const shallow of shallowJobs) {
      const jobId = shallow.jobId;
      if (!Number.isInteger(jobId)) throw new ExampleError("Scheduler.searchJobs returned a job without an integer jobId.");
      if (jobs.has(jobId) || failures.has(jobId)) continue;
      try { jobs.set(jobId, await client.getJob(jobId)); }
      catch (error) { failures.set(jobId, { jobId, jobName: shallow.jobName, error: error.message }); }
    }
    const returnedPageSize = Number(page.pageSize || config.pageSize);
    if (!Number.isInteger(returnedPageSize) || returnedPageSize <= 0) throw new ExampleError("Scheduler.searchJobs returned an invalid page size.");
    if (total == null && page.total != null) total = Number(page.total);
    if (total != null && offset + shallowJobs.length >= total) break;
    if (total == null && shallowJobs.length < returnedPageSize) break;
    if (!shallowJobs.length) throw new ExampleError("Scheduler.searchJobs returned an empty page before the reported total.");
    offset += returnedPageSize;
  }
  return {
    jobs: [...jobs.entries()].sort(([a], [b]) => a - b).map(([, job]) => job),
    failures: [...failures.entries()].sort(([a], [b]) => a - b).map(([, failure]) => failure),
  };
}

export function buildDocuments(jobs, failures, networks, exportedAt = new Date().toISOString().replace(/\.\d{3}Z$/, "Z")) {
  return {
    backup: {
      format: FORMAT_NAME, formatVersion: FORMAT_VERSION, exportedAt,
      networks: [...networks].sort(), complete: failures.length === 0,
      jobCount: jobs.length, jobs,
    },
    failureReport: {
      format: FAILURE_FORMAT_NAME, formatVersion: FORMAT_VERSION, exportedAt,
      failureCount: failures.length, failures,
    },
  };
}

function canonicalize(value) {
  if (Array.isArray(value)) return value.map(canonicalize);
  if (value && typeof value === "object") {
    return Object.fromEntries(Object.keys(value).sort().map((key) => [key, canonicalize(value[key])]));
  }
  return value;
}

async function writeJsonAtomic(destination, document) {
  await mkdir(path.dirname(destination), { recursive: true });
  const temporary = path.join(path.dirname(destination), `.${path.basename(destination)}.${randomUUID()}.tmp`);
  try {
    await writeFile(temporary, `${JSON.stringify(canonicalize(document), null, 2)}\n`, {
      encoding: "utf8", flag: "wx", mode: 0o600,
    });
    await rename(temporary, destination);
  } catch (error) {
    await rm(temporary, { force: true }).catch(() => {});
    throw error;
  }
}

export async function backupSavedJobs(client, config, exportedAt) {
  const { jobs, failures } = await collectJobs(client, config);
  const { backup, failureReport } = buildDocuments(jobs, failures, config.networks, exportedAt);
  await writeJsonAtomic(config.outputFile, backup);
  await writeJsonAtomic(config.failureFile, failureReport);
  return { jobCount: jobs.length, failureCount: failures.length };
}

export async function main() {
  const directory = path.dirname(fileURLToPath(import.meta.url));
  const envOffset = process.argv.indexOf("--env");
  if (envOffset >= 0 && !process.argv[envOffset + 1]) throw new ExampleError("--env requires a file path.");
  const envFile = envOffset >= 0 ? path.resolve(process.argv[envOffset + 1]) : path.join(directory, ".env");
  const config = await loadConfig(directory, envFile);
  const client = new NetLDClient(config.baseUrl, config.apiKey);
  await client.login();
  const result = await backupSavedJobs(client, config);
  console.log(`Wrote ${result.jobCount} complete saved jobs to ${config.outputFile}`);
  console.log(`Wrote ${result.failureCount} retrieval failures to ${config.failureFile}`);
  return result.failureCount ? 2 : 0;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().then((code) => { process.exitCode = code; }).catch((error) => {
    console.error(`Error: ${error.message}`); process.exitCode = 1;
  });
}
