import assert from "node:assert/strict";
import test from "node:test";

import {
  BridgeError,
  LiveNXClient,
  NetLDClient,
  parseLiveNXDeviceIps,
  prepareDiscoveryJob,
} from "../live-nx-to-thirdeye.mjs";


test("parses and normalizes valid vendor device addresses", () => {
  const csv =
    "\ufeffIP ADDRESS,VENDOR,NAME\n" +
    "192.0.2.10,Cisco,router-1\n" +
    "2001:0db8::1,Juniper,router-2\n" +
    "not-an-address,Cisco,bad-row\n" +
    "192.0.2.20,,vendorless\n";

  assert.deepEqual(
    [...parseLiveNXDeviceIps(csv)],
    ["192.0.2.10", "2001:db8::1"],
  );
});


test("can include vendorless devices", () => {
  const csv = "Management IP,Name\n192.0.2.20,router-1\n";
  assert.deepEqual(
    [...parseLiveNXDeviceIps(csv, { requireVendor: false })],
    ["192.0.2.20"],
  );
});


test("rejects an unknown CSV shape", () => {
  assert.throws(
    () => parseLiveNXDeviceIps("HOSTNAME,VENDOR\nrouter-1,Cisco\n"),
    BridgeError,
  );
});


test("prepares a copy of a compatible discovery job", () => {
  const source = {
    managedNetwork: "Old",
    jobParameters: {
      managedNetwork: "Old",
      includedAddresses: "192.0.2.1",
    },
  };
  const prepared = prepareDiscoveryJob(
    source,
    "Default",
    new Set(["2001:db8::1", "192.0.2.20"]),
  );

  assert.equal(source.managedNetwork, "Old");
  assert.equal(prepared.managedNetwork, "Default");
  assert.equal(prepared.jobParameters.managedNetwork, "Default");
  assert.equal(prepared.jobParameters.includedAddresses, "192.0.2.20,2001:db8::1");
});


test("rejects a non-discovery job", () => {
  assert.throws(
    () => prepareDiscoveryJob({ jobParameters: {} }, "Default", new Set(["192.0.2.1"])),
    BridgeError,
  );
});


test("sends the LiveNX token in a header and requests no redirects", async () => {
  let request;
  const fetchFunction = async (url, options) => {
    request = { url, options };
    return new Response("IP ADDRESS,VENDOR\n192.0.2.10,Cisco\n");
  };
  const client = new LiveNXClient(
    "https://livenx.example.com:8093",
    "secret-token",
    "/v1/devices/export/csv",
    30000,
    fetchFunction,
  );

  await client.exportDevicesCsv();

  assert.equal(request.url.includes("secret-token"), false);
  assert.equal(request.options.headers.Authorization, "Bearer secret-token");
  assert.equal(request.options.redirect, "manual");
});


test("reads every ThirdEye inventory page", async () => {
  const client = new NetLDClient("https://thirdeye.example.com", "key");
  const offsets = [];
  client.call = async (_method, params) => {
    offsets.push(params.pageData.offset);
    if (offsets.length === 1) {
      return {
        devices: [{ ipAddress: "192.0.2.10" }, { ipAddress: "bad" }],
        total: 3,
      };
    }
    return { devices: [{ ipAddress: "2001:0db8::1" }], total: 3 };
  };

  const addresses = await client.inventoryAddresses("Default");

  assert.deepEqual(addresses, new Set(["192.0.2.10", "2001:db8::1"]));
  assert.deepEqual(offsets, [0, 2]);
});
