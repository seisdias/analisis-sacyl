// web/assets/ui/modals/histograms/proxy_client.js
import { state } from "../../../state.js";
import { apiJson } from "../modal_utils.js";

export function createProxyClient({ debug = false } = {}) {
  const cache = new Map(); // key: `${type}|${date}`

  const log = (...args) => {
    if (debug) console.debug("[histograms]", ...args);
  };

  async function getProxy({ date, type }) {
    const cacheKey = `${type}|${date}`;
    const hit = cache.get(cacheKey);
    if (hit) {
      log("cache hit", cacheKey);
      return hit;
    }

    const url =
      `/histograms/proxy?date=${encodeURIComponent(date)}&type=${encodeURIComponent(type)}` +
      `&session_id=${encodeURIComponent(state.sessionId || "")}`;

    log("fetch", url);
    let res = await apiJson("GET", url);

    // Compat: si apiJson envuelve en {data: ...}
    if (
      res &&
      typeof res === "object" &&
      res.data &&
      (res.x || res.y || res.categories || res.pct || res.abs) == null
    ) {
      res = res.data;
      log("unwrapped res.data", res);
    }

    cache.set(cacheKey, res);
    return res;
  }

  return {
    getProxy,
    clearCache: () => cache.clear(),
  };
}
