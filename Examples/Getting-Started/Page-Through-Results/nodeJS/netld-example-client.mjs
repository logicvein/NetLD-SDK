import { randomUUID } from "node:crypto";

export class NetLDError extends Error {}

export class NetLDClient {
  constructor(baseUrl, apiKey, timeout = 10000, debug = false) {
    this.baseUrl = baseUrl.replace(/\/$/, "");
    this.apiKey = apiKey;
    this.timeout = timeout;
    this.debug = debug;
    this.cookieHeader = "";
  }

  static fromEnv() {
    const baseUrl = (process.env.NETLD_BASE_URL || "").trim();
    const apiKey = (process.env.NETLD_API_KEY || "").trim();
    if (!baseUrl) throw new NetLDError("Set NETLD_BASE_URL in .env before running this example.");
    if (!apiKey) throw new NetLDError("Set NETLD_API_KEY in .env before running this example.");
    return new NetLDClient(baseUrl, apiKey, 10000, process.env.NETLD_DEBUG === "1");
  }

  headers(extra = {}) {
    return {
      Authorization: `Bearer ${this.apiKey}`,
      ...(this.cookieHeader ? { Cookie: this.cookieHeader } : {}),
      ...extra,
    };
  }

  updateCookies(response) {
    const values = response.headers.getSetCookie
      ? response.headers.getSetCookie()
      : splitSetCookie(response.headers.get("set-cookie") || "");
    this.cookieHeader = values.map((value) => value.split(";", 1)[0]).join("; ");
  }

  async request(options = {}) {
    let response;
    try {
      response = await fetch(`${this.baseUrl}/rest`, {
        ...options,
        headers: this.headers(options.headers),
        redirect: "manual",
        signal: AbortSignal.timeout(this.timeout),
      });
    } catch {
      throw new NetLDError(`Could not reach ${this.baseUrl}.`);
    }
    if (response.status >= 300 && response.status < 400) {
      throw new NetLDError(`Request redirected to ${response.headers.get("location") || ""}.`);
    }
    if (!response.ok) {
      throw new NetLDError(`Request failed with HTTP ${response.status}.`);
    }
    this.updateCookies(response);
    return response;
  }

  async login() {
    const response = await this.request();
    console.log(`Login status=${response.status}`);
  }

  async call(method, params) {
    const payload = { jsonrpc: "2.0", method, params, id: randomUUID() };
    if (this.debug) console.log("Request JSON:\n" + JSON.stringify(payload, null, 2));
    const response = await this.request({
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    let data;
    try {
      data = await response.json();
    } catch {
      throw new NetLDError(`${method} returned invalid JSON.`);
    }
    if (this.debug) console.log("Response JSON:\n" + JSON.stringify(data, null, 2));
    if (data.error) throw new NetLDError(JSON.stringify(data.error));
    return data.result;
  }

  async getConfigurationChangeLogPage(network, ipAddress, offset, pageSize) {
    const result = await this.call("Configuration.retrieveSnapshotChangeLog", {
      network,
      ipAddress,
      pageData: { offset, pageSize },
    });
    if (!result || !Array.isArray(result.changeLogs)) {
      throw new NetLDError("Configuration.retrieveSnapshotChangeLog returned an invalid page.");
    }
    return result;
  }
}

function splitSetCookie(header) {
  return header ? header.split(/,(?=\s*[^;=]+=[^;]+)/) : [];
}
