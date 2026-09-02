#!/usr/bin/env node

import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { randomUUID } from "node:crypto";
import { fileURLToPath, pathToFileURL } from "node:url";

export const STATE_FORMAT = "logicvein-netld-job-execution-output-state";
export const RUN_FORMAT = "logicvein-netld-job-execution-output-run";
export const FORMAT_VERSION = 1;

export class ExampleError extends Error {}

export function safeName(value, fallback) {
  return String(value).trim().replace(/[^A-Za-z0-9._-]+/g, "_").replace(/^[._]+|[._]+$/g, "") || fallback;
}

export function loadConfig(base = path.dirname(fileURLToPath(import.meta.url))) {
  const baseUrl = (process.env.NETLD_BASE_URL || "").trim();
  const apiKey = (process.env.NETLD_API_KEY || "").trim();
  if (!baseUrl || !apiKey) {
    throw new ExampleError("Set NETLD_BASE_URL and NETLD_API_KEY in the environment file.");
  }
  const pageSize = Number.parseInt(process.env.NETLD_PAGE_SIZE || "100", 10);
  if (!Number.isInteger(pageSize) || pageSize <= 0) {
    throw new ExampleError("NETLD_PAGE_SIZE must be a positive integer.");
  }
  const initialMode = (process.env.NETLD_INITIAL_MODE || "latest").trim().toLowerCase();
  if (!new Set(["latest", "all"]).has(initialMode)) {
    throw new ExampleError("NETLD_INITIAL_MODE must be latest or all.");
  }
  const destination = (name, fallback) => {
    const value = process.env[name] || fallback;
    return path.isAbsolute(value) ? value : path.join(base, value);
  };
  return {
    baseUrl: baseUrl.replace(/\/$/, ""),
    apiKey,
    outputDir: destination("NETLD_OUTPUT_DIR", "job-execution-outputs"),
    statePath: destination("NETLD_STATE_FILE", "job-execution-output-state.json"),
    reportPath: destination("NETLD_RUN_REPORT_FILE", "job-execution-output-run.json"),
    pageSize,
    initialMode,
    searchScheme: (process.env.NETLD_SEARCH_SCHEME || "").trim(),
    searchData: (process.env.NETLD_SEARCH_DATA || "").trim(),
    jobType: (process.env.NETLD_JOB_TYPE ?? "Script Tool Job").trim(),
    jobName: (process.env.NETLD_JOB_NAME || "").trim(),
  };
}

export class NetLDClient {
  constructor(config, fetchImpl = fetch, timeout = 30000) {
    this.config = config;
    this.fetch = fetchImpl;
    this.timeout = timeout;
    this.cookie = "";
  }

  async request(endpoint, options = {}) {
    const headers = {
      Authorization: `Bearer ${this.config.apiKey}`,
      ...(this.cookie ? { Cookie: this.cookie } : {}),
      ...(options.headers || {}),
    };
    let response;
    try {
      response = await this.fetch(`${this.config.baseUrl}${endpoint}`, {
        ...options,
        headers,
        redirect: "manual",
        signal: AbortSignal.timeout(this.timeout),
      });
    } catch {
      throw new ExampleError(`Could not reach ${this.config.baseUrl}.`);
    }
    const setCookie = response.headers.get("set-cookie");
    if (setCookie) this.cookie = setCookie.split(";", 1)[0];
    if (response.status >= 300 && response.status < 400) {
      throw new ExampleError(`Request redirected to ${response.headers.get("location") || ""}.`);
    }
    if (!response.ok) throw new ExampleError(`Request failed with HTTP ${response.status}.`);
    return response;
  }

  async login() {
    await this.request("/rest");
  }

  async call(method, params) {
    const response = await this.request("/rest", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ jsonrpc: "2.0", method, params, id: randomUUID() }),
    });
    let data;
    try {
      data = await response.json();
    } catch {
      throw new ExampleError(`${method} returned invalid JSON.`);
    }
    if (data.error) throw new ExampleError(`${method} failed: ${JSON.stringify(data.error)}`);
    return data.result;
  }

  async searchExecutionPage(offset, pageSize) {
    const result = await this.call("Scheduler.searchExecutions", {
      scheme: this.config.searchScheme,
      data: this.config.searchData,
      pageData: { offset, executionData: [], pageSize, total: 0 },
      sortColumn: "endTime",
      descending: true,
    });
    if (!result || !Array.isArray(result.executionData)) {
      throw new ExampleError("Scheduler.searchExecutions returned an invalid page.");
    }
    return result;
  }

  async executionDetails(executionId) {
    const result = await this.call("Plugins.getExecutionDetails", { executionId });
    if (result == null) return [];
    if (!Array.isArray(result)) {
      throw new ExampleError("Plugins.getExecutionDetails returned an invalid collection.");
    }
    return result;
  }

  async downloadDetail(executionId, recordId) {
    const query = new URLSearchParams({ executionId: String(executionId), recordId: String(recordId) });
    return Buffer.from(await (await this.request(`/servlet/pluginDetail?${query}`)).arrayBuffer());
  }
}

export function loadState(statePath) {
  if (!fs.existsSync(statePath)) return { format: STATE_FORMAT, formatVersion: FORMAT_VERSION };
  let state;
  try {
    state = JSON.parse(fs.readFileSync(statePath, "utf8"));
  } catch (error) {
    throw new ExampleError(`Could not read archive state: ${statePath}`);
  }
  if (state.format !== STATE_FORMAT || state.formatVersion !== FORMAT_VERSION) {
    throw new ExampleError("The job-execution state file has an unsupported format.");
  }
  return state;
}

export function writeAtomic(destination, content) {
  fs.mkdirSync(path.dirname(destination), { recursive: true });
  const temporary = `${destination}.${process.pid}.${randomUUID()}.tmp`;
  try {
    fs.writeFileSync(temporary, content);
    fs.renameSync(temporary, destination);
  } finally {
    if (fs.existsSync(temporary)) fs.unlinkSync(temporary);
  }
}

export function writeJson(destination, value) {
  writeAtomic(destination, JSON.stringify(value, null, 2) + "\n");
}

function executionEnd(execution) {
  return execution.endTime == null ? null : Number(execution.endTime);
}

function executionId(execution) {
  const value = execution.id ?? execution.executionId;
  if (value == null) throw new ExampleError("Scheduler.searchExecutions returned a record without an execution ID.");
  return Number(value);
}

function eligible(config, execution) {
  return (!config.jobType || execution.jobType === config.jobType) &&
    (!config.jobName || execution.jobName === config.jobName);
}

export async function collectExecutions(client, config, state) {
  const watermark = state.lastEndTime == null ? null : Number(state.lastEndTime);
  const watermarkIds = new Set((state.executionIdsAtLastEndTime || []).map(Number));
  const observed = [];
  let offset = 0;
  let reportedTotal = null;

  while (reportedTotal === null || offset < reportedTotal) {
    const page = await client.searchExecutionPage(offset, config.pageSize);
    const batch = page.executionData;
    const pageOffset = Number(page.offset ?? offset);
    const pageTotal = Number(page.total ?? pageOffset + batch.length);
    reportedTotal = reportedTotal === null ? pageTotal : Math.max(reportedTotal, pageTotal);
    let passedWatermark = false;
    for (const execution of batch) {
      const endTime = executionEnd(execution);
      if (endTime === null) continue;
      if (watermark !== null && endTime < watermark) {
        passedWatermark = true;
        break;
      }
      observed.push(execution);
    }
    if (passedWatermark || (watermark === null && config.initialMode === "latest")) break;
    const nextOffset = pageOffset + batch.length;
    if (nextOffset >= reportedTotal) break;
    if (!batch.length || nextOffset <= offset) {
      throw new ExampleError("Execution paging stopped before all results were returned.");
    }
    offset = nextOffset;
  }

  if (watermark === null && config.initialMode === "latest") return { observed, candidates: [] };
  const candidates = observed.filter((execution) => {
    const endTime = executionEnd(execution);
    const isNew = endTime !== null && (
      watermark === null || endTime > watermark ||
      (endTime === watermark && !watermarkIds.has(executionId(execution)))
    );
    return isNew && eligible(config, execution);
  }).sort((left, right) => executionEnd(left) - executionEnd(right) || executionId(left) - executionId(right));
  return { observed, candidates };
}

export async function archiveExecution(client, config, execution) {
  const id = executionId(execution);
  const endTime = executionEnd(execution);
  if (endTime === null) throw new ExampleError(`Execution ${id} has not completed.`);
  const date = new Date(endTime).toISOString().slice(0, 10);
  const directory = path.join(config.outputDir, date, `${id}_${safeName(execution.jobName || "job", "job")}`);
  const details = await client.executionDetails(id);
  const outputs = [];
  for (const detail of details) {
    const detailId = Number(detail.id);
    const identity = safeName(`${detail.managedNetwork || "network"}_${detail.ipAddress || "device"}`, "device");
    const contentPath = path.join(directory, `${detailId}_${identity}.log`);
    const metadataPath = path.join(directory, `${detailId}_${identity}.metadata.json`);
    const content = await client.downloadDetail(id, detailId);
    writeAtomic(contentPath, content);
    writeJson(metadataPath, { executionId: id, detail, contentFile: path.basename(contentPath) });
    outputs.push({
      detailId,
      bytes: content.length,
      contentFile: path.relative(config.outputDir, contentPath),
      metadataFile: path.relative(config.outputDir, metadataPath),
    });
  }
  const metadataPath = path.join(directory, "execution.metadata.json");
  writeJson(metadataPath, { execution, outputCount: outputs.length });
  return {
    executionId: id,
    endTime,
    jobName: execution.jobName,
    outputCount: outputs.length,
    metadataFile: path.relative(config.outputDir, metadataPath),
    outputs,
  };
}

function advanceState(state, observed) {
  const completed = observed.filter((execution) => executionEnd(execution) !== null);
  if (!completed.length) return;
  const newest = Math.max(...completed.map(executionEnd));
  const ids = new Set(completed.filter((execution) => executionEnd(execution) === newest).map(executionId));
  if (state.lastEndTime != null && Number(state.lastEndTime) === newest) {
    for (const id of state.executionIdsAtLastEndTime || []) ids.add(Number(id));
  }
  state.lastEndTime = newest;
  state.executionIdsAtLastEndTime = [...ids].sort((left, right) => left - right);
}

export async function archiveJobExecutionOutputs(client, config, timestamp = new Date().toISOString()) {
  const state = loadState(config.statePath);
  const initialBaseline = state.lastEndTime == null && config.initialMode === "latest";
  const { observed, candidates } = await collectExecutions(client, config, state);
  const archived = [];
  const failures = [];
  for (const execution of candidates) {
    try {
      archived.push(await archiveExecution(client, config, execution));
    } catch (error) {
      failures.push({ executionId: execution.id, error: error.message });
    }
  }
  if (!failures.length) advanceState(state, observed);
  const report = {
    format: RUN_FORMAT,
    formatVersion: FORMAT_VERSION,
    generatedAt: timestamp,
    initialBaseline,
    observedCount: observed.length,
    candidateCount: candidates.length,
    archivedCount: archived.length,
    outputCount: archived.reduce((sum, item) => sum + item.outputCount, 0),
    failureCount: failures.length,
    archived,
    failures,
  };
  writeJson(config.statePath, state);
  writeJson(config.reportPath, report);
  return report;
}

export async function main() {
  try {
    const config = loadConfig();
    const client = new NetLDClient(config);
    await client.login();
    const report = await archiveJobExecutionOutputs(client, config);
    if (report.initialBaseline) console.log("Recorded the latest completed execution as the initial baseline.");
    console.log(
      `Archived ${report.archivedCount} executions and ${report.outputCount} outputs; ` +
      `recorded ${report.failureCount} failures in ${config.reportPath}`,
    );
    return report.failureCount ? 2 : 0;
  } catch (error) {
    console.error(`Error: ${error.message}`);
    return 1;
  }
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  process.exitCode = await main();
}
