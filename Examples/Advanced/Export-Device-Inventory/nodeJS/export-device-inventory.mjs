#!/usr/bin/env node

import { randomUUID } from "node:crypto";
import { mkdir, open, readFile, rename, rm } from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { fileURLToPath, pathToFileURL } from "node:url";

export const CSV_FIELDS = [
  "network", "ipAddress", "hostname", "adapterId", "deviceType",
  "hardwareVendor", "model", "serialNumber", "softwareVendor", "osVersion",
  "backupStatus", "complianceState", "lastBackup", "lastTelemetry", "memoSummary",
  "custom1", "custom2", "custom3", "custom4", "custom5",
];

export class ExampleError extends Error {}

export function parseNetworks(value) {
  const networks = value.split(",").map((item) => item.trim()).filter(Boolean);
  if (!networks.length) throw new ExampleError("NETLD_NETWORKS must contain at least one managed network.");
  return networks;
}

export function csvCell(value) {
  if (value == null) return "";
  const text = String(value);
  return /[",\r\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}

function csvRow(values) {
  return `${values.map(csvCell).join(",")}\n`;
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
    process.env[line.slice(0, offset).trim()] = line.slice(offset + 1).trim().replace(/^(['"])(.*)\1$/, "$2");
  }
}

async function loadConfig(directory, envFile, formatOverride) {
  await loadDotEnv(envFile);
  for (const name of ["NETLD_BASE_URL", "NETLD_API_KEY"]) {
    if (!process.env[name]?.trim()) throw new ExampleError(`Set ${name} in .env before running this example.`);
  }
  const pageSize = Number.parseInt(process.env.NETLD_PAGE_SIZE || "500", 10);
  if (!Number.isInteger(pageSize) || pageSize <= 0) throw new ExampleError("NETLD_PAGE_SIZE must be a positive integer.");
  const format = (formatOverride || process.env.NETLD_OUTPUT_FORMAT || "csv").trim().toLowerCase();
  if (!["csv", "json"].includes(format)) throw new ExampleError("NETLD_OUTPUT_FORMAT must be either csv or json.");
  return {
    baseUrl: process.env.NETLD_BASE_URL.replace(/\/$/, ""),
    apiKey: process.env.NETLD_API_KEY,
    networks: parseNetworks(process.env.NETLD_NETWORKS || "Default"),
    outputFile: path.resolve(directory, process.env.NETLD_OUTPUT_FILE || `inventory.${format}`),
    format,
    pageSize,
    scheme: process.env.NETLD_SEARCH_SCHEME?.trim() || "ipAddress",
    query: process.env.NETLD_SEARCH_QUERY || "",
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
    return { Authorization: `Bearer ${this.apiKey}`, ...(this.cookies ? { Cookie: this.cookies } : {}), ...extra };
  }

  async request(options = {}) {
    let response;
    try {
      response = await fetch(`${this.baseUrl}/rest`, {
        redirect: "manual", signal: AbortSignal.timeout(this.timeout), ...options,
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
    await this.request();
  }

  async call(method, parameters = {}) {
    const response = await this.request({
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ jsonrpc: "2.0", method, params: parameters, id: randomUUID() }),
    });
    const data = await response.json();
    if (data.error) throw new ExampleError(`${method} failed: ${JSON.stringify(data.error)}`);
    return data.result;
  }

  async searchInventory(networks, scheme, query, offset, pageSize) {
    const result = await this.call("Inventory.search", {
      network: networks, scheme, query: query.endsWith("\n") ? query : `${query}\n`,
      pageData: { offset, pageSize }, sortColumn: "ipAddress", descending: false,
    });
    if (!result || typeof result !== "object") throw new ExampleError("Inventory.search returned no page data.");
    return result;
  }
}

function splitSetCookie(header) {
  return header ? header.split(/,(?=\s*[^;=]+=[^;]+)/) : [];
}

export async function exportInventory(client, options) {
  const { networks, scheme, query, pageSize, outputFile, format = "csv" } = options;
  if (!["csv", "json"].includes(format)) throw new ExampleError("Output format must be either csv or json.");
  await mkdir(path.dirname(outputFile), { recursive: true });
  const temporaryFile = path.join(path.dirname(outputFile), `.${path.basename(outputFile)}.${randomUUID()}.tmp`);
  let handle;
  let count = 0;
  try {
    handle = await open(temporaryFile, "wx");
    if (format === "csv") await handle.write(csvRow(CSV_FIELDS));
    else await handle.write("[\n");
    let firstJsonRecord = true;
    let offset = 0;
    let total;
    while (true) {
      const page = await client.searchInventory(networks, scheme, query, offset, pageSize);
      const devices = page.devices || [];
      if (!Array.isArray(devices)) throw new ExampleError("Inventory.search returned an invalid devices collection.");
      for (const device of devices) {
        if (format === "csv") {
          await handle.write(csvRow(CSV_FIELDS.map((field) => device[field])));
        } else {
          const record = Object.fromEntries(CSV_FIELDS.map((field) => [field, device[field] ?? null]));
          if (!firstJsonRecord) await handle.write(",\n");
          const rendered = JSON.stringify(record, null, 2).split("\n").map((line) => `  ${line}`).join("\n");
          await handle.write(rendered);
          firstJsonRecord = false;
        }
        count += 1;
      }
      const returnedPageSize = Number(page.pageSize || pageSize);
      if (!Number.isInteger(returnedPageSize) || returnedPageSize <= 0) {
        throw new ExampleError("Inventory.search returned an invalid page size.");
      }
      if (total == null && page.total != null) total = Number(page.total);
      if (total != null && offset + devices.length >= total) break;
      if (total == null && devices.length < returnedPageSize) break;
      if (!devices.length) throw new ExampleError("Inventory.search returned an empty page before the reported total.");
      offset += returnedPageSize;
    }
    if (format === "json") await handle.write("\n]\n");
    await handle.close();
    handle = undefined;
    await rename(temporaryFile, outputFile);
    return count;
  } catch (error) {
    await handle?.close().catch(() => {});
    await rm(temporaryFile, { force: true }).catch(() => {});
    throw error;
  }
}

export async function main() {
  const directory = path.dirname(fileURLToPath(import.meta.url));
  const envOffset = process.argv.indexOf("--env");
  const formatOffset = process.argv.indexOf("--format");
  if (envOffset >= 0 && !process.argv[envOffset + 1]) throw new ExampleError("--env requires a file path.");
  if (formatOffset >= 0 && !process.argv[formatOffset + 1]) throw new ExampleError("--format requires csv or json.");
  const envFile = envOffset >= 0 ? path.resolve(process.argv[envOffset + 1]) : path.join(directory, ".env");
  const config = await loadConfig(directory, envFile, formatOffset >= 0 ? process.argv[formatOffset + 1] : undefined);
  const client = new NetLDClient(config.baseUrl, config.apiKey);
  await client.login();
  const count = await exportInventory(client, config);
  console.log(`Wrote ${count} devices to ${config.outputFile}`);
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error) => {
    console.error(`Error: ${error.message}`);
    process.exitCode = 1;
  });
}
