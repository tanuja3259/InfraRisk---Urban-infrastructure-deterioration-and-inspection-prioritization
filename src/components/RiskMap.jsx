import { MapContainer, TileLayer, CircleMarker, Popup } from "react-leaflet";
import { Link } from "react-router-dom";
import { priorityColor } from "../api/client";

const CENTER = [30.3165, 78.0322]; // Dehradun

export default function RiskMap({ features = [], height = "520px" }) {
  return (
    <div className="overflow-hidden rounded-2xl border border-slateish/10 shadow-soft" style={{ height }}>
      <MapContainer center={CENTER} zoom={12} scrollWheelZoom style={{ height: "100%", width: "100%" }}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {features.map((f) => (
          <CircleMarker
            key={f.id}
            center={[f.lat, f.lon]}
            radius={f.priority === "Critical" ? 11 : f.priority === "High" ? 9 : 7}
            pathOptions={{
              color: "#fff",
              weight: 1.5,
              fillColor: priorityColor[f.priority] || "#0d7377",
              fillOpacity: 0.85,
            }}
          >
            <Popup>
              <div className="min-w-[180px] space-y-1 text-sm">
                <p className="font-semibold">{f.name}</p>
                <p className="text-xs opacity-70">{f.asset_code} · {f.asset_type}</p>
                <p>
                  Risk <strong>{f.risk_score}</strong> · {f.priority}
                </p>
                <p className="text-xs">Deterioration p = {(f.deterioration_prob * 100).toFixed(1)}%</p>
                <Link className="text-teal underline" to={`/assets/${f.id}`}>
                  Open asset details
                </Link>
              </div>
            </Popup>
          </CircleMarker>
        ))}
      </MapContainer>
    </div>
  );
}
