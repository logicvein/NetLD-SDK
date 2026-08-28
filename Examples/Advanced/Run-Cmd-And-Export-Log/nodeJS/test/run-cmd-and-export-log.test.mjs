import assert from "node:assert/strict";
import test from "node:test";

import { buildJob, safeFilename } from "../run-cmd-and-export-log.mjs";

test("builds a guarded command-runner job", () => {
  const job = buildJob("Lab", "192.0.2.10", ["show version", "show clock"]);
  assert.deepEqual(job.managedNetworks, ["Lab"]);
  assert.equal(job.jobType, "Script Tool Job");
  assert.equal(job.jobParameters.ipResolutionScheme, "ipCsv");
  assert.equal(job.jobParameters.ipResolutionData, '"192.0.2.10@Lab"');
  assert.equal(job.jobParameters["input.commandList"], "show version\nshow clock");
  assert.equal(job.jobParameters.backupOnCompletion, "false");
});

test("rejects an empty command list", () => {
  assert.throws(() => buildJob("Lab", "192.0.2.10", []), /no commands/);
});

test("sanitizes log filenames", () => {
  assert.equal(safeFilename("Lab / 192.0.2.10"), "Lab_192.0.2.10");
});

