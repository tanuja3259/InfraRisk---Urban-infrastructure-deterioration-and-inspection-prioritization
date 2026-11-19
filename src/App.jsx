import { NavLink, Route, Routes } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import AssetDetail from "./pages/AssetDetail";
import DetectPage from "./pages/DetectPage";
import ReviewsPage from "./pages/ReviewsPage";

const linkClass = ({ isActive }) =>
  `px-3 py-2 rounded-lg text-sm font-medium transition ${
    isActive ? "bg-teal text-white" : "text-slateish/80 hover:bg-mist"
  }`;

export default function App() {
  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-40 border-b border-slateish/10 bg-fog/85 backdrop-blur-md">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-3">
          <div>
            <p className="font-display text-2xl tracking-tight text-ink">InfraRisk</p>
            <p className="text-xs text-slateish/70">
              Urban infrastructure deterioration · inspection prioritization
            </p>
          </div>
          <nav className="flex flex-wrap items-center gap-1">
            <NavLink to="/" end className={linkClass}>
              GIS Dashboard
            </NavLink>
            <NavLink to="/detect" className={linkClass}>
              Damage Detection
            </NavLink>
            <NavLink to="/reviews" className={linkClass}>
              Human Review
            </NavLink>
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-6">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/assets/:id" element={<AssetDetail />} />
          <Route path="/detect" element={<DetectPage />} />
          <Route path="/reviews" element={<ReviewsPage />} />
        </Routes>
      </main>
    </div>
  );
}
