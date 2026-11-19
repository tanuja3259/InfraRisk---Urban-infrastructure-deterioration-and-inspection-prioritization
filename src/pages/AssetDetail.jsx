import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, priorityColor } from "../api/client";
import ShapChart from "../components/ShapChart";

export default function AssetDetail() {
  const { id } = useParams();
  const [asset, setAsset] = useState(null);
  const [pred, setPred] = useState(null);
  const [shap, setShap] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const [a, p, s] = await Promise.all([
          api.asset(id),
          api.prediction(id),
          api.shap(id),
        ]);
        if (!cancelled) {
          setAsset(a);
          setPred(p);
          setShap(s);
        }
      } catch (e) {
        if (!cancelled) setError(e.message);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, [id]);

  if (error) {
    return <p className="text-critical">{error}</p>;
  }
  if (!asset || !pred) {
    return <p className="text-slateish/60">Loading asset…</p>;
  }

  const action =
    pred.priority === "Critical"
      ? "Schedule immediate field inspection within 7 days; draft emergency notice."
      : pred.priority === "High"
        ? "Prioritize inspection within 30 days; prepare maintenance assessment."
        : pred.priority === "Medium"
          ? "Include in next quarterly inspection cycle; monitor after rainfall events."
          : "Continue routine scheduled inspection; no urgent action required.";

  return (
    <div className="space-y-6 animate-rise">
      <Link to="/" className="text-sm text-teal hover:underline">
        ← Back to map
      </Link>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-sm text-slateish/60">{asset.asset_code}</p>
          <h1 className="font-display text-4xl text-ink">{asset.name}</h1>
          <p className="mt-1 capitalize text-slateish/70">
            {asset.asset_type} · {asset.material} · age {asset.age_years} yrs
          </p>
        </div>
        <div className="rounded-2xl border border-slateish/10 bg-white px-5 py-3 text-right shadow-soft">
          <p className="text-xs uppercase tracking-wide text-slateish/55">Risk score</p>
          <p className="font-display text-4xl">{pred.risk_score}</p>
          <p className="font-semibold" style={{ color: priorityColor[pred.priority] }}>
            {pred.priority}
          </p>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {[
          ["Deterioration probability", `${(pred.deterioration_prob * 100).toFixed(1)}%`],
          ["CV damage score", pred.cv_damage_score.toFixed(3)],
          ["Model", pred.model_name],
          ["Traffic (AADT)", asset.traffic_aadt?.toLocaleString()],
          ["Last inspection score", asset.last_inspection_score],
          ["Years since inspection", asset.years_since_inspection],
          ["Years since maintenance", asset.years_since_maintenance],
          ["Rainfall (mm)", asset.rainfall_mm],
        ].map(([k, v]) => (
          <div key={k} className="rounded-xl border border-slateish/10 bg-white/80 p-3">
            <p className="text-xs text-slateish/55">{k}</p>
            <p className="font-medium">{v ?? "—"}</p>
          </div>
        ))}
      </div>

      <div className="rounded-2xl border border-amber/20 bg-amber/5 p-4">
        <h2 className="font-semibold text-ink">Recommended action</h2>
        <p className="mt-1 text-sm text-slateish/80">{action}</p>
        <p className="mt-2 text-xs text-slateish/55">
          Decision support only — final inspection and notices require human authorization.
        </p>
      </div>

      <div className="rounded-2xl border border-slateish/10 bg-white/90 p-4 shadow-soft">
        <h2 className="font-display text-2xl">SHAP explanation</h2>
        <p className="mb-3 text-sm text-slateish/65">
          Feature contributions to the deterioration prediction (model: {shap?.model_name})
        </p>
        <ShapChart contributions={shap?.feature_contributions || []} />
      </div>
    </div>
  );
}
