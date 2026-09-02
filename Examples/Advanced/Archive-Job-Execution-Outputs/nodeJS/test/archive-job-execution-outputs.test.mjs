import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";

import { archiveJobExecutionOutputs } from "../archive-job-execution-outputs.mjs";

const execution = (id, endTime, jobType = "Script Tool Job") => ({
  id,
  endTime,
  startTime: endTime - 100,
  jobName: `Job ${id}`,
  jobType,
});

class FakeClient {
  constructor(records, failDetail = null) {
    this.records = records;
    this.failDetail = failDetail;
    this.offsets = [];
  }
  async searchExecutionPage(offset, pageSize) {
    this.offsets.push(offset);
    return {
      offset,
      pageSize,
      total: offset === 0 ? this.records.length : 0,
      executionData: this.records.slice(offset, offset + pageSize),
    };
  }
  async executionDetails(executionId) {
    return [{ id: executionId * 10, managedNetwork: "Default", ipAddress: "192.0.2.10" }];
  }
  async downloadDetail(executionId, detailId) {
    if (detailId === this.failDetail) throw new Error("download failed");
    return Buffer.from(`output ${executionId}`);
  }
}

function config(base, initialMode = "all") {
  return {
    outputDir: path.join(base, "outputs"),
    statePath: path.join(base, "state.json"),
    reportPath: path.join(base, "report.json"),
    pageSize: 2,
    initialMode,
    jobType: "Script Tool Job",
    jobName: "",
  };
}

test("all mode pages and archives only Script Tool Jobs", async (context) => {
  const base = fs.mkdtempSync(path.join(os.tmpdir(), "netld-job-output-"));
  context.after(() => fs.rmSync(base, { recursive: true, force: true }));
  const client = new FakeClient([
    execution(3, 3000), execution(2, 2000, "Report Job"), execution(1, 1000),
  ]);

  const report = await archiveJobExecutionOutputs(client, config(base), "2026-09-02T00:00:00Z");

  assert.deepEqual(client.offsets, [0, 2]);
  assert.equal(report.archivedCount, 2);
  assert.equal(report.outputCount, 2);
  assert.equal(JSON.parse(fs.readFileSync(path.join(base, "state.json"))).lastEndTime, 3000);
});

test("latest mode baselines then archives a new execution", async (context) => {
  const base = fs.mkdtempSync(path.join(os.tmpdir(), "netld-job-output-"));
  context.after(() => fs.rmSync(base, { recursive: true, force: true }));
  const settings = config(base, "latest");

  const first = await archiveJobExecutionOutputs(
    new FakeClient([execution(2, 2000), execution(1, 1000)]), settings,
  );
  const second = await archiveJobExecutionOutputs(
    new FakeClient([execution(3, 3000), execution(2, 2000), execution(1, 1000)]), settings,
  );

  assert.equal(first.initialBaseline, true);
  assert.equal(first.archivedCount, 0);
  assert.equal(second.archivedCount, 1);
});

test("a failed download does not advance state", async (context) => {
  const base = fs.mkdtempSync(path.join(os.tmpdir(), "netld-job-output-"));
  context.after(() => fs.rmSync(base, { recursive: true, force: true }));
  const settings = config(base, "latest");
  await archiveJobExecutionOutputs(new FakeClient([execution(1, 1000)]), settings);

  const report = await archiveJobExecutionOutputs(
    new FakeClient([execution(2, 2000), execution(1, 1000)], 20), settings,
  );

  assert.equal(report.failureCount, 1);
  assert.equal(JSON.parse(fs.readFileSync(path.join(base, "state.json"))).lastEndTime, 1000);
});
