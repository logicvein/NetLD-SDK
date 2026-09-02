#!/usr/bin/env node

import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

export const STATE_FORMAT = "logicvein-thirdeye-violation-export-state";
export const RUN_FORMAT = "logicvein-thirdeye-violation-export-run";
const FORMAT_VERSION = 1;
export const CSV_FIELDS = [
  "eventId", "incidentId", "severity", "clearState", "eventType", "network",
  "ipAddress", "hostname", "deviceId", "hostUuid", "measurement",
  "measurementIndex", "message", "occurrences", "triggerId", "created", "updated",
];

export class ExampleError extends Error {}

export function loadEnv(file) {
  if (!fs.existsSync(file)) return;
  for (const raw of fs.readFileSync(file, "utf8").split(/\r?\n/)) {
    const match = raw.match(/^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)\s*$/);
    if (!match || raw.trimStart().startsWith("#")) continue;
    let value = match[2];
    if ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'"))) {
      value = value.slice(1, -1);
    }
    process.env[match[1]] = value;
  }
}

export function parseQueries(value) {
  let parsed;
  try {
    parsed = JSON.parse(value || "[]");
  } catch (error) {
    throw new ExampleError("NETLD_SEARCH_QUERIES must be a JSON array of strings.", { cause: error });
  }
  if (!Array.isArray(parsed) || parsed.some((item) => typeof item !== "string" || !item.trim())) {
    throw new ExampleError("NETLD_SEARCH_QUERIES must be a JSON array of non-empty strings.");
  }
  const queries = parsed.map((item) => item.trim());
  if (queries.some((item) => /^(?:start|end)=/i.test(item))) {
    throw new ExampleError("NETLD_SEARCH_QUERIES must not contain start or end; the exporter controls its time window.");
  }
  return queries;
}

const resolvePath = (base, value) => path.isAbsolute(value) ? value : path.join(base, value);
const isoUtc = (milliseconds) => new Date(Number(milliseconds)).toISOString().replace(/\.\d{3}Z$/, "Z");

function positiveInteger(value, name) {
  const result = Number(value);
  if (!Number.isInteger(result) || result <= 0) throw new ExampleError(`${name} must be a positive integer.`);
  return result;
}

export function configFromEnv(base) {
  for (const name of ["NETLD_BASE_URL", "NETLD_API_KEY"]) {
    if (!process.env[name]?.trim()) throw new ExampleError(`Set ${name} in the environment file.`);
  }
  const outputFormat = (process.env.NETLD_OUTPUT_FORMAT || "csv").trim().toLowerCase();
  if (!["csv", "json"].includes(outputFormat)) throw new ExampleError("NETLD_OUTPUT_FORMAT must be csv or json.");
  return {
    baseUrl: process.env.NETLD_BASE_URL.trim().replace(/\/$/, ""),
    apiKey: process.env.NETLD_API_KEY.trim(),
    outputDir: resolvePath(base, process.env.NETLD_OUTPUT_DIR || "violation-exports"),
    outputFormat,
    statePath: resolvePath(base, process.env.NETLD_STATE_FILE || "violation-export-state.json"),
    reportPath: resolvePath(base, process.env.NETLD_RUN_REPORT_FILE || "violation-export-run.json"),
    pageSize: positiveInteger(process.env.NETLD_PAGE_SIZE || "100", "NETLD_PAGE_SIZE"),
    initialLookbackHours: positiveInteger(
      process.env.NETLD_INITIAL_LOOKBACK_HOURS || "24",
      "NETLD_INITIAL_LOOKBACK_HOURS",
    ),
    searchQueries: parseQueries(process.env.NETLD_SEARCH_QUERIES || "[]"),
  };
}

export class ThirdEyeClient {
  constructor(config) {
    this.config = config;
    this.cookie = "";
  }

  async request(endpoint, options = {}) {
    const headers = {
      Authorization: `Bearer ${this.config.apiKey}`,
      ...(this.cookie ? { Cookie: this.cookie } : {}),
      ...(options.headers || {}),
    };
    const response = await fetch(`${this.config.baseUrl}${endpoint}`, {
      ...options,
      headers,
      redirect: "manual",
      signal: AbortSignal.timeout(30000),
    });
    const cookie = response.headers.get("set-cookie");
    if (cookie) this.cookie = cookie.split(";", 1)[0];
    if (response.status >= 300 && response.status < 400) {
      throw new ExampleError(`Request redirected to ${response.headers.get("location") || ""}.`);
    }
    if (!response.ok) throw new ExampleError(`Request failed with HTTP ${response.status}.`);
    return response;
  }

  async login() {
    await this.request("/rest");
  }

  async searchPage(queries, offset, pageSize) {
    const response = await this.request("/rest", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        jsonrpc: "2.0",
        method: "Incidents.searchTriggerEvents",
        params: {
          pageData: { offset, total: 0, pageSize, violations: [] },
          queries,
          sortColumn: "updated",
          descending: true,
        },
        id: crypto.randomUUID(),
      }),
    });
    const data = await response.json();
    if (data.error) throw new ExampleError(`Incidents.searchTriggerEvents failed: ${JSON.stringify(data.error)}`);
    if (!data.result || typeof data.result !== "object" || !Array.isArray(data.result.violations)) {
      throw new ExampleError("Incidents.searchTriggerEvents returned invalid page data.");
    }
    return data.result;
  }
}

function numericField(event, field) {
  const value = Number(event?.[field]);
  if (!Number.isInteger(value)) {
    throw new ExampleError(`Incidents.searchTriggerEvents returned an invalid ${field}.`);
  }
  return value;
}

const eventId = (event) => numericField(event, "eventId");
const eventUpdated = (event) => numericField(event, "updated");

function loadState(file) {
  if (!fs.existsSync(file)) return { format: STATE_FORMAT, formatVersion: FORMAT_VERSION };
  const state = JSON.parse(fs.readFileSync(file, "utf8"));
  if (state.format !== STATE_FORMAT || state.formatVersion !== FORMAT_VERSION) {
    throw new ExampleError("The violation-export state file has an unsupported format.");
  }
  return state;
}

function atomicWrite(file, content) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  const temporary = path.join(path.dirname(file), `.${path.basename(file)}.${crypto.randomUUID()}.tmp`);
  try {
    fs.writeFileSync(temporary, content, { mode: 0o600 });
    fs.renameSync(temporary, file);
  } catch (error) {
    try { fs.unlinkSync(temporary); } catch {}
    throw error;
  }
}

const writeJson = (file, value) => atomicWrite(file, `${JSON.stringify(value, null, 2)}\n`);

export function buildQueries(config, state, nowMs) {
  const start = state.lastUpdated == null
    ? nowMs - config.initialLookbackHours * 60 * 60 * 1000
    : Number(state.lastUpdated);
  return [...config.searchQueries, `start=${isoUtc(start)}`, `end=${isoUtc(nowMs)}`];
}

export async function collectEvents(client, queries, pageSize) {
  let offset = 0;
  let total = null;
  let pages = 0;
  const events = [];
  while (total == null || offset < total) {
    const page = await client.searchPage(queries, offset, pageSize);
    const batch = page.violations;
    const pageOffset = Number(page.offset ?? offset);
    const pageTotal = Number(page.total ?? pageOffset + batch.length);
    total = total == null ? pageTotal : Math.max(total, pageTotal);
    pages += 1;
    for (const event of batch) {
      if (!event || typeof event !== "object" || Array.isArray(event)) {
        throw new ExampleError("Incidents.searchTriggerEvents returned a non-object violation.");
      }
      eventId(event);
      eventUpdated(event);
      events.push(event);
    }
    const nextOffset = pageOffset + batch.length;
    if (nextOffset >= total) break;
    if (!batch.length || nextOffset <= offset) {
      throw new ExampleError("Violation paging stopped before all reported results were returned.");
    }
    offset = nextOffset;
  }
  const unique = new Map(events.map((event) => [`${eventUpdated(event)}:${eventId(event)}`, event]));
  return {
    events: [...unique.values()].sort((left, right) => eventUpdated(left) - eventUpdated(right) || eventId(left) - eventId(right)),
    pageCount: pages,
  };
}

export function selectEvents(events, state) {
  if (state.lastUpdated == null) return events;
  const watermark = Number(state.lastUpdated);
  const ids = new Set((state.eventIdsAtLastUpdated || []).map(Number));
  return events.filter((event) => eventUpdated(event) > watermark
    || (eventUpdated(event) === watermark && !ids.has(eventId(event))));
}

function csvCell(value) {
  const text = value == null ? "" : String(value);
  return /[",\r\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}

export function renderExport(events, outputFormat) {
  if (outputFormat === "json") return `${JSON.stringify(events, null, 2)}\n`;
  const rows = [CSV_FIELDS.join(",")];
  for (const event of events) {
    rows.push(CSV_FIELDS.map((field) => {
      const value = ["created", "updated"].includes(field) && event[field] != null
        ? isoUtc(event[field])
        : event[field];
      return csvCell(value);
    }).join(","));
  }
  return `${rows.join("\n")}\n`;
}

function advanceState(state, events) {
  if (!events.length) return;
  const newest = Math.max(...events.map(eventUpdated));
  const ids = events.filter((event) => eventUpdated(event) === newest).map(eventId);
  if (state.lastUpdated != null && Number(state.lastUpdated) === newest) {
    ids.push(...(state.eventIdsAtLastUpdated || []).map(Number));
  }
  state.lastUpdated = newest;
  state.eventIdsAtLastUpdated = [...new Set(ids)].sort((left, right) => left - right);
}

export async function exportViolations(client, config, nowMs, timestamp = isoUtc(nowMs)) {
  const state = loadState(config.statePath);
  const queries = buildQueries(config, state, nowMs);
  const { events, pageCount } = await collectEvents(client, queries, config.pageSize);
  const selected = selectEvents(events, state);
  let outputFile = null;
  if (selected.length) {
    const stamp = isoUtc(nowMs).replace(/[-:]/g, "");
    outputFile = path.join(config.outputDir, `violations-${stamp}.${config.outputFormat}`);
    atomicWrite(outputFile, renderExport(selected, config.outputFormat));
    advanceState(state, selected);
  }
  const report = {
    format: RUN_FORMAT,
    formatVersion: FORMAT_VERSION,
    generatedAt: timestamp,
    queries,
    pageCount,
    resultCount: events.length,
    exportedCount: selected.length,
    outputFormat: config.outputFormat,
    outputFile,
  };
  writeJson(config.statePath, state);
  writeJson(config.reportPath, report);
  return report;
}

async function main() {
  const here = path.dirname(fileURLToPath(import.meta.url));
  const index = process.argv.indexOf("--env");
  const envFile = index >= 0 ? process.argv[index + 1] : path.join(here, ".env");
  if (index >= 0 && !envFile) throw new ExampleError("--env requires a file path.");
  loadEnv(envFile);
  const config = configFromEnv(here);
  const client = new ThirdEyeClient(config);
  await client.login();
  const report = await exportViolations(client, config, Date.now());
  console.log(`Found ${report.resultCount} violations and exported ${report.exportedCount}.`);
  console.log(`Run report: ${config.reportPath}`);
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main().catch((error) => {
    console.error(`Error: ${error.message}`);
    process.exitCode = 1;
  });
}
