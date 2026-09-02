import assert from "node:assert/strict";
import test from "node:test";

import { getAllChangeLogs } from "../page-through-results.mjs";

test("retrieves all pages including a partial final page", async () => {
  const offsets = [];
  const client = {
    async getConfigurationChangeLogPage(network, ipAddress, offset, pageSize) {
      offsets.push(offset);
      const total = 61;
      const count = Math.min(pageSize, total - offset);
      return {
        offset,
        pageSize,
        total: offset === 0 ? total : 0,
        changeLogs: Array.from({ length: count }, (_, index) => ({ index: offset + index })),
      };
    },
  };

  const results = await getAllChangeLogs(client, "Default", "192.0.2.10", 10);

  assert.equal(results.length, 61);
  assert.deepEqual(offsets, [0, 10, 20, 30, 40, 50, 60]);
});

test("rejects a non-positive page size", async () => {
  await assert.rejects(
    getAllChangeLogs({}, "Default", "192.0.2.10", 0),
    /positive integer/,
  );
});
