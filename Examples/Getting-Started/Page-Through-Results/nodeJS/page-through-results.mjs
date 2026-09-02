import { NetLDClient, NetLDError } from "./netld-example-client.mjs";
import { pathToFileURL } from "node:url";

export async function getAllChangeLogs(client, network, ipAddress, pageSize) {
  if (!Number.isInteger(pageSize) || pageSize <= 0) {
    throw new NetLDError("NETLD_PAGE_SIZE must be a positive integer.");
  }

  const changeLogs = [];
  let offset = 0;
  let total = null;

  while (total === null || offset < total) {
    const page = await client.getConfigurationChangeLogPage(
      network,
      ipAddress,
      offset,
      pageSize,
    );
    const pageOffset = Number(page.offset ?? offset);
    const reportedTotal = Number(page.total ?? pageOffset + page.changeLogs.length);
    total = total === null ? reportedTotal : Math.max(total, reportedTotal);
    changeLogs.push(...page.changeLogs);
    const nextOffset = pageOffset + page.changeLogs.length;

    console.log(
      `Fetched ${page.changeLogs.length} records at offset ${pageOffset} ` +
        `(${nextOffset} of ${total})`,
    );

    if (nextOffset >= total) break;
    if (page.changeLogs.length === 0 || nextOffset <= offset) {
      throw new NetLDError("Paging stopped before all results were returned.");
    }
    offset = nextOffset;
  }

  return changeLogs;
}

export async function main() {
  const client = NetLDClient.fromEnv();
  const network = process.env.NETLD_NETWORK || "Default";
  const ipAddress = (process.env.NETLD_DEVICE_IP || "").trim();
  if (!ipAddress) {
    throw new NetLDError("Set NETLD_DEVICE_IP in .env before running this example.");
  }
  const pageSize = Number.parseInt(process.env.NETLD_PAGE_SIZE || "10", 10);

  await client.login();
  const changeLogs = await getAllChangeLogs(client, network, ipAddress, pageSize);
  console.log(JSON.stringify({ total: changeLogs.length, changeLogs }, null, 2));
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  await main();
}
