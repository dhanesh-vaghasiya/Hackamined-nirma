import { motion } from "framer-motion";
import { useAuth } from "../context/AuthContext";
import { useNavigate } from "react-router-dom";
import { LogOut } from "lucide-react";

/* ── Oasis leaf logo mark ──────────────────────────────────────────── */
function OasisLogo() {
  return (
    <motion.svg
      width="28"
      height="28"
      viewBox="0 0 28 28"
      animate={{ rotate: [0, 5, -5, 0] }}
      transition={{ repeat: Infinity, duration: 6, ease: "easeInOut" }}
      className="shrink-0"
    >
      <circle cx="14" cy="14" r="13" fill="none" stroke="#97A87A" strokeWidth="1.5" opacity="0.4" />
      <circle cx="14" cy="14" r="6" fill="#97A87A" opacity="0.7" />
      <circle cx="14" cy="14" r="2.5" fill="#dad7cd" />
    </motion.svg>
  );
}

/* ── Layer switcher ────────────────────────────────────────────────── */
const LAYERS = ["Market Intelligence", "Employers View", "Worker Portal", "AI Assistant"];

function LayerSwitcher({ activeLayer, setActiveLayer }) {
  return (
    <div
      className="flex items-center rounded-full px-1 py-1"
      style={{
        background: "rgba(218,215,205,0.08)",
        border: "1px solid rgba(151,168,122,0.2)",
      }}
    >
      {LAYERS.map((label) => {
        const isActive = activeLayer === label;
        return (
          <button
            key={label}
            onClick={() => setActiveLayer(label)}
            className="relative rounded-full px-4 py-1.5 text-sm transition-colors cursor-pointer font-brand"
            style={{
              fontWeight: isActive ? 700 : 500,
              color: isActive ? "#1A1D1A" : "#dad7cd",
              zIndex: 1,
            }}
            onMouseEnter={(e) => {
              if (!isActive) e.currentTarget.style.color = "#FFFFFF";
            }}
            onMouseLeave={(e) => {
              if (!isActive) e.currentTarget.style.color = "#dad7cd";
            }}
          >
            {isActive && (
              <motion.span
                layoutId="navPill"
                className="absolute inset-0 rounded-full"
                style={{ background: "#97A87A", zIndex: -1 }}
                transition={{ type: "spring", stiffness: 380, damping: 30 }}
              />
            )}
            {label}
          </button>
        );
      })}
    </div>
  );
}

/* ── Main Navbar ───────────────────────────────────────────────────── */
const Navbar = ({ activeLayer, setActiveLayer }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <nav
      className="fixed top-0 left-0 w-full flex items-center justify-between px-6"
      style={{
        height: 64,
        background: "rgba(18,20,18,0.85)",
        backdropFilter: "blur(20px)",
        WebkitBackdropFilter: "blur(20px)",
        borderBottom: "1px solid rgba(151,168,122,0.15)",
        zIndex: 50,
      }}
    >
      {/* LEFT — Logo */}
      <div className="flex items-center gap-2.5">
        <OasisLogo />
        <div className="flex flex-col leading-none">
          <span className="font-brand" style={{ fontWeight: 700, fontSize: 22, color: "#FFFFFF", lineHeight: 1 }}>
            OASIS
          </span>
          <span className="font-data" style={{ fontSize: 9, color: "#6B7265", letterSpacing: "0.15em", marginTop: 3 }}>
            Workforce Intelligence
          </span>
        </div>
      </div>

      {/* CENTER — Layer Switcher */}
      <LayerSwitcher activeLayer={activeLayer} setActiveLayer={setActiveLayer} />

      {/* RIGHT — User + Logout */}
      <div className="flex items-center gap-4">
        {user && (
          <>
            <span className="text-sm font-data" style={{ color: "#dad7cd" }}>
              {user?.name || user?.email}
            </span>
            <button
              onClick={handleLogout}
              className="flex items-center gap-1 text-sm cursor-pointer transition-colors font-data"
              style={{ color: "#6B7265" }}
              onMouseEnter={(e) => (e.currentTarget.style.color = "#DC2626")}
              onMouseLeave={(e) => (e.currentTarget.style.color = "#6B7265")}
            >
              <LogOut size={15} /> Logout
            </button>
          </>
        )}
      </div>
    </nav>
  );
};

export default Navbar;
