import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api, priorityColor } from "../api/client";
import RiskMap from "../components/RiskMap";
import StatCard from "../components/StatCard";

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [features, setFeatures] = useState([]);
  const [priority, setPriority] = useState("");
  const [assetType, setAssetType] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      try {
        const params = {};
        if (priority) params.priority = priority;
        if (assetType) params.asset_type = assetType;
        const [s, m] = await Promise.all([api.stats(), api.map(params)]);
        if (!cancelled) {
          setStats(s);
          setFeatures(m);
          setError("");
        }
      } catch (e) {
        if (!cancelled) setError(e.message || "Failed to load dashboard");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, [priority, assetType]);

  const queue = useMemo(() => features.slice(0, 12), [features]);

  return (
    <div className="space-y-6">
      <section className="animate-rise">
        <h1 className="font-display text-4xl text-ink md:text-5xl">
          Inspection priority at a glance
        </h1>
        <p className="mt-2 max-w-2xl text-slateish/75">
          ML deterioration risk fused with visual damage evidence into an explainable
          Infrastructure Risk Score — mapped for Dehradun-area roads and bridges.
        </p>
      </section>

      {error && (
        <div className="rounded-xl border border-critical/30 bg-critical/10 px-4 py-3 text-sm text-critical">
          {error}. Start the API with <code>uvicorn app.main:app --reload</code> in{" "}
          <code>backend/</code>.
        </div>
      )}

      {stats && (
        <div className="animate-rise-delay grid gap-3 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-7">
          <StatCard label="Assets" value={stats.total_assets} />
          <StatCard label="Roads" value={stats.roads} accent="teal" />
          <StatCard label="Bridges" value={stats.bridges} accent="amber" />
          <StatCard label="Critical" value={stats.critical} accent="critical" />
          <StatCard label="High" value={stats.high} accent="high" />
          <StatCard label="Pending reviews" value={stats.pending_reviews} accent="medium" />
          <StatCard label="Avg risk" value={stats.avg_risk_score} accent="low" />
        </div>
      )}

      <div className="flex flex-wrap items-center gap-3">
        <select
          className="rounded-lg border border-slateish/15 bg-white px-3 py-2 text-sm"
          value={priority}
          onChange={(e) => setPriority(e.target.value)}
        >
          <option value="">All priorities</option>
          {["Critical", "High", "Medium", "Low"].map((p) => (
            <option key={p} value={p}>
              {p}
            </option>
          ))}
        </select>
        <select
          className="rounded-lg border border-slateish/15 bg-white px-3 py-2 text-sm"
          value={assetType}
          onChange={(e) => setAssetType(e.target.value)}
        >
          <option value="">Roads & bridges</option>
          <option value="road">Roads</option>
          <option value="bridge">Bridges</option>
        </select>
        <div className="flex flex-wrap gap-3 text-xs text-slateish/70">
          {Object.entries(priorityColor).map(([k, c]) => (
            <span key={k} className="inline-flex items-center gap-1.5">
              <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ background: c }} />
              {k}
            </span>
          ))}
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
        <RiskMap features={features} />
        <div className="rounded-2xl border border-slateish/10 bg-white/80 p-4 shadow-soft">
          <h2 className="font-display text-2xl">Priority queue</h2>
          <p className="mb-3 text-sm text-slateish/65">Ranked by Infrastructure Risk Score</p>
          {loading ? (
            <p className="text-sm text-slateish/60">Loading…</p>
          ) : (
            <ul className="max-h-[460px] space-y-2 overflow-auto pr-1">
              {queue.map((f, idx) => (
                <li key={f.id}>
                  <Link
                    to={`/assets/${f.id}`}
                    className="flex items-start gap-3 rounded-xl border border-transparent px-2 py-2 transition hover:border-slateish/10 hover:bg-mist/70"
                  >
                    <span className="mt-0.5 w-6 text-sm font-semibold text-slateish/40">
                      {idx + 1}
                    </span>
                    <span className="min-w-0 flex-1">
                      <span className="block truncate font-medium">{f.name}</span>
                      <span className="text-xs text-slateish/60">
                        {f.asset_code} · {f.asset_type}
                      </span>
                    </span>
                    <span className="text-right">
                      <span className="block font-semibold">{f.risk_score}</span>
                      <span
                        className="text-xs font-medium"
                        style={{ color: priorityColor[f.priority] }}
                      >
                        {f.priority}
                      </span>
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}
