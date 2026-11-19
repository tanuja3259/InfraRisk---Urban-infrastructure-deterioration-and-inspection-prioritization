import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  Cell,
  ReferenceLine,
} from "recharts";

export default function ShapChart({ contributions = [] }) {
  const data = contributions.slice(0, 10).map((c) => ({
    name: c.feature.replace(/_/g, " "),
    contribution: Number(c.contribution.toFixed(4)),
    value: c.value,
  }));

  if (!data.length) {
    return <p className="text-sm text-slateish/60">No SHAP explanation available yet.</p>;
  }

  return (
    <div className="h-72 w-full">
      <ResponsiveContainer>
        <BarChart data={data} layout="vertical" margin={{ left: 24, right: 16 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#d5dee3" />
          <XAxis type="number" tick={{ fontSize: 11 }} />
          <YAxis type="category" dataKey="name" width={120} tick={{ fontSize: 11 }} />
          <Tooltip
            formatter={(v, _n, props) => [`${v}`, `Contribution (value=${props.payload.value})`]}
          />
          <ReferenceLine x={0} stroke="#243642" />
          <Bar dataKey="contribution" radius={[0, 4, 4, 0]}>
            {data.map((d, i) => (
              <Cell key={i} fill={d.contribution >= 0 ? "#b42318" : "#15803d"} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
