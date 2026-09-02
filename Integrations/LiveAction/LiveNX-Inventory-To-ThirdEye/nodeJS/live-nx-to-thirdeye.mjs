#!/usr/bin/env node

import "dotenv/config";

import { randomUUID } from "node:crypto";
import { isIP } from "node:net";
import process from "node:process";
import { pathToFileURL } from "node:url";

import { parse } from "csv-parse/sync";


export class BridgeError extends Error {}


export function environmentBoolean(name, defaultValue = false) {
  const value = process.env[name];
  if (value === undefined || value.trim() === "") {
    return defaultValue;
  }
  return ["1", "true", "yes", "on"].includes(value.trim().toLowerCase());
}


function requiredEnvironmentValue(name) {
  const value = process.env[name];
  if (!value) {
    throw new BridgeError(`Set ${name} in .env before running this integration.`);
  }
  return value;
}


function normalizedHeader(value) {
  return value.toUpperCase().replaceAll(/[^A-Z0-9]/g, "");
}


export function canonicalIpAddress(value) {
  const candidate = String(value || "").trim();
  const version = isIP(candidate);
  if (version === 4) {
    return candidate
      .split(".")
      .map((part) => Number.parseInt(part, 10))
      .join(".");
  }
  if (version === 6) {
    return new URL(`http://[${candidate}]/`).hostname.slice(1, -1);
  }
  return null;
}


export function sortedIpAddresses(addresses) {
  return [...addresses].sort((left, right) => {
    const versionDifference = isIP(left) - isIP(right);
    return versionDifference || left.localeCompare(right, "en", { numeric: true });
  });
}


export function parseLiveNXDeviceIps(csvText, { requireVendor = true } = {}) {
  let rows;
  try {
    rows = parse(csvText, {
      bom: true,
      columns: true,
      relax_column_count: true,
      skip_empty_lines: true,
      trim: true,
    });
  } catch (error) {
    throw new BridgeError(`Could not parse the LiveNX device CSV: ${error.message}`);
  }
  if (rows.length === 0) {
    return new Set();
  }

  const fields = new Map(
    Object.keys(rows[0]).map((name) => [normalizedHeader(name), name]),
  );
  const ipField = ["IPADDRESS", "MANAGEMENTIPADDRESS", "MANAGEMENTIP", "IP"]
    .map((name) => fields.get(name))
    .find(Boolean);
  if (!ipField) {
    throw new BridgeError(
      `The LiveNX CSV does not contain a recognized IP-address column. Available columns: ${Object.keys(
        rows[0],
      ).join(", ")}`,
    );
  }

  const vendorField = fields.get("VENDOR");
  if (requireVendor && !vendorField) {
    throw new BridgeError(
      "LIVENX_REQUIRE_VENDOR=true, but the LiveNX CSV has no VENDOR column.",
    );
  }

  const addresses = new Set();
  for (const row of rows) {
    if (requireVendor && !String(row[vendorField] || "").trim()) {
      continue;
    }
    const address = canonicalIpAddress(row[ipField]);
    if (address) {
      addresses.add(address);
    }
  }
  return addresses;
}


export function prepareDiscoveryJob(jobData, network, addresses) {
  const prepared = structuredClone(jobData);
  const parameters = prepared?.jobParameters;
  if (!parameters || typeof parameters !== "object" || Array.isArray(parameters)) {
    throw new BridgeError("The selected job has no jobParameters object.");
  }
  if (!("includedAddresses" in parameters)) {
    throw new BridgeError(
      "The selected job is not a compatible Discover Devices job: " +
        "jobParameters.includedAddresses is missing.",
    );
  }

  if ("managedNetwork" in prepared) {
    prepared.managedNetwork = network;
  }
  if ("managedNetworks" in prepared) {
    prepared.managedNetworks = Array.isArray(prepared.managedNetworks) ? [network] : network;
  }
  if ("managedNetwork" in parameters) {
    parameters.managedNetwork = network;
  }
  parameters.includedAddresses = sortedIpAddresses(addresses).join(",");
  return prepared;
}


function isRedirect(response) {
  return response.status >= 300 && response.status < 400;
}


function splitSetCookie(header) {
  return header ? header.split(/,(?=\s*[^;=]+=[^;]+)/) : [];
}


export class LiveNXClient {
  constructor(baseUrl, apiToken, exportPath, timeout = 30000, fetchFunction = fetch) {
    this.baseUrl = baseUrl.replace(/\/$/, "");
    this.apiToken = apiToken;
    this.exportPath = `/${exportPath.replace(/^\//, "")}`;
    this.timeout = timeout;
    this.fetch = fetchFunction;
  }

  async exportDevicesCsv() {
    const url = `${this.baseUrl}${this.exportPath}`;
    let response;
    try {
      response = await this.fetch(url, {
        headers: {
          Accept: "text/csv",
          Authorization: `Bearer ${this.apiToken}`,
        },
        redirect: "manual",
        signal: AbortSignal.timeout(this.timeout),
      });
    } catch (error) {
      throw new BridgeError(`Could not retrieve the LiveNX device export from ${url}.`);
    }
    if (isRedirect(response)) {
      throw new BridgeError(
        "The LiveNX export request was redirected. Confirm LIVENX_BASE_URL, " +
          "LIVENX_DEVICE_EXPORT_PATH, and the API token.",
      );
    }
    if (!response.ok) {
      throw new BridgeError(`LiveNX device export failed with HTTP ${response.status}.`);
    }
    return response.text();
  }
}


export class NetLDClient {
  constructor(baseUrl, apiKey, timeout = 30000, debug = false, fetchFunction = fetch) {
    this.baseUrl = baseUrl.replace(/\/$/, "");
    this.apiKey = apiKey;
    this.timeout = timeout;
    this.debug = debug;
    this.fetch = fetchFunction;
    this.cookieHeader = "";
  }

  headers(extra = {}) {
    return {
      Authorization: `Bearer ${this.apiKey}`,
      "Content-Type": "application/json",
      ...(this.cookieHeader ? { Cookie: this.cookieHeader } : {}),
      ...extra,
    };
  }

  updateCookies(response) {
    const setCookie = response.headers.getSetCookie
      ? response.headers.getSetCookie()
      : splitSetCookie(response.headers.get("set-cookie") || "");
    this.cookieHeader = setCookie
      .map((cookie) => cookie.split(";")[0])
      .filter(Boolean)
      .join("; ");
  }

  async login() {
    let response;
    try {
      response = await this.fetch(`${this.baseUrl}/rest`, {
        headers: { Authorization: `Bearer ${this.apiKey}` },
        redirect: "manual",
        signal: AbortSignal.timeout(this.timeout),
      });
    } catch (error) {
      throw new BridgeError(`Could not reach ${this.baseUrl}.`);
    }
    if (isRedirect(response)) {
      throw new BridgeError("ThirdEye login redirected instead of creating an API session.");
    }
    if (!response.ok) {
      throw new BridgeError(`ThirdEye login failed with HTTP ${response.status}.`);
    }
    this.updateCookies(response);
  }

  async call(method, params = {}) {
    const payload = {
      jsonrpc: "2.0",
      method,
      params,
      id: randomUUID(),
    };
    if (this.debug) {
      console.log(`ThirdEye request: ${JSON.stringify(payload, null, 2)}`);
    }

    let response;
    try {
      response = await this.fetch(`${this.baseUrl}/rest`, {
        method: "POST",
        headers: this.headers(),
        body: JSON.stringify(payload),
        redirect: "manual",
        signal: AbortSignal.timeout(this.timeout),
      });
    } catch (error) {
      throw new BridgeError(`ThirdEye API call ${method} failed to connect.`);
    }
    if (isRedirect(response)) {
      throw new BridgeError(`ThirdEye API call ${method} was redirected.`);
    }
    if (!response.ok) {
      throw new BridgeError(
        `ThirdEye API call ${method} failed with HTTP ${response.status}.`,
      );
    }

    let data;
    try {
      data = await response.json();
    } catch (error) {
      throw new BridgeError(`ThirdEye API call ${method} returned invalid JSON.`);
    }
    if (data.error) {
      throw new BridgeError(`ThirdEye API call ${method} failed: ${JSON.stringify(data.error)}`);
    }
    return data.result;
  }

  async inventoryAddresses(network, pageSize = 500) {
    const addresses = new Set();
    let offset = 0;
    while (true) {
      const page =
        (await this.call("Inventory.search", {
          network: [network],
          scheme: "ipAddress",
          query: "\n",
          pageData: { offset, pageSize },
          sortColumn: "ipAddress",
          descending: false,
        })) || {};
      const devices = page.devices || [];
      for (const device of devices) {
        const address = canonicalIpAddress(device.ipAddress);
        if (address) {
          addresses.add(address);
        }
      }
      offset += devices.length;
      const total = page.total ?? offset;
      if (devices.length === 0 || offset >= total) {
        return addresses;
      }
    }
  }

  async findJob(network, jobName, pageSize = 100) {
    const matches = [];
    let offset = 0;
    while (true) {
      const page =
        (await this.call("Scheduler.searchJobs", {
          pageData: { offset, jobData: [], pageSize, total: 1 },
          networks: [network],
          sortColumn: "",
          descending: false,
        })) || {};
      const jobs = page.jobData || [];
      matches.push(...jobs.filter((job) => job.jobName === jobName));
      offset += jobs.length;
      const total = page.total ?? offset;
      if (jobs.length === 0 || offset >= total) {
        break;
      }
    }
    if (matches.length === 0) {
      throw new BridgeError(`No available job named "${jobName}" was found.`);
    }
    if (matches.length > 1) {
      throw new BridgeError(
        `Multiple jobs named "${jobName}" were found: ${matches
          .map((job) => job.jobId)
          .join(", ")}`,
      );
    }

    const job = await this.call("Scheduler.getJob", { jobId: matches[0].jobId });
    if (!job) {
      throw new BridgeError(
        `Scheduler.getJob returned no data for job ID ${matches[0].jobId}.`,
      );
    }
    return job;
  }

  runNow(jobData) {
    return this.call("Scheduler.runNow", { jobData });
  }
}


function configurationFromEnvironment() {
  const timeoutSeconds = Number.parseFloat(process.env.REQUEST_TIMEOUT_SECONDS || "30");
  if (!Number.isFinite(timeoutSeconds) || timeoutSeconds <= 0) {
    throw new BridgeError("REQUEST_TIMEOUT_SECONDS must be a number greater than zero.");
  }
  return {
    liveNXBaseUrl: requiredEnvironmentValue("LIVENX_BASE_URL"),
    liveNXApiToken: requiredEnvironmentValue("LIVENX_API_TOKEN"),
    liveNXExportPath: process.env.LIVENX_DEVICE_EXPORT_PATH || "/v1/devices/export/csv",
    requireVendor: environmentBoolean("LIVENX_REQUIRE_VENDOR", true),
    netLDBaseUrl: requiredEnvironmentValue("NETLD_BASE_URL"),
    netLDApiKey: requiredEnvironmentValue("NETLD_API_KEY"),
    network: process.env.NETLD_NETWORK || "Default",
    discoveryJobName: process.env.NETLD_DISCOVERY_JOB_NAME,
    debug: environmentBoolean("NETLD_DEBUG"),
    timeout: timeoutSeconds * 1000,
  };
}


export async function runBridge({ apply = false } = {}) {
  const config = configurationFromEnvironment();
  const liveNX = new LiveNXClient(
    config.liveNXBaseUrl,
    config.liveNXApiToken,
    config.liveNXExportPath,
    config.timeout,
  );
  const netLD = new NetLDClient(
    config.netLDBaseUrl,
    config.netLDApiKey,
    config.timeout,
    config.debug,
  );

  const liveNXAddresses = parseLiveNXDeviceIps(await liveNX.exportDevicesCsv(), {
    requireVendor: config.requireVendor,
  });
  await netLD.login();
  const managedAddresses = await netLD.inventoryAddresses(config.network);
  const missingAddresses = new Set(
    [...liveNXAddresses].filter((address) => !managedAddresses.has(address)),
  );

  console.log(`LiveNX device addresses: ${liveNXAddresses.size}`);
  console.log(`ThirdEye managed addresses: ${managedAddresses.size}`);
  console.log(`Missing from ThirdEye: ${missingAddresses.size}`);
  for (const address of sortedIpAddresses(missingAddresses)) {
    console.log(`  ${address}`);
  }

  if (missingAddresses.size === 0) {
    console.log("No discovery is required.");
    return;
  }
  if (!apply) {
    console.log("Dry run only. Re-run with --apply to start discovery.");
    return;
  }
  if (!config.discoveryJobName) {
    throw new BridgeError(
      "Set NETLD_DISCOVERY_JOB_NAME to an existing Discover Devices job before using --apply.",
    );
  }

  const job = await netLD.findJob(config.network, config.discoveryJobName);
  const prepared = prepareDiscoveryJob(job, config.network, missingAddresses);
  const execution = await netLD.runNow(prepared);
  console.log("Discovery started:");
  console.log(JSON.stringify(execution, null, 2));
}


function showHelp() {
  console.log("Usage: node live-nx-to-thirdeye.mjs [--apply]");
  console.log("");
  console.log("Find LiveNX devices missing from ThirdEye inventory.");
  console.log("  --apply  Run the configured discovery job for missing addresses.");
}


async function main() {
  const unknown = process.argv.slice(2).filter((value) => !["--apply", "--help", "-h"].includes(value));
  if (unknown.length > 0) {
    throw new BridgeError(`Unknown argument: ${unknown[0]}`);
  }
  if (process.argv.includes("--help") || process.argv.includes("-h")) {
    showHelp();
    return;
  }
  await runBridge({ apply: process.argv.includes("--apply") });
}


if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error) => {
    console.error(`Error: ${error.message}`);
    process.exitCode = 1;
  });
}
