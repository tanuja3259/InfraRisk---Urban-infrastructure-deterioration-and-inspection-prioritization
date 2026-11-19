const BASE = "/api";

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, options);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || res.statusText);
  }
  if (res.status === 204) return null;
  const type = res.headers.get("content-type") || "";
  if (type.includes("application/json")) return res.json();
  return res;
}

export const api = {
  health: () => request("/health"),
  stats: () => request("/stats"),
  assets: (params = {}) => {
    const q = new URLSearchParams(params).toString();
    return request(`/assets${q ? `?${q}` : ""}`);
  },
  asset: (id) => request(`/assets/${id}`),
  prediction: (id) => request(`/assets/${id}/prediction`),
  shap: (id) => request(`/assets/${id}/shap`),
  map: (params = {}) => {
    const q = new URLSearchParams(params).toString();
    return request(`/map${q ? `?${q}` : ""}`);
  },
  priority: (limit = 50) => request(`/priority?limit=${limit}`),
  reviews: (status) => request(`/reviews${status ? `?status=${status}` : ""}`),
  updateReview: (id, body) =>
    request(`/reviews/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  metrics: () => request("/models/metrics"),
  detect: async (file, assetId) => {
    const form = new FormData();
    form.append("file", file);
    const q = assetId ? `?asset_id=${assetId}` : "";
    return request(`/detect${q}`, { method: "POST", body: form });
  },
  annotate: async (file) => {
    const form = new FormData();
    form.append("file", file);
    const res = await fetch(`${BASE}/detect/annotate`, { method: "POST", body: form });
    if (!res.ok) throw new Error("Annotation failed");
    return res.blob();
  },
};

export const priorityColor = {
  Critical: "#b42318",
  High: "#c2410c",
  Medium: "#a16207",
  Low: "#15803d",
};
