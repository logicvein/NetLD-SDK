import assert from "node:assert/strict";
import test from "node:test";

import { createParameters } from "../create-device.mjs";

test("builds named create-device parameters", () => {
  assert.deepEqual(createParameters("Default", "2001:0db8::10", "Cisco::IOS"), {
    network: "Default",
    ipAddress: "2001:db8::10",
    adapterId: "Cisco::IOS",
  });
});

test("rejects an invalid IP address", () => {
  assert.throws(() => createParameters("Default", "not-an-address", "Cisco::IOS"), /valid IPv4/);
});
