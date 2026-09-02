import assert from "node:assert/strict";
import { mkdtemp, readFile, rm } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import test from "node:test";

import { exportInterfaces, flattenIpAddresses } from "../export-device-interfaces.mjs";

test("exports multiple pages while preserving per-device failures", async () => {
  const offsets = [];
  const client = {
    async searchInventory(networks, scheme, query, offset) {
      offsets.push(offset);
      return {
        0: { pageSize: 2, total: 3, devices: [
          { network: "Default", ipAddress: "192.0.2.1", hostname: "one" },
          { network: "Lab", ipAddress: "192.0.2.2", hostname: "two" },
        ] },
        2: { pageSize: 2, total: 0, devices: [
          { network: "Lab", ipAddress: "192.0.2.3", hostname: "three" },
        ] },
      }[offset];
    },
    async getDeviceInterfaces(network, ipAddress) {
      if (ipAddress === "192.0.2.2") throw new Error("simulated lookup failure");
      if (ipAddress === "192.0.2.3") return [];
      return [{ id: 7, index: 1, name: "Ethernet1", adminUp: true, ipAddresses: [
        { ipAddress: "192.0.2.10", cidrPrefix: 24 }, { ipAddress: "2001:db8::10", cidrPrefix: 64 },
      ] }];
    },
  };
  const directory = await mkdtemp(path.join(os.tmpdir(), "netld-interfaces-"));
  try {
    const config = {
      networks: ["Default", "Lab"], scheme: "ipAddress", query: "", pageSize: 2,
      outputFile: path.join(directory, "interfaces.csv"), failureFile: path.join(directory, "failures.csv"),
    };
    const result = await exportInterfaces(client, config);
    const output = await readFile(config.outputFile, "utf8");
    const failures = await readFile(config.failureFile, "utf8");
    assert.deepEqual(result, { deviceCount: 3, interfaceCount: 1, failureCount: 1 });
    assert.deepEqual(offsets, [0, 2]);
    assert.match(output, /192\.0\.2\.10\/24;2001:db8::10\/64/);
    assert.match(failures, /192\.0\.2\.2/);
  } finally {
    await rm(directory, { recursive: true, force: true });
  }
});

test("flattens an empty address collection", () => {
  assert.equal(flattenIpAddresses({ ipAddresses: [] }), "");
});
