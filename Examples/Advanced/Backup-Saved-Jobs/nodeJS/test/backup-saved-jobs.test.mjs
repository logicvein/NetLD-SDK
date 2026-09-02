import assert from "node:assert/strict";
import { mkdtemp, readFile, rm } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import test from "node:test";

import { backupSavedJobs } from "../backup-saved-jobs.mjs";

test("creates a sorted versioned backup across pages and records failures", async () => {
  const offsets = [];
  const client = {
    async searchJobs(networks, offset) {
      offsets.push(offset);
      return {
        0: { pageSize: 2, total: 3, jobData: [{ jobId: 3, jobName: "Three" }, { jobId: 1, jobName: "One" }] },
        2: { pageSize: 2, total: 0, jobData: [{ jobId: 2, jobName: "Two" }] },
      }[offset];
    },
    async getJob(jobId) {
      if (jobId === 2) throw new Error("simulated retrieval failure");
      return { jobId, jobName: String(jobId), jobParameters: { z: "last", a: "first" } };
    },
  };
  const directory = await mkdtemp(path.join(os.tmpdir(), "netld-jobs-"));
  try {
    const config = {
      networks: ["Lab", "Default"], pageSize: 2,
      outputFile: path.join(directory, "jobs.json"), failureFile: path.join(directory, "failures.json"),
    };
    const result = await backupSavedJobs(client, config, "2026-08-28T12:00:00Z");
    const backup = JSON.parse(await readFile(config.outputFile, "utf8"));
    const failures = JSON.parse(await readFile(config.failureFile, "utf8"));
    assert.deepEqual(result, { jobCount: 2, failureCount: 1 });
    assert.deepEqual(offsets, [0, 2]);
    assert.deepEqual(backup.jobs.map((job) => job.jobId), [1, 3]);
    assert.deepEqual(backup.networks, ["Default", "Lab"]);
    assert.equal(backup.complete, false);
    assert.equal(failures.failures[0].jobId, 2);
  } finally { await rm(directory, { recursive: true, force: true }); }
});

test("deduplicates a repeated job ID", async () => {
  const requested = [];
  const client = {
    async searchJobs() { return { pageSize: 2, total: 2, jobData: [{ jobId: 1 }, { jobId: 1 }] }; },
    async getJob(jobId) { requested.push(jobId); return { jobId }; },
  };
  const directory = await mkdtemp(path.join(os.tmpdir(), "netld-jobs-"));
  try {
    await backupSavedJobs(client, {
      networks: ["Default"], pageSize: 2,
      outputFile: path.join(directory, "jobs.json"), failureFile: path.join(directory, "failures.json"),
    }, "2026-08-28T12:00:00Z");
    assert.deepEqual(requested, [1]);
  } finally { await rm(directory, { recursive: true, force: true }); }
});
