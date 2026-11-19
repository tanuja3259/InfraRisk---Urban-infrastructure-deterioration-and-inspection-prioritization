export default function StatCard({ label, value, accent = "teal" }) {
  const accents = {
    teal: "from-teal/15 to-transparent text-tealdeep",
    critical: "from-critical/15 to-transparent text-critical",
    high: "from-high/15 to-transparent text-high",
    medium: "from-medium/15 to-transparent text-medium",
    low: "from-low/15 to-transparent text-low",
    amber: "from-amber/15 to-transparent text-amber",
  };
  return (
    <div className={`rounded-2xl border border-slateish/10 bg-gradient-to-br ${accents[accent]} p-4 shadow-soft`}>
      <p className="text-xs uppercase tracking-wide text-slateish/60">{label}</p>
      <p className="mt-1 font-display text-3xl text-ink">{value}</p>
    </div>
  );
}
