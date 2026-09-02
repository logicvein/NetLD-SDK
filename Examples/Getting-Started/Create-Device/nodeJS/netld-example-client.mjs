import { randomUUID } from "node:crypto";

export class NetLDError extends Error {}

export class NetLDClient {
  constructor(baseUrl, apiKey, timeout = 10000) {
    this.baseUrl = baseUrl.replace(/\/$/, "");
    this.apiKey = apiKey;
    this.timeout = timeout;
    this.cookieHeader = "";
  }

  headers(extra = {}) {
    return {
      Authorization: `Bearer ${this.apiKey}`,
      "Content-Type": "application/json",
      ...(this.cookieHeader ? { Cookie: this.cookieHeader } : {}),
      ...extra,
    };
  }

  updateCookies(response) {
    const values = response.headers.getSetCookie?.() || splitSetCookie(response.headers.get("set-cookie") || "");
    this.cookieHeader = values.map((value) => value.split(";", 1)[0]).filter(Boolean).join("; ");
  }

  async login() {
    const response = await this.request("/rest");
    this.updateCookies(response);
  }

  async request(path, options = {}) {
    let response;
    try {
      response = await fetch(`${this.baseUrl}${path}`, {
        redirect: "manual",
        signal: AbortSignal.timeout(this.timeout),
        ...options,
        headers: this.headers(options.headers),
      });
    } catch {
      throw new NetLDError(`Could not reach ${this.baseUrl}.`);
    }
    if (response.status >= 300 && response.status < 400) {
      throw new NetLDError(`Request redirected to ${response.headers.get("location") || ""}.`);
    }
    if (!response.ok) throw new NetLDError(`Request failed with HTTP ${response.status}.`);
    return response;
  }

  async call(method, parameters = {}) {
    const response = await this.request("/rest", {
      method: "POST",
      body: JSON.stringify({ jsonrpc: "2.0", method, params: parameters, id: randomUUID() }),
    });
    const data = await response.json();
    if (data.error) throw new NetLDError(JSON.stringify(data.error));
    return data.result;
  }

  getDevice({ network, ipAddress }) {
    return this.call("Inventory.getDevice", { network, ipAddress });
  }

  createDevice({ network, ipAddress, adapterId }) {
    return this.call("Inventory.createDevice", { network, ipAddress, adapterId });
  }
}

function splitSetCookie(header) {
  return header ? header.split(/,(?=\s*[^;=]+=[^;]+)/) : [];
}

