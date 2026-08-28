import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import { archiveConfigurationRevisions } from "../archive-configuration-revisions.mjs";

const item = (pathName, timestamp) => ({ managedNetwork: "Default", ipAddress: "192.0.2.1", path: pathName, lastChanged: timestamp, mimeType: "text/plain", size: 4 });
class FakeClient {
  constructor(failPath = null) { this.failPath = failPath; }
  async searchInventory() { return { pageSize: 10, total: 1, devices: [{ network: "Default", ipAddress: "192.0.2.1" }] }; }
  async configurationHistory() { return { pageSize: 10, total: 3, configHistoryItems: [item("/running-config", 300), item("/startup-config", 200), item("/running-config", 100)] }; }
  async retrieveRevision(value) { if (value.path === this.failPath) throw new Error("simulated revision failure"); return { path: value.path, lastChanged: value.lastChanged, mimeType: "text/plain", size: 4, content: Buffer.from("test").toString("base64") }; }
}
const config = (base, initialMode = "latest") => ({ networks: ["Default"], archiveDir: path.join(base, "archive"), statePath: path.join(base, "state.json"), runReportPath: path.join(base, "run.json"), inventoryPageSize: 10, historyPageSize: 10, searchScheme: "ipAddress", searchQuery: "", initialMode });

test("latest baseline then incremental no-op", async t => { const base = fs.mkdtempSync(path.join(os.tmpdir(), "netld-node-")); t.after(() => fs.rmSync(base, { recursive: true })); const cfg = config(base);
  assert.equal((await archiveConfigurationRevisions(new FakeClient(), cfg, "2026-08-28T12:00:00Z")).archivedCount, 2);
  assert.equal((await archiveConfigurationRevisions(new FakeClient(), cfg, "2026-08-28T12:01:00Z")).archivedCount, 0);
  assert.equal(JSON.parse(fs.readFileSync(cfg.statePath)).devices["Default@192.0.2.1"].lastChanged, 300);
});
test("failure does not advance state", async t => { const base = fs.mkdtempSync(path.join(os.tmpdir(), "netld-node-")); t.after(() => fs.rmSync(base, { recursive: true })); const cfg = config(base);
  assert.equal((await archiveConfigurationRevisions(new FakeClient("/startup-config"), cfg)).failureCount, 1); assert.equal(JSON.parse(fs.readFileSync(cfg.statePath)).devices["Default@192.0.2.1"], undefined);
});
test("all mode archives every revision", async t => { const base = fs.mkdtempSync(path.join(os.tmpdir(), "netld-node-")); t.after(() => fs.rmSync(base, { recursive: true })); assert.equal((await archiveConfigurationRevisions(new FakeClient(), config(base, "all"))).archivedCount, 3); });
