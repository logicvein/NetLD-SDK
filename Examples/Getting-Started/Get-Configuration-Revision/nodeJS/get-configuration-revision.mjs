import "dotenv/config";

import {
  NetLDClient,
  NetLDError,
  decodeRevisionContent,
} from "./netld-example-client.mjs";

const network = process.env.NETLD_NETWORK || "Default";
const deviceIp = process.env.NETLD_DEVICE_IP || "10.95.1.40";
const configPath = process.env.NETLD_CONFIG_PATH || "/running-config";

const client = NetLDClient.fromEnv();
await client.login();

const pageData = await client.getConfigurationHistory({
  networks: [network],
  scheme: "ipAddress",
  data: deviceIp,
});

const matches = (pageData?.configHistoryItems || []).filter(
  (item) => item.path === configPath,
);
if (matches.length === 0) {
  throw new NetLDError(
    `No configuration history item for "${configPath}" was found on ${deviceIp}@${network}.`,
  );
}

const historyItem = matches[0];
const revision = await client.retrieveRevision({
  network: historyItem.managedNetwork,
  ipAddress: historyItem.ipAddress,
  configPath: historyItem.path,
  timestamp: historyItem.lastChanged,
});
if (!revision) {
  throw new NetLDError("Configuration.retrieveRevision returned no revision.");
}

const { content, ...metadata } = revision;
console.log("Revision metadata:");
console.log(JSON.stringify(metadata, null, 2));

const decodedContent = decodeRevisionContent(revision);
if (decodedContent === null) {
  console.log("Revision content is empty or binary; Base64 content was not printed.");
} else {
  console.log("Decoded revision content:");
  console.log(decodedContent);
}
