#!/usr/bin/env node

import { randomUUID } from "node:crypto";
import { readFile, mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { fileURLToPath, pathToFileURL } from "node:url";

export class ExampleError extends Error {}

export function safeFilename(value) {
  return value.trim().replace(/[^A-Za-z0-9._-]+/g, "_").replace(/^[._]+|[._]+$/g, "") || "device";
}

export function buildJob(network, target, commands, backup = false) {
  if (!commands.length) throw new ExampleError("The command file contains no commands.");
  return {
    jobName: `API Commands - ${target}`,
    managedNetworks: [network],
    jobType: "Script Tool Job",
    description: "Ad hoc command execution from the NetLD SDK advanced example",
    jobParameters: {
      tool: "org.ziptie.tools.scripts.commandRunner",
      managedNetwork: network,
      ipResolutionScheme: "ipCsv",
      ipResolutionData: `"${target}@${network}"`,
      backupOnCompletion: String(backup),
      "input.commandList": commands.join("\n"),
    },
  };
}

function envBoolean(name, defaultValue = false) {
  const value = process.env[name];
  return value == null || !value.trim()
    ? defaultValue
    : ["1", "true", "yes", "on"].includes(value.trim().toLowerCase());
}

async function loadDotEnv(file) {
  let text;
  try {
    text = await readFile(file, "utf8");
  } catch (error) {
    if (error.code === "ENOENT") return;
    throw error;
  }
  for (const raw of text.split(/\r?\n/)) {
    const line = raw.trim();
    if (!line || line.startsWith("#") || !line.includes("=")) continue;
    const offset = line.indexOf("=");
    process.env[line.slice(0, offset).trim()] = line
      .slice(offset + 1)
      .trim()
      .replace(/^(['"])(.*)\1$/, "$2");
  }
}

async function loadConfig(directory) {
  await loadDotEnv(path.join(directory, ".env"));
  for (const name of ["NETLD_BASE_URL", "NETLD_API_KEY", "NETLD_TARGET"]) {
    if (!process.env[name]?.trim()) {
      throw new ExampleError(`Set ${name} in .env before running this example.`);
    }
  }
  const commandFile = path.resolve(directory, process.env.NETLD_COMMAND_FILE || "commands.txt");
  const commands = (await readFile(commandFile, "utf8"))
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);
  return {
    baseUrl: process.env.NETLD_BASE_URL.replace(/\/$/, ""),
    apiKey: process.env.NETLD_API_KEY,
    network: process.env.NETLD_NETWORK?.trim() || "Default",
    target: process.env.NETLD_TARGET.trim(),
    commands,
    outputDir: path.resolve(directory, process.env.NETLD_OUTPUT_DIR || "output"),
    runJob: envBoolean("NETLD_RUN_JOB"),
    pollMilliseconds: Number(process.env.NETLD_POLL_SECONDS || 2) * 1000,
    timeoutMilliseconds: Number(process.env.NETLD_WAIT_TIMEOUT_SECONDS || 300) * 1000,
    backup: envBoolean("NETLD_BACKUP_ON_COMPLETION"),
  };
}

class NetLDClient {
  constructor(baseUrl, apiKey, timeout = 30000) {
    this.baseUrl = baseUrl;
    this.apiKey = apiKey;
    this.timeout = timeout;
    this.cookies = "";
  }

  headers(extra = {}) {
    return {
      Authorization: `Bearer ${this.apiKey}`,
      ...(this.cookies ? { Cookie: this.cookies } : {}),
      ...extra,
    };
  }

  async request(pathname, options = {}) {
    let response;
    try {
      response = await fetch(`${this.baseUrl}${pathname}`, {
        redirect: "manual",
        signal: AbortSignal.timeout(this.timeout),
        ...options,
        headers: this.headers(options.headers),
      });
    } catch {
      throw new ExampleError(`Could not reach ${this.baseUrl}.`);
    }
    if (response.status >= 300 && response.status < 400) {
      throw new ExampleError(`Request redirected to ${response.headers.get("location") || ""}.`);
    }
    if (!response.ok) throw new ExampleError(`Request failed with HTTP ${response.status}.`);
    const setCookies = response.headers.getSetCookie?.() || splitSetCookie(response.headers.get("set-cookie") || "");
    if (setCookies.length) this.cookies = setCookies.map((item) => item.split(";", 1)[0]).join("; ");
    return response;
  }

  async login() {
    await this.request("/rest");
  }

  async call(method, parameters = {}) {
    const response = await this.request("/rest", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ jsonrpc: "2.0", method, params: parameters, id: randomUUID() }),
    });
    const data = await response.json();
    if (data.error) throw new ExampleError(`${method} failed: ${JSON.stringify(data.error)}`);
    return data.result;
  }

  async downloadDetail(executionId, recordId) {
    const query = new URLSearchParams({ executionId, recordId });
    return (await this.request(`/servlet/pluginDetail?${query}`)).text();
  }
}

const sleep = (milliseconds) => new Promise((resolve) => setTimeout(resolve, milliseconds));

function splitSetCookie(header) {
  return header ? header.split(/,(?=\s*[^;=]+=[^;]+)/) : [];
}

async function waitForCompletion(client, execution, pollMilliseconds, timeoutMilliseconds) {
  const deadline = Date.now() + timeoutMilliseconds;
  let current = execution;
  while (current.endTime == null) {
    if (Date.now() >= deadline) {
      throw new ExampleError(`Execution ${execution.id} did not finish within ${timeoutMilliseconds / 1000} seconds.`);
    }
    await sleep(pollMilliseconds);
    current = await client.call("Scheduler.getExecutionDataById", { executionId: execution.id });
    if (!current) throw new ExampleError(`Scheduler returned no data for execution ${execution.id}.`);
  }
  return current;
}

async function exportDetails(client, execution, outputDir) {
  const details = (await client.call("Plugins.getExecutionDetails", { executionId: execution.id })) || [];
  if (!details.length) throw new ExampleError(`No device output was returned for execution ${execution.id}.`);
  await mkdir(outputDir, { recursive: true });
  const paths = [];
  for (const detail of details) {
    const date = new Date(Number(detail.startTime || execution.startTime || 0));
    const timestamp = date.toISOString().replace(/[-:]/g, "").replace(/\.\d{3}/, "");
    const identity = safeFilename(`${detail.managedNetwork || "network"}_${detail.ipAddress || "device"}`);
    const destination = path.join(outputDir, `${timestamp}_${execution.id}_${detail.id}_${identity}.log`);
    await writeFile(destination, await client.downloadDetail(execution.id, detail.id), "utf8");
    paths.push(destination);
  }
  return paths;
}

export async function main() {
  const directory = path.dirname(fileURLToPath(import.meta.url));
  const config = await loadConfig(directory);
  const job = buildJob(config.network, config.target, config.commands, config.backup);
  console.log(JSON.stringify(job, null, 2));
  if (!config.runJob) {
    console.log("Dry run only. Set NETLD_RUN_JOB=true after reviewing this job.");
    return;
  }
  const client = new NetLDClient(config.baseUrl, config.apiKey);
  await client.login();
  const execution = await client.call("Scheduler.runNow", { jobData: job });
  const final = await waitForCompletion(client, execution, config.pollMilliseconds, config.timeoutMilliseconds);
  console.log(JSON.stringify(final, null, 2));
  for (const destination of await exportDetails(client, final, config.outputDir)) {
    console.log(`Wrote ${destination}`);
  }
  if (final.status != null && final.status !== "OK") {
    throw new ExampleError(`Execution completed with status ${final.status}.`);
  }
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error) => {
    console.error(`Error: ${error.message}`);
    process.exitCode = 1;
  });
}
