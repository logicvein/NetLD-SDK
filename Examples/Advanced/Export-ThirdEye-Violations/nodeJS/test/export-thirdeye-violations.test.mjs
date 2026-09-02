import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";

import { ExampleError, exportViolations, parseQueries } from "../export-thirdeye-violations.mjs";

const event = (eventId, updated) => ({
  eventId,
  incidentId: 1,
  severity: "ERROR",
  clearState: "ACTIVE",
  eventType: "THRESHOLD",
  network: "Default",
  ipAddress: "192.0.2.1",
  hostname: "router",
  deviceId: 7,
  hostUuid: "host-7",
  measurement: "CPU",
  measurementIndex: null,
  message: "Test, with comma",
  occurrences: 1,
  triggerId: "trigger-1",
  created: updated - 1000,
  updated,
});

class FakeClient {
  constructor(pages) { this.pages = pages; }
  async searchPage(_queries, offset) { return this.pages[offset]; }
}

function config(base, outputFormat = "csv") {
  return {
    baseUrl: "https://example",
    apiKey: "key",
    outputDir: path.join(base, "output"),
    outputFormat,
    statePath: path.join(base, "state.json"),
    reportPath: path.join(base, "run.json"),
    pageSize: 2,
    initialLookbackHours: 24,
    searchQueries: ["incidentId=1"],
  };
}

test("pages CSV and uses event IDs to break watermark ties", async (context) => {
  const base = fs.mkdtempSync(path.join(os.tmpdir(), "violations-node-"));
  context.after(() => fs.rmSync(base, { recursive: true, force: true }));
  const cfg = config(base);
  const pages = {
    0: { offset: 0, pageSize: 2, total: 3, violations: [event(3, 3000), event(2, 2000)] },
    2: { offset: 2, pageSize: 2, total: 0, violations: [event(1, 2000)] },
  };
  const first = await exportViolations(new FakeClient(pages), cfg, 4000, "1970-01-01T00:00:04Z");
  const csv = fs.readFileSync(first.outputFile, "utf8");
  const state = JSON.parse(fs.readFileSync(cfg.statePath, "utf8"));
  const secondPages = {
    0: { offset: 0, pageSize: 2, total: 2, violations: [event(4, 3000), event(3, 3000)] },
  };
  const second = await exportViolations(new FakeClient(secondPages), cfg, 5000, "1970-01-01T00:00:05Z");
  assert.equal(first.pageCount, 2);
  assert.equal(first.exportedCount, 3);
  assert.match(csv, /"Test, with comma"/);
  assert.equal(state.lastUpdated, 3000);
  assert.equal(second.exportedCount, 1);
});

test("JSON preserves API values", async (context) => {
  const base = fs.mkdtempSync(path.join(os.tmpdir(), "violations-node-"));
  context.after(() => fs.rmSync(base, { recursive: true, force: true }));
  const cfg = config(base, "json");
  const pages = { 0: { offset: 0, pageSize: 2, total: 1, violations: [event(1, 2000)] } };
  const report = await exportViolations(new FakeClient(pages), cfg, 3000);
  const result = JSON.parse(fs.readFileSync(report.outputFile, "utf8"));
  assert.equal(result[0].updated, 2000);
  assert.equal(result[0].measurementIndex, null);
});

test("query validation reserves the incremental window", () => {
  assert.deepEqual(parseQueries('["incidentId=1"]'), ["incidentId=1"]);
  assert.throws(() => parseQueries('["end=2026-01-01T00:00:00Z"]'), ExampleError);
});
