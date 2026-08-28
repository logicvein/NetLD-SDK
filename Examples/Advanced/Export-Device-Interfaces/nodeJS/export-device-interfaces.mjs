#!/usr/bin/env node

import { randomUUID } from "node:crypto";
import { mkdir, open, readFile, rename, rm } from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { fileURLToPath, pathToFileURL } from "node:url";

export const INTERFACE_FIELDS = [
  "network", "deviceIpAddress", "hostname", "interfaceId", "interfaceIndex",
  "name", "ifName", "type", "description", "comment", "macAddress", "mtu",
  "speed", "adminUp", "vrfName", "ipAddresses",
];
export const FAILURE_FIELDS = ["network", "deviceIpAddress", "hostname", "error"];

export class ExampleError extends Error {}

export function parseNetworks(value) {
  const networks = value.split(",").map((item) => item.trim()).filter(Boolean);
  if (!networks.length) throw new ExampleError("NETLD_NETWORKS must contain at least one managed network.");
  return networks;
}

function csvCell(value) {
  if (value == null) return "";
  const text = String(value);
  return /[",\r\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}

function csvRow(values) {
  return `${values.map(csvCell).join(",")}\n`;
}

export function flattenIpAddresses(interfaceData) {
  return (interfaceData.ipAddresses || [])
    .filter((address) => String(address.ipAddress || "").trim())
    .map((address) => address.cidrPrefix == null ? String(address.ipAddress) : `${address.ipAddress}/${address.cidrPrefix}`)
    .join(";");
}

export function interfaceRow(device, interfaceData) {
  return {
    network: device.network, deviceIpAddress: device.ipAddress, hostname: device.hostname,
    interfaceId: interfaceData.id, interfaceIndex: interfaceData.index,
    name: interfaceData.name, ifName: interfaceData.ifName, type: interfaceData.type,
    description: interfaceData.description, comment: interfaceData.comment,
    macAddress: interfaceData.macAddress, mtu: interfaceData.mtu, speed: interfaceData.speed,
    adminUp: interfaceData.adminUp, vrfName: interfaceData.vrfName,
    ipAddresses: flattenIpAddresses(interfaceData),
  };
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

async function loadConfig(directory, envFile) {
  await loadDotEnv(envFile);
  for (const name of ["NETLD_BASE_URL", "NETLD_API_KEY"]) {
    if (!process.env[name]?.trim()) throw new ExampleError(`Set ${name} in the environment file.`);
  }
  const pageSize = Number.parseInt(process.env.NETLD_PAGE_SIZE || "500", 10);
  if (!Number.isInteger(pageSize) || pageSize <= 0) throw new ExampleError("NETLD_PAGE_SIZE must be a positive integer.");
  return {
    baseUrl: process.env.NETLD_BASE_URL.replace(/\/$/, ""), apiKey: process.env.NETLD_API_KEY,
    networks: parseNetworks(process.env.NETLD_NETWORKS || "Default"), pageSize,
    outputFile: path.resolve(directory, process.env.NETLD_OUTPUT_FILE || "interfaces.csv"),
    failureFile: path.resolve(directory, process.env.NETLD_FAILURE_FILE || "interface-failures.csv"),
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

  async searchInventory(networks, scheme, query, offset, pageSize) {
    const result = await this.call("Inventory.search", {
      network: networks, scheme, query: query.endsWith("\n") ? query : `${query}\n`,
      pageData: { offset, pageSize }, sortColumn: "ipAddress", descending: false,
    });
    if (!result || typeof result !== "object") throw new ExampleError("Inventory.search returned no page data.");
    return result;
  }

  async getDeviceInterfaces(network, ipAddress) {
    const result = await this.call("Inventory.getDeviceInterfaces", { network, ipAddress });
    if (result == null) return [];
    if (!Array.isArray(result)) throw new ExampleError("Inventory.getDeviceInterfaces returned an invalid collection.");
    return result;
  }
}

function splitSetCookie(header) {
  return header ? header.split(/,(?=\s*[^;=]+=[^;]+)/) : [];
}

export async function exportInterfaces(client, config) {
  await mkdir(path.dirname(config.outputFile), { recursive: true });
  await mkdir(path.dirname(config.failureFile), { recursive: true });
  const interfaceTemp = path.join(path.dirname(config.outputFile), `.${path.basename(config.outputFile)}.${randomUUID()}.tmp`);
  const failureTemp = path.join(path.dirname(config.failureFile), `.${path.basename(config.failureFile)}.${randomUUID()}.tmp`);
  let interfaceHandle;
  let failureHandle;
  let deviceCount = 0;
  let interfaceCount = 0;
  let failureCount = 0;
  try {
    interfaceHandle = await open(interfaceTemp, "wx");
    failureHandle = await open(failureTemp, "wx");
    await interfaceHandle.write(csvRow(INTERFACE_FIELDS));
    await failureHandle.write(csvRow(FAILURE_FIELDS));
    let offset = 0;
    let total;
    while (true) {
      const page = await client.searchInventory(config.networks, config.scheme, config.query, offset, config.pageSize);
      const devices = page.devices || [];
      if (!Array.isArray(devices)) throw new ExampleError("Inventory.search returned an invalid devices collection.");
      for (const device of devices) {
        deviceCount += 1;
        let interfaces;
        try {
          interfaces = await client.getDeviceInterfaces(device.network, device.ipAddress);
        } catch (error) {
          const failure = { network: device.network, deviceIpAddress: device.ipAddress, hostname: device.hostname, error: error.message };
          await failureHandle.write(csvRow(FAILURE_FIELDS.map((field) => failure[field])));
          failureCount += 1;
          continue;
        }
        for (const interfaceData of interfaces) {
          const row = interfaceRow(device, interfaceData);
          await interfaceHandle.write(csvRow(INTERFACE_FIELDS.map((field) => row[field])));
          interfaceCount += 1;
        }
      }
      const returnedPageSize = Number(page.pageSize || config.pageSize);
      if (!Number.isInteger(returnedPageSize) || returnedPageSize <= 0) throw new ExampleError("Inventory.search returned an invalid page size.");
      if (total == null && page.total != null) total = Number(page.total);
      if (total != null && offset + devices.length >= total) break;
      if (total == null && devices.length < returnedPageSize) break;
      if (!devices.length) throw new ExampleError("Inventory.search returned an empty page before the reported total.");
      offset += returnedPageSize;
    }
    await interfaceHandle.close(); interfaceHandle = undefined;
    await failureHandle.close(); failureHandle = undefined;
    await rename(interfaceTemp, config.outputFile);
    await rename(failureTemp, config.failureFile);
    return { deviceCount, interfaceCount, failureCount };
  } catch (error) {
    await interfaceHandle?.close().catch(() => {});
    await failureHandle?.close().catch(() => {});
    await rm(interfaceTemp, { force: true }).catch(() => {});
    await rm(failureTemp, { force: true }).catch(() => {});
    throw error;
  }
}

export async function main() {
  const directory = path.dirname(fileURLToPath(import.meta.url));
  const envOffset = process.argv.indexOf("--env");
  const envFile = envOffset >= 0 ? path.resolve(process.argv[envOffset + 1]) : path.join(directory, ".env");
  if (envOffset >= 0 && !process.argv[envOffset + 1]) throw new ExampleError("--env requires a file path.");
  const config = await loadConfig(directory, envFile);
  const client = new NetLDClient(config.baseUrl, config.apiKey);
  await client.login();
  const result = await exportInterfaces(client, config);
  console.log(`Processed ${result.deviceCount} devices and wrote ${result.interfaceCount} interfaces to ${config.outputFile}`);
  console.log(`Wrote ${result.failureCount} device lookup failures to ${config.failureFile}`);
  return result.failureCount ? 2 : 0;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().then((code) => { process.exitCode = code; }).catch((error) => {
    console.error(`Error: ${error.message}`);
    process.exitCode = 1;
  });
}
