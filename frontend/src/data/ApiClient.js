import { ApiError } from "./ApiErrors";

export class ApiClient {
  constructor(
    baseURL = "http://127.0.0.1:8000/financetool/api/v1",
    getAuthToken
  ) {
    this.baseURL = baseURL;
    this.getAuthToken = getAuthToken;
  }

  buildPath(path, query) {
    if (!query) return path;
    const qs = new URLSearchParams();
    Object.entries(query).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== "") qs.set(k, String(v));
    });
    const suffix = qs.toString();
    return suffix ? `${path}?${suffix}` : path;
  }

  async request(
    path,
    {
      method = "GET",
      data,
      headers,
      signal,
      timeoutMs = 15000,
      withCredentials = true,
    } = {}
  ) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);
    const finalSignal = signal || controller.signal;

    const h = {
      "Content-Type": "application/json",
      ...(headers || {}),
    };
    const token = this.getAuthToken ? this.getAuthToken() : undefined;
    if (token) h["Authorization"] = `Bearer ${token}`;

    const url = path.startsWith("http") ? path : `${this.baseURL}${path}`;
    let body;
    if (data !== undefined && method !== "GET") {
      body = JSON.stringify(data);
    }

    let res;
    try {
      res = await fetch(url, {
        method,
        headers: h,
        body,
        credentials: withCredentials ? "include" : "same-origin",
        signal: finalSignal,
      });
    } catch (e) {
      clearTimeout(timer);
      if (e?.name === "AbortError") throw new ApiError("Request timeout", 408);
      throw new ApiError("Network error", 0);
    }

    clearTimeout(timer);

    const ct = res.headers.get("content-type") || "";
    const isJson = ct.includes("application/json");
    const payload = isJson
      ? await res.json().catch(() => ({}))
      : await res.text();

    if (!res.ok) {
      const msg =
        (payload && (payload.message || payload.error)) ||
        res.statusText ||
        "Request failed";
      throw new ApiError(msg, res.status, payload);
    }
    return payload;
  }

  get(path, query, opts) {
    const p = this.buildPath(path, query);
    return this.request(p, { ...(opts || {}), method: "GET" });
  }
  post(path, data, opts) {
    return this.request(path, { ...(opts || {}), method: "POST", data });
  }
  put(path, data, opts) {
    return this.request(path, { ...(opts || {}), method: "PUT", data });
  }
  patch(path, data, opts) {
    return this.request(path, { ...(opts || {}), method: "PATCH", data });
  }
  delete(path, opts) {
    return this.request(path, { ...(opts || {}), method: "DELETE" });
  }
}
