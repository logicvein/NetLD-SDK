import assert from "node:assert/strict";
import { mkdtemp, readFile, rm } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import test from "node:test";

import { csvCell, exportInventory, parseNetworks } from "../export-device-inventory.mjs";

test("exports every inventory page", async () => {
  const offsets = [];
  const client = {
    async searchInventory(networks, scheme, query, offset) {
      offsets.push(offset);
      return {
        0: { offset: 0, pageSize: 2, total: 5, devices: [
          { network: "Default", ipAddress: "192.0.2.1", hostname: "core,one" },
          { network: "Lab", ipAddress: "192.0.2.2", memoSummary: "first\nsecond" },
        ] },
        2: { offset: 2, pageSize: 2, total: 0, devices: [
          { network: "Lab", ipAddress: "192.0.2.3" },
          { network: "Lab", ipAddress: "192.0.2.4" },
        ] },
        4: { offset: 4, pageSize: 2, total: 0, devices: [
          { network: "Lab", ipAddress: "192.0.2.5" },
        ] },
      }[offset];
    },
  };
  const directory = await mkdtemp(path.join(os.tmpdir(), "netld-inventory-"));
  try {
    const outputFile = path.join(directory, "inventory.csv");
    const count = await exportInventory(client, {
      networks: ["Default", "Lab"], scheme: "ipAddress", query: "", pageSize: 2, outputFile,
    });
    const csv = await readFile(outputFile, "utf8");
    assert.equal(count, 5);
    assert.deepEqual(offsets, [0, 2, 4]);
    assert.match(csv, /"core,one"/);
    assert.match(csv, /"first\nsecond"/);
    assert.match(csv, /Lab,192\.0\.2\.3/);
  } finally {
    await rm(directory, { recursive: true, force: true });
  }
});

test("quotes CSV metacharacters and parses network lists", () => {
  assert.equal(csvCell('a"b'), '"a""b"');
  assert.deepEqual(parseNetworks("Default, Lab"), ["Default", "Lab"]);
  assert.throws(() => parseNetworks(" , "), /at least one/);
});

test("JSON output is an array with native values and explicit nulls", async () => {
  const client = {
    async searchInventory() {
      return { pageSize: 1, total: 1, devices: [
        { network: "Default", ipAddress: "192.0.2.1", complianceState: 2 },
      ] };
    },
  };
  const directory = await mkdtemp(path.join(os.tmpdir(), "netld-inventory-"));
  try {
    const outputFile = path.join(directory, "inventory.json");
    const count = await exportInventory(client, {
      networks: ["Default"], scheme: "ipAddress", query: "", pageSize: 1, outputFile, format: "json",
    });
    const devices = JSON.parse(await readFile(outputFile, "utf8"));
    assert.equal(count, 1);
    assert.ok(Array.isArray(devices));
    assert.equal(devices[0].complianceState, 2);
    assert.equal(devices[0].hostname, null);
    assert.deepEqual(Object.keys(devices[0]), [
      "network", "ipAddress", "hostname", "adapterId", "deviceType",
      "hardwareVendor", "model", "serialNumber", "softwareVendor", "osVersion",
      "backupStatus", "complianceState", "lastBackup", "lastTelemetry", "memoSummary",
      "custom1", "custom2", "custom3", "custom4", "custom5",
    ]);
  } finally {
    await rm(directory, { recursive: true, force: true });
  }
});
