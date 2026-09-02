#!/usr/bin/env node
import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

export const STATE_FORMAT = "logicvein-netld-configuration-archive-state";
export const RUN_FORMAT = "logicvein-netld-configuration-archive-run";
const VERSION = 1;

export function loadEnv(file) {
  if (!fs.existsSync(file)) return;
  for (const raw of fs.readFileSync(file, "utf8").split(/\r?\n/)) {
    const match = raw.match(/^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)\s*$/);
    if (!match || raw.trimStart().startsWith("#")) continue;
    let value = match[2];
    if ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'"))) value = value.slice(1, -1);
    process.env[match[1]] = value;
  }
}

const safeName = (value, fallback) => value.trim().replace(/[^A-Za-z0-9._-]+/g, "_").replace(/^[._]+|[._]+$/g, "") || fallback;
const pathHash = value => crypto.createHash("sha256").update(value).digest("hex").slice(0, 8);
const asPath = (base, value) => path.isAbsolute(value) ? value : path.join(base, value);

export function configFromEnv(base) {
  const required = ["NETLD_BASE_URL", "NETLD_API_KEY"];
  for (const name of required) if (!process.env[name]?.trim()) throw new Error(`${name} is required.`);
  const networks = [...new Set((process.env.NETLD_NETWORKS || "Default").split(",").map(v => v.trim()).filter(Boolean))].sort();
  const initialMode = (process.env.NETLD_INITIAL_MODE || "latest").trim().toLowerCase();
  if (!networks.length) throw new Error("NETLD_NETWORKS must contain at least one managed network.");
  if (!["latest", "all"].includes(initialMode)) throw new Error("NETLD_INITIAL_MODE must be either latest or all.");
  const inventoryPageSize = Number(process.env.NETLD_INVENTORY_PAGE_SIZE || 500);
  const historyPageSize = Number(process.env.NETLD_HISTORY_PAGE_SIZE || 500);
  if (!Number.isInteger(inventoryPageSize) || inventoryPageSize < 1 || !Number.isInteger(historyPageSize) || historyPageSize < 1) throw new Error("Page sizes must be positive integers.");
  return {
    baseUrl: process.env.NETLD_BASE_URL.trim().replace(/\/$/, ""), apiKey: process.env.NETLD_API_KEY.trim(), networks,
    archiveDir: asPath(base, process.env.NETLD_ARCHIVE_DIR || "configuration-archive"),
    statePath: asPath(base, process.env.NETLD_STATE_FILE || "configuration-archive-state.json"),
    runReportPath: asPath(base, process.env.NETLD_RUN_REPORT_FILE || "configuration-archive-run.json"),
    inventoryPageSize, historyPageSize, searchScheme: process.env.NETLD_SEARCH_SCHEME?.trim() || "ipAddress",
    searchQuery: process.env.NETLD_SEARCH_QUERY || "", initialMode,
  };
}

export class NetLDClient {
  constructor(config) { this.config = config; this.cookie = ""; }
  async request(method, body) {
    const headers = { Authorization: `Bearer ${this.config.apiKey}` };
    if (this.cookie) headers.Cookie = this.cookie;
    if (body) headers["Content-Type"] = "application/json";
    const response = await fetch(`${this.config.baseUrl}/rest`, { method, headers, body: body && JSON.stringify(body), redirect: "manual" });
    const cookie = response.headers.get("set-cookie"); if (cookie) this.cookie = cookie.split(";", 1)[0];
    if (!response.ok) throw new Error(`Request failed with HTTP ${response.status}.`);
    return response;
  }
  async login() { await this.request("GET"); }
  async call(method, params) {
    const response = await this.request("POST", { jsonrpc: "2.0", method, params, id: crypto.randomUUID() });
    const data = await response.json();
    if (data.error) throw new Error(`${method} failed: ${JSON.stringify(data.error)}`);
    return data.result;
  }
  searchInventory(config, offset) {
    const query = config.searchQuery.endsWith("\n") ? config.searchQuery : `${config.searchQuery}\n`;
    return this.call("Inventory.search", { network: config.networks, scheme: config.searchScheme, query,
      pageData: { offset, pageSize: config.inventoryPageSize }, sortColumn: "ipAddress", descending: false });
  }
  configurationHistory(device, offset, pageSize) {
    return this.call("Configuration.retrieveConfigHistory", { pageData: { offset, pageSize, total: 0, configHistoryItems: [] },
      networks: [device.network], scheme: "ipAddress", data: device.ipAddress, sortColumn: "session", descending: true });
  }
  retrieveRevision(item) {
    return this.call("Configuration.retrieveRevision", { network: item.managedNetwork, ipAddress: item.ipAddress,
      configPath: item.path, timestamp: item.lastChanged });
  }
}

async function collectPages(fetchPage, pageSize, listName, stopBefore = null) {
  const output = []; let offset = 0; let total = null;
  while (true) {
    const page = await fetchPage(offset); const values = page?.[listName] || [];
    for (const value of values) {
      if (stopBefore !== null && Number(value.lastChanged) < stopBefore) return output;
      output.push(value);
    }
    if (total === null && page?.total !== undefined && page.total !== null) total = Number(page.total);
    const actualPageSize = Number(page?.pageSize || pageSize);
    if ((total !== null && offset + values.length >= total) || (total === null && values.length < actualPageSize)) return output;
    if (!values.length) throw new Error(`${listName} returned an empty page before the reported total.`);
    offset += actualPageSize;
  }
}

export function selectCandidates(items, stateEntry, initialMode) {
  let selected;
  if (!stateEntry) {
    if (initialMode === "all") selected = items;
    else { const newest = new Map(); for (const item of items) if (!newest.has(item.path)) newest.set(item.path, item); selected = [...newest.values()]; }
  } else {
    const paths = new Set(stateEntry.pathsAtLastChanged || []), watermark = Number(stateEntry.lastChanged);
    selected = items.filter(i => Number(i.lastChanged) > watermark || (Number(i.lastChanged) === watermark && !paths.has(i.path)));
  }
  const unique = new Map(selected.map(i => [`${Number(i.lastChanged)}\0${i.path}`, i]));
  return [...unique.values()].sort((a, b) => Number(a.lastChanged) - Number(b.lastChanged) || a.path.localeCompare(b.path));
}

function loadState(file) {
  if (!fs.existsSync(file)) return { format: STATE_FORMAT, formatVersion: VERSION, devices: {} };
  const state = JSON.parse(fs.readFileSync(file, "utf8"));
  if (state.format !== STATE_FORMAT || state.formatVersion !== VERSION || !state.devices || Array.isArray(state.devices)) throw new Error("The archive state file has an unsupported format.");
  return state;
}
function atomicWrite(file, content) {
  fs.mkdirSync(path.dirname(file), { recursive: true }); const temporary = path.join(path.dirname(file), `.${path.basename(file)}.${crypto.randomUUID()}.tmp`);
  try { fs.writeFileSync(temporary, content, { mode: 0o600 }); fs.renameSync(temporary, file); } catch (error) { try { fs.unlinkSync(temporary); } catch {} throw error; }
}
const writeJson = (file, value) => atomicWrite(file, `${JSON.stringify(value, null, 2)}\n`);

function archiveOne(config, item, revision) {
  const encoded = revision.content || "";
  if (!/^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$/.test(encoded)) throw new Error("Configuration revision content is not valid Base64.");
  const content = Buffer.from(encoded, "base64"), stem = `${Number(item.lastChanged)}_${safeName(item.path, "config")}_${pathHash(item.path)}`;
  const extension = String(revision.mimeType || item.mimeType || "").startsWith("text/") ? ".txt" : ".bin";
  const directory = path.join(config.archiveDir, safeName(item.managedNetwork, "network"), safeName(item.ipAddress, "device"));
  const contentPath = path.join(directory, stem + extension), metadataPath = path.join(directory, `${stem}.metadata.json`);
  atomicWrite(contentPath, content);
  const { content: ignored, ...revisionMetadata } = revision;
  writeJson(metadataPath, { network: item.managedNetwork, ipAddress: item.ipAddress, configPath: item.path,
    lastChanged: Number(item.lastChanged), history: item, revision: revisionMetadata, contentFile: path.basename(contentPath) });
  return { network: item.managedNetwork, ipAddress: item.ipAddress, configPath: item.path, lastChanged: Number(item.lastChanged),
    mimeType: revision.mimeType, size: content.length, contentFile: path.relative(config.archiveDir, contentPath), metadataFile: path.relative(config.archiveDir, metadataPath) };
}

export async function archiveConfigurationRevisions(client, config, generatedAt = new Date().toISOString().replace(/\.\d{3}Z$/, "Z")) {
  const state = loadState(config.statePath), archived = [], failures = [];
  const devices = await collectPages(offset => client.searchInventory(config, offset), config.inventoryPageSize, "devices");
  for (const device of devices) {
    const key = `${device.network}@${device.ipAddress}`, oldEntry = state.devices[key]; let candidates;
    try {
      const items = await collectPages(offset => client.configurationHistory(device, offset, config.historyPageSize), config.historyPageSize, "configHistoryItems", oldEntry ? Number(oldEntry.lastChanged) : null);
      candidates = selectCandidates(items, oldEntry, config.initialMode);
    } catch (error) { failures.push({ stage: "history", network: device.network, ipAddress: device.ipAddress, error: error.message }); continue; }
    let failed = false;
    for (const item of candidates) try { archived.push(archiveOne(config, item, await client.retrieveRevision(item))); }
    catch (error) { failed = true; failures.push({ stage: "revision", network: item.managedNetwork, ipAddress: item.ipAddress, configPath: item.path, lastChanged: item.lastChanged, error: error.message }); }
    if (candidates.length && !failed) {
      const newest = Math.max(...candidates.map(i => Number(i.lastChanged))); let paths = candidates.filter(i => Number(i.lastChanged) === newest).map(i => i.path);
      if (oldEntry && newest === Number(oldEntry.lastChanged)) paths.push(...(oldEntry.pathsAtLastChanged || []));
      state.devices[key] = { lastChanged: newest, pathsAtLastChanged: [...new Set(paths)].sort() };
    }
  }
  const report = { format: RUN_FORMAT, formatVersion: VERSION, generatedAt, initialMode: config.initialMode, deviceCount: devices.length,
    archivedCount: archived.length, failureCount: failures.length, archived, failures };
  writeJson(config.statePath, state); writeJson(config.runReportPath, report); return report;
}

async function main() {
  const here = path.dirname(fileURLToPath(import.meta.url)); const index = process.argv.indexOf("--env"); const envFile = index >= 0 ? process.argv[index + 1] : path.join(here, ".env");
  loadEnv(envFile); const config = configFromEnv(here); const client = new NetLDClient(config); await client.login(); const report = await archiveConfigurationRevisions(client, config);
  console.log(`Processed ${report.deviceCount} devices and archived ${report.archivedCount} revisions`); console.log(`Recorded ${report.failureCount} failures in ${config.runReportPath}`); process.exitCode = report.failureCount ? 2 : 0;
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main().catch(error => { console.error(`Error: ${error.message}`); process.exitCode = 1; });
