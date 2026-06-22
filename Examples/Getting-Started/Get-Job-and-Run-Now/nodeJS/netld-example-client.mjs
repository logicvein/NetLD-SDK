import { randomUUID } from "node:crypto";
import process from "node:process";

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
    const baseUrl = process.env.NETLD_BASE_URL;
    const apiKey = process.env.NETLD_API_KEY;
    const debug = process.env.NETLD_DEBUG === "1";

    if (!baseUrl) {
      throw new NetLDError("Set NETLD_BASE_URL in .env before running this example.");
    }
    if (!apiKey) {
      throw new NetLDError("Set NETLD_API_KEY before running this example.");
    }

    return new NetLDClient(baseUrl, apiKey, 10000, debug);
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
    const setCookie = response.headers.getSetCookie
      ? response.headers.getSetCookie()
      : splitSetCookie(response.headers.get("set-cookie") || "");

    this.cookieHeader = setCookie
      .map((cookie) => cookie.split(";")[0])
      .filter(Boolean)
      .join("; ");
  }

  async login() {
    let response;

    try {
      response = await fetch(`${this.baseUrl}/rest`, {
        headers: {
          Authorization: `Bearer ${this.apiKey}`,
          ...(this.cookieHeader ? { Cookie: this.cookieHeader } : {}),
        },
        redirect: "manual",
        signal: AbortSignal.timeout(this.timeout),
      });
    } catch (error) {
      throw new NetLDError(
        `Could not reach ${this.baseUrl}. Check NETLD_BASE_URL in your .env file.`,
      );
    }

    if (isRedirect(response)) {
      const location = response.headers.get("location") || "";
      throw new NetLDError(
        `Login redirected instead of returning a netLD session. Redirect target: ${location}`,
      );
    }

    if (!response.ok) {
      throw new NetLDError(`Login failed: ${response.status} ${await response.text()}`);
    }

    this.updateCookies(response);
    console.log(`Login status=${response.status}`);

    if (this.debug) {
      console.log(`Cookies=${this.cookieHeader}`);
    }
  }

  async call(method, params = {}) {
    const payload = {
      jsonrpc: "2.0",
      method,
      params,
      id: randomUUID(),
    };

    if (this.debug) {
      console.log("Request JSON:");
      console.log(JSON.stringify(payload, null, 2));
    }

    let response;

    try {
      response = await fetch(`${this.baseUrl}/rest`, {
        method: "POST",
        headers: this.headers(),
        body: JSON.stringify(payload),
        redirect: "manual",
        signal: AbortSignal.timeout(this.timeout),
      });
    } catch (error) {
      throw new NetLDError(
        `Could not reach ${this.baseUrl}. Check NETLD_BASE_URL in your .env file.`,
      );
    }

    if (isRedirect(response)) {
      const location = response.headers.get("location") || "";
      throw new NetLDError(
        `API call redirected instead of returning JSON-RPC data. Redirect target: ${location}`,
      );
    }

    if (!response.ok) {
      throw new NetLDError(`API call failed: ${response.status} ${await response.text()}`);
    }

    const data = await response.json();

    if (this.debug) {
      console.log("Response JSON:");
      console.log(JSON.stringify(data, null, 2));
    }

    if (data.error) {
      throw new NetLDError(JSON.stringify(data.error));
    }

    return data.result;
  }

  searchAvailableJobs({
    networks,
    offset = 0,
    pageSize = 100,
    sortColumn = "",
    descending = false,
  }) {
    const networkList = Array.isArray(networks) ? networks : [networks];

    return this.call("Scheduler.searchJobs", {
      pageData: {
        offset,
        jobData: [],
        pageSize,
        total: 1,
      },
      networks: networkList,
      sortColumn,
      descending,
    });
  }

  getJob(jobId) {
    return this.call("Scheduler.getJob", { jobId });
  }

  runNow(jobData) {
    return this.call("Scheduler.runNow", { jobData });
  }
}

export function printJson(value) {
  console.log(JSON.stringify(value, null, 2));
}

function splitSetCookie(header) {
  return header ? header.split(/,(?=\s*[^;=]+=[^;]+)/) : [];
}

function isRedirect(response) {
  return response.status >= 300 && response.status < 400;
}
