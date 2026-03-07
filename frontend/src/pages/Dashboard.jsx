import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import GlassSelect from "../components/ui/GlassSelect";
import HiringTrends from "../components/dashboard/HiringTrends";
import SkillsIntel from "../components/dashboard/SkillsIntel";
import AiVulnerability from "../components/dashboard/AiVulnerability";
import MarketRecords from "../components/dashboard/MarketRecords";
import WorkerPortal from "../components/worker/WorkerPortal";
import ChatbotPage from "./ChatbotPage";
import { getMarketSummary } from "../services/market";

/* ── constants ─────────────────────────────────────────────────────── */
const TABS = ["Hiring Trends", "Skills Intel", "AI Vulnerability", "Data Records"];


const CITY_OPTIONS = [
  { value: "all-india", label: "All India" },
  { value: "mumbai", label: "Mumbai" },
  { value: "delhi", label: "Delhi" },
  { value: "bengaluru", label: "Bengaluru" },
  { value: "hyderabad", label: "Hyderabad" },
  { value: "pune", label: "Pune" },
  { value: "chennai", label: "Chennai" },
  { value: "jaipur", label: "Jaipur" },
  { value: "indore", label: "Indore" },
  { value: "lucknow", label: "Lucknow" },
  { value: "bhopal", label: "Bhopal" },
  { value: "surat", label: "Surat" },
  { value: "nagpur", label: "Nagpur" },
  { value: "patna", label: "Patna" },
  { value: "coimbatore", label: "Coimbatore" },
  { value: "kochi", label: "Kochi" },
  { value: "chandigarh", label: "Chandigarh" },
];

const TIME_OPTIONS = [
  { value: "7d", label: "7 D" },
  { value: "30d", label: "30 D" },
  { value: "90d", label: "90 D" },
  { value: "1yr", label: "1 YR" },
];

/* ── tab renderer ──────────────────────────────────────────────────── */
function renderTab(name, filters) {
  switch (name) {
    case "Hiring Trends":    return <HiringTrends filters={filters} />;
    case "Skills Intel":     return <SkillsIntel filters={filters} />;
    case "AI Vulnerability": return <AiVulnerability filters={filters} />;
    case "Data Records":     return <MarketRecords filters={filters} />;
    default:                 return null;
  }
}

/* ── Dashboard ─────────────────────────────────────────────────────── */
const Dashboard = ({ activeLayer }) => {
  const [activeTab, setActiveTab] = useState("Hiring Trends");
  const [city, setCity] = useState("all-india");
  const [timeframe, setTimeframe] = useState("1yr");
  const [summary, setSummary] = useState({ rows: 0, unique_roles: 0, unique_cities: 0, vulnerability_roles: 0 });
  const [profileId, setProfileId] = useState(null);

  useEffect(() => {
    getMarketSummary()
      .then((res) => setSummary(res || { rows: 0, unique_roles: 0, unique_cities: 0, vulnerability_roles: 0 }))
      .catch(() => setSummary({ rows: 0, unique_roles: 0, unique_cities: 0, vulnerability_roles: 0 }));
  }, []);

  /* ── Worker Portal layer ── */
  if (activeLayer === "Worker Portal") {
    return (
      <AnimatePresence mode="wait">
        <motion.div
          key="worker"
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -16 }}
          transition={{ duration: 0.4 }}
        >
          <WorkerPortal onProfileReady={setProfileId} />
        </motion.div>
      </AnimatePresence>
    );
  }

  /* ── AI Assistant layer ── */
  if (activeLayer === "AI Assistant") {
    return (
      <AnimatePresence mode="wait">
        <motion.div
          key="chatbot"
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -16 }}
          transition={{ duration: 0.4 }}
        >
          <ChatbotPage profileId={profileId} />
        </motion.div>
      </AnimatePresence>
    );
  }

  return (
    <div className="min-h-screen px-6 pb-12" style={{ paddingTop: 16 }}>
      {/* ── Top bar: Tabs + Filters ── */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        {/* Tabs */}
        <div
          className="flex items-center rounded-xl p-1"
          style={{
            background: "rgba(218,215,205,0.06)",
            border: "1px solid rgba(151,168,122,0.15)",
          }}
        >
          {TABS.map((tab) => {
            const isActive = activeTab === tab;
            return (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className="relative rounded-lg px-5 py-2.5 text-[13px] transition-colors cursor-pointer font-brand"
                style={{
                  fontWeight: isActive ? 700 : 500,
                  color: isActive ? "#121412" : "#6B7265",
                  zIndex: 1,
                }}
                onMouseEnter={(e) => {
                  if (!isActive) {
                    e.currentTarget.style.color = "#dad7cd";
                    e.currentTarget.style.background = "rgba(218,215,205,0.06)";
                  }
                }}
                onMouseLeave={(e) => {
                  if (!isActive) {
                    e.currentTarget.style.color = "#6B7265";
                    e.currentTarget.style.background = "transparent";
                  }
                }}
              >
                {isActive && (
                  <motion.span
                    layoutId="tabIndicator"
                    className="absolute inset-0 rounded-lg"
                    style={{ background: "#97A87A", zIndex: -1 }}
                    transition={{ type: "spring", stiffness: 380, damping: 30 }}
                  />
                )}
                {tab}
              </button>
            );
          })}
        </div>

        {/* Filters */}
        <div className="flex items-center gap-3">
          <GlassSelect
            value={city}
            onValueChange={setCity}
            placeholder="Select City"
            options={CITY_OPTIONS}
          />
          <GlassSelect
            value={timeframe}
            onValueChange={setTimeframe}
            placeholder="Timeframe"
            options={TIME_OPTIONS}
          />
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mt-5">
        {[
          { label: "Total Rows", value: summary.rows },
          { label: "Unique Roles", value: summary.unique_roles },
          { label: "Unique Cities", value: summary.unique_cities },
          { label: "Vulnerability Rows", value: summary.vulnerability_roles },
        ].map((x) => (
          <div key={x.label} className="oasis-dash-card rounded-xl px-4 py-3">
            <p className="font-data text-[11px]" style={{ color: "#6B7265" }}>{x.label}</p>
            <p className="font-brand text-2xl" style={{ color: "#dad7cd", fontWeight: 700 }}>
              {Number(x.value || 0).toLocaleString("en-IN")}
            </p>
          </div>
        ))}
      </div>

      {/* ── Tab content ── */}
      <motion.div
        key={activeTab}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        {renderTab(activeTab, { city, timeframe })}
      </motion.div>
    </div>
  );
};

export default Dashboard;
