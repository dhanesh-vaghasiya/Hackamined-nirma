import React, { useEffect, useState, useMemo, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Building2,
  MapPin,
  Briefcase,
  ChevronDown,
  ChevronUp,
  Users,
  Loader2,
  Crosshair,
  Zap,
  TrendingUp,
  ArrowLeft,
  Code2,
  Database,
  Shield,
  Palette,
  Megaphone,
  Landmark,
  UserCheck,
  Headphones,
  Target,
  Wrench,
  GraduationCap,
  Heart,
  Layers,
} from "lucide-react";
import GlassCard from "../ui/GlassCard";
import IndiaMap from "./IndiaMap";
import { getEmployerCitySkills, getEmployerSectorHiring } from "../../services/market";

const TABS = ["City-wise Skills", "Sector Hiring"];

/* ── Sector color palette ── */
const SECTOR_COLORS = {
  "IT & Software": "#97A87A",
  "Data & AI": "#7AA8A0",
  "Cybersecurity": "#A87A7A",
  "Design & Creative": "#A89A7A",
  "Marketing & Sales": "#D4A853",
  "Finance & Accounting": "#7A8BA8",
  "HR & Operations": "#A87AA8",
  "Customer Support & BPO": "#7AA87A",
  "Management & Consulting": "#8A97A8",
  "Engineering (Non-IT)": "#A8A07A",
  "Education & Training": "#7A98A8",
  "Healthcare": "#A87A90",
  Other: "#6B7265",
};

/* ── Sector icon mapping ── */
const SECTOR_ICONS = {
  "IT & Software": Code2,
  "Data & AI": Database,
  "Cybersecurity": Shield,
  "Design & Creative": Palette,
  "Marketing & Sales": Megaphone,
  "Finance & Accounting": Landmark,
  "HR & Operations": UserCheck,
  "Customer Support & BPO": Headphones,
  "Management & Consulting": Target,
  "Engineering (Non-IT)": Wrench,
  "Education & Training": GraduationCap,
  "Healthcare": Heart,
  Other: Layers,
};

/* ── Small skill pill ── */
function SkillPill({ skill, count, rank }) {
  const isTop3 = rank < 3;
  return (
    <div
      className="inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-data transition-all"
      style={{
        background: isTop3 ? "rgba(151,168,122,0.18)" : "rgba(151,168,122,0.08)",
        border: `1px solid ${isTop3 ? "rgba(151,168,122,0.35)" : "rgba(151,168,122,0.15)"}`,
        color: "#dad7cd",
      }}
    >
      <span>{skill}</span>
      <span
        className="rounded-full px-1.5 py-0.5 text-[10px] font-brand"
        style={{
          background: isTop3 ? "rgba(151,168,122,0.35)" : "rgba(151,168,122,0.2)",
          color: "#97A87A",
        }}
      >
        {count.toLocaleString("en-IN")}
      </span>
    </div>
  );
}

/* ── City detail panel (right side) ── */
function CityDetailPanel({ data, onBack }) {
  const [showAll, setShowAll] = useState(false);
  if (!data) return null;

  const visibleSkills = showAll ? data.skills : data.skills.slice(0, 8);
  const topSkill = data.skills[0];
  const totalMentions = data.total_jobs;

  return (
    <motion.div
      key={data.city}
      initial={{ opacity: 0, x: 30 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 30 }}
      transition={{ duration: 0.4, ease: "easeOut" }}
      className="flex flex-col h-full"
    >
      {/* Back button */}
      <button
        onClick={onBack}
        className="flex items-center gap-1.5 text-xs font-data mb-3 cursor-pointer transition-colors self-start"
        style={{ color: "#97A87A" }}
        onMouseEnter={(e) => (e.currentTarget.style.color = "#dad7cd")}
        onMouseLeave={(e) => (e.currentTarget.style.color = "#97A87A")}
      >
        <ArrowLeft size={13} /> Back to overview
      </button>

      {/* City header */}
      <div
        className="rounded-xl p-4 mb-3"
        style={{
          background: "rgba(151,168,122,0.08)",
          border: "1px solid rgba(151,168,122,0.2)",
        }}
      >
        <div className="flex items-center gap-2.5 mb-2">
          <div
            className="flex items-center justify-center w-9 h-9 rounded-lg"
            style={{ background: "rgba(151,168,122,0.2)" }}
          >
            <MapPin size={18} color="#97A87A" />
          </div>
          <div>
            <h3 className="font-brand text-lg" style={{ color: "#FFFFFF", fontWeight: 700 }}>
              {data.city}
            </h3>
            <p className="font-data text-[11px]" style={{ color: "#8a8d85" }}>
              {totalMentions.toLocaleString("en-IN")} skill mentions across profiles
            </p>
          </div>
        </div>

        {/* Quick stats */}
        <div className="grid grid-cols-2 gap-2 mt-3">
          <div className="rounded-lg px-3 py-2" style={{ background: "rgba(18,20,18,0.5)" }}>
            <p className="font-data text-[10px]" style={{ color: "#6B7265" }}>
              <Zap size={10} className="inline mr-1" />Top Skill
            </p>
            <p className="font-brand text-sm" style={{ color: "#97A87A", fontWeight: 600 }}>
              {topSkill?.skill || "—"}
            </p>
          </div>
          <div className="rounded-lg px-3 py-2" style={{ background: "rgba(18,20,18,0.5)" }}>
            <p className="font-data text-[10px]" style={{ color: "#6B7265" }}>
              <TrendingUp size={10} className="inline mr-1" />Skills Tracked
            </p>
            <p className="font-brand text-sm" style={{ color: "#dad7cd", fontWeight: 600 }}>
              {data.skills.length}
            </p>
          </div>
        </div>
      </div>

      {/* Skills list */}
      <div className="flex-1 overflow-y-auto pr-1" style={{ scrollbarWidth: "thin" }}>
        <p className="font-brand text-[11px] mb-2" style={{ color: "#6B7265" }}>
          Available Skills
        </p>
        <div className="flex flex-wrap gap-2">
          {visibleSkills.map((s, i) => (
            <SkillPill key={s.skill} skill={s.skill} count={s.count} rank={i} />
          ))}
        </div>

        {data.skills.length > 8 && (
          <button
            onClick={() => setShowAll(!showAll)}
            className="flex items-center gap-1 mt-3 text-xs cursor-pointer font-data transition-colors"
            style={{ color: "#97A87A" }}
            onMouseEnter={(e) => (e.currentTarget.style.color = "#dad7cd")}
            onMouseLeave={(e) => (e.currentTarget.style.color = "#97A87A")}
          >
            {showAll ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
            {showAll ? "Show less" : `+${data.skills.length - 8} more skills`}
          </button>
        )}

        {/* Skill bars (top 6) */}
        <div className="mt-4 space-y-2">
          <p className="font-brand text-[11px] mb-1" style={{ color: "#6B7265" }}>
            Skill Distribution
          </p>
          {data.skills.slice(0, 6).map((s, i) => {
            const maxCount = data.skills[0]?.count || 1;
            const pct = Math.max(8, (s.count / maxCount) * 100);
            return (
              <div key={s.skill} className="flex items-center gap-2">
                <span
                  className="font-data text-[11px] w-28 truncate text-right"
                  style={{ color: "#dad7cd" }}
                >
                  {s.skill}
                </span>
                <div className="flex-1 h-2 rounded-full" style={{ background: "rgba(218,215,205,0.06)" }}>
                  <motion.div
                    className="h-2 rounded-full"
                    style={{ background: i < 3 ? "#97A87A" : "rgba(151,168,122,0.5)" }}
                    initial={{ width: 0 }}
                    animate={{ width: `${pct}%` }}
                    transition={{ duration: 0.6, delay: i * 0.08 }}
                  />
                </div>
                <span className="font-brand text-[10px] w-10 text-right" style={{ color: "#6B7265" }}>
                  {s.count.toLocaleString("en-IN")}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </motion.div>
  );
}

/* ── City list sidebar (when no city selected) ── */
function CityListPanel({ cities, onCitySelect }) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="flex flex-col h-full"
    >
      <p className="font-brand text-xs mb-3" style={{ color: "#8a8d85" }}>
        <Crosshair size={11} className="inline mr-1" />
        Click a city on the map or select below
      </p>

      <div className="flex-1 overflow-y-auto pr-1 space-y-1.5" style={{ scrollbarWidth: "thin" }}>
        {cities.map((c, i) => (
          <motion.button
            key={c.city}
            onClick={() => onCitySelect(c.city)}
            className="w-full flex items-center justify-between rounded-lg px-3 py-2.5 cursor-pointer transition-all text-left"
            style={{
              background: "rgba(218,215,205,0.04)",
              border: "1px solid rgba(151,168,122,0.08)",
            }}
            whileHover={{
              backgroundColor: "rgba(151,168,122,0.1)",
              borderColor: "rgba(151,168,122,0.25)",
            }}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.02 }}
          >
            <div className="flex items-center gap-2">
              <div
                className="w-2 h-2 rounded-full"
                style={{
                  background: "#97A87A",
                  opacity: Math.max(0.3, c.total_jobs / (cities[0]?.total_jobs || 1)),
                }}
              />
              <span className="font-data text-sm" style={{ color: "#dad7cd" }}>
                {c.city}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className="font-data text-[11px]" style={{ color: "#6B7265" }}>
                {c.skills?.length || 0} skills
              </span>
              <span className="font-brand text-xs" style={{ color: "#97A87A" }}>
                {c.total_jobs.toLocaleString("en-IN")}
              </span>
            </div>
          </motion.button>
        ))}
      </div>
    </motion.div>
  );
}

const MAX_VISIBLE_SECTORS = 7;

/* ── Sector Constellation (radial hub-and-spoke) ── */
function SectorConstellation({ sectors }) {
  const [selected, setSelected] = useState(null);
  const containerRef = useRef(null);
  const [radius, setRadius] = useState(280);
  const NODE_SIZE = 56;

  /* Show only top sectors by job count */
  const visibleSectors = useMemo(
    () =>
      [...sectors]
        .sort((a, b) => b.total_jobs - a.total_jobs)
        .slice(0, MAX_VISIBLE_SECTORS),
    [sectors]
  );
  const count = visibleSectors.length;

  const totalSectors = visibleSectors.length;
  const totalJobs = visibleSectors.reduce((a, s) => a + s.total_jobs, 0);

  /* Dynamic radius based on container size */
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const updateRadius = () => {
      const { width, height } = el.getBoundingClientRect();
      const minDim = Math.min(width, height);
      setRadius(Math.max(200, minDim * 0.42));
    };
    updateRadius();
    const ro = new ResizeObserver(updateRadius);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  const nodes = useMemo(
    () =>
      visibleSectors.map((sec, i) => {
        const angle = (2 * Math.PI * i) / count - Math.PI / 2;
        return {
          ...sec,
          x: Math.cos(angle) * radius,
          y: Math.sin(angle) * radius,
          angleDeg: (360 * i) / count - 90,
          color: SECTOR_COLORS[sec.sector] || "#6B7265",
          Icon: SECTOR_ICONS[sec.sector] || Building2,
        };
      }),
    [visibleSectors, count, radius]
  );

  /* Derive selectedData from nodes so it includes color & Icon */
  const selectedData = useMemo(
    () => (selected ? nodes.find((s) => s.sector === selected) || null : null),
    [selected, nodes]
  );

  return (
    <div
      ref={containerRef}
      className="relative w-full overflow-hidden rounded-2xl"
      style={{
        height: "calc(100vh - 140px)",
        minHeight: 560,
        background: "rgba(18,20,18,0.4)",
        border: "1px solid rgba(151,168,122,0.1)",
      }}
    >
      {/* Connecting dashed lines */}
      {nodes.map((node, i) => {
        const isActive = selected === node.sector;
        return (
          <motion.div
            key={`line-${node.sector}`}
            style={{
              position: "absolute",
              left: "50%",
              top: "50%",
              height: 0,
              borderTop: `${isActive ? 2 : 1}px dashed ${node.color}`,
              transformOrigin: "0 center",
              transform: `rotate(${node.angleDeg}deg)`,
              opacity: isActive ? 0.65 : 0.2,
              transition: "opacity 0.4s ease",
            }}
            initial={{ width: 0 }}
            animate={{ width: radius - NODE_SIZE / 2 }}
            transition={{ duration: 0.5, delay: i * 0.04, ease: "easeOut" }}
          />
        );
      })}

      {/* Center Hub */}
      <div
        style={{
          position: "absolute",
          left: "50%",
          top: "50%",
          transform: "translate(-50%, -50%)",
          zIndex: 10,
        }}
      >
        <AnimatePresence mode="wait">
          {selectedData ? (
            <motion.div
              key="detail"
              initial={{ scale: 0.85, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.85, opacity: 0 }}
              transition={{ duration: 0.25 }}
              className="rounded-xl p-3.5 cursor-pointer"
              style={{
                width: 210,
                maxHeight: 300,
                background: "rgba(18,20,18,0.92)",
                border: `1.5px solid ${selectedData.color || "#97A87A"}44`,
                backdropFilter: "blur(24px)",
                boxShadow: `0 0 40px ${selectedData.color || "#97A87A"}22`,
                overflowY: "auto",
                scrollbarWidth: "thin",
              }}
              onClick={() => setSelected(null)}
            >
              <div className="flex items-center gap-2 mb-2">
                <div
                  className="flex items-center justify-center w-8 h-8 rounded-lg"
                  style={{ background: `${selectedData.color}22` }}
                >
                  {(() => {
                    const Icon = SECTOR_ICONS[selectedData.sector] || Building2;
                    return <Icon size={16} color={selectedData.color} />;
                  })()}
                </div>
                <div>
                  <h3 className="font-brand text-sm" style={{ color: "#FFFFFF", fontWeight: 700 }}>
                    {selectedData.sector}
                  </h3>
                  <p className="font-data text-[10px]" style={{ color: "#a0a39a" }}>
                    {selectedData.total_jobs.toLocaleString("en-IN")} postings
                  </p>
                </div>
              </div>

              <p
                className="font-brand text-[11px] mb-1 flex items-center gap-1"
                style={{ color: selectedData.color }}
              >
                <Briefcase size={11} /> Top Roles
              </p>
              <div className="space-y-0.5 mb-2">
                {selectedData.top_roles.map((r, ri) => (
                  <motion.div
                    key={r.role}
                    className="flex items-center justify-between text-xs font-data"
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: ri * 0.05 }}
                  >
                    <span style={{ color: "#dad7cd" }} className="truncate mr-2">
                      {r.role}
                    </span>
                    <span
                      style={{ color: selectedData.color }}
                      className="font-brand shrink-0 text-[11px]"
                    >
                      {r.count.toLocaleString("en-IN")}
                    </span>
                  </motion.div>
                ))}
              </div>

              <p
                className="font-brand text-[11px] mb-1 flex items-center gap-1"
                style={{ color: selectedData.color }}
              >
                <MapPin size={11} /> Top Cities
              </p>
              <div className="space-y-0.5">
                {selectedData.top_cities.map((c, ci) => (
                  <motion.div
                    key={c.city}
                    className="flex items-center justify-between text-xs font-data"
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: ci * 0.05 + 0.15 }}
                  >
                    <span style={{ color: "#dad7cd" }} className="truncate mr-2">
                      {c.city}
                    </span>
                    <span
                      style={{ color: selectedData.color }}
                      className="font-brand shrink-0 text-[11px]"
                    >
                      {c.count.toLocaleString("en-IN")}
                    </span>
                  </motion.div>
                ))}
              </div>

              <p
                className="font-data text-[9px] text-center mt-2"
                style={{ color: "#8a8d85" }}
              >
                Click to deselect
              </p>
            </motion.div>
          ) : (
            <motion.div
              key="hub"
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              exit={{ scale: 0.85, opacity: 0 }}
              transition={{ type: "spring", stiffness: 200, damping: 20 }}
              className="flex flex-col items-center justify-center rounded-full"
              style={{
                width: 120,
                height: 120,
                background: "rgba(18,20,18,0.85)",
                border: "1.5px solid rgba(151,168,122,0.2)",
                backdropFilter: "blur(20px)",
                animation: "sectorHubPulse 3s ease-in-out infinite",
              }}
            >
              <Building2 size={26} color="#97A87A" style={{ opacity: 0.7 }} />
              <p className="font-brand text-lg mt-1" style={{ color: "#dad7cd", fontWeight: 700 }}>
                {totalSectors}
              </p>
              <p className="font-data text-[10px]" style={{ color: "#8a8d85" }}>
                sectors &middot; {totalJobs.toLocaleString("en-IN")} jobs
              </p>
              <p className="font-data text-[10px] mt-1" style={{ color: "#97A87Acc" }}>
                Select one
              </p>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Sector Nodes */}
      {nodes.map((node, i) => {
        const isSelected = selected === node.sector;
        const Icon = node.Icon;
        return (
          <div
            key={node.sector}
            className="absolute"
            style={{
              left: `calc(50% + ${node.x}px)`,
              top: `calc(50% + ${node.y}px)`,
              transform: "translate(-50%, -50%)",
              zIndex: isSelected ? 20 : 5,
            }}
          >
            <motion.div
              className="flex flex-col items-center cursor-pointer"
              initial={{ opacity: 0, scale: 0 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{
                type: "spring",
                stiffness: 260,
                damping: 20,
                delay: 0.08 + i * 0.05,
              }}
              onClick={() => setSelected(isSelected ? null : node.sector)}
              whileHover={{ scale: 1.12 }}
              whileTap={{ scale: 0.95 }}
            >
              <motion.div
                className="flex items-center justify-center rounded-full"
                style={{
                  width: NODE_SIZE,
                  height: NODE_SIZE,
                  background: isSelected ? `${node.color}30` : `${node.color}15`,
                  border: `2px solid ${isSelected ? node.color : `${node.color}55`}`,
                  transition: "background 0.3s, border-color 0.3s",
                }}
                animate={
                  isSelected
                    ? {
                        boxShadow: [
                          `0 0 15px ${node.color}33, 0 0 30px ${node.color}18`,
                          `0 0 25px ${node.color}55, 0 0 45px ${node.color}28`,
                          `0 0 15px ${node.color}33, 0 0 30px ${node.color}18`,
                        ],
                      }
                    : { boxShadow: `0 0 10px ${node.color}11` }
                }
                transition={
                  isSelected
                    ? { duration: 2, repeat: Infinity, ease: "easeInOut" }
                    : { duration: 0.3 }
                }
              >
                <Icon size={20} color={node.color} />
              </motion.div>
              <span
                className="font-brand text-[11px] mt-1.5 text-center leading-tight"
                style={{
                  color: isSelected ? "#dad7cd" : "#b0b3aa",
                  fontWeight: isSelected ? 600 : 500,
                  maxWidth: 90,
                  transition: "color 0.3s",
                }}
              >
                {node.sector}
              </span>
              <span
                className="font-data text-[10px]"
                style={{
                  color: isSelected ? node.color : `${node.color}aa`,
                  transition: "color 0.3s",
                }}
              >
                {node.total_jobs.toLocaleString("en-IN")}
              </span>
            </motion.div>
          </div>
        );
      })}

      {/* Hub pulse keyframes */}
      <style>{`
        @keyframes sectorHubPulse {
          0%, 100% { box-shadow: 0 0 30px rgba(151,168,122,0.12); }
          50% { box-shadow: 0 0 50px rgba(151,168,122,0.25), 0 0 80px rgba(151,168,122,0.08); }
        }
      `}</style>
    </div>
  );
}

/* ── Main EmployersView component ── */
export default function EmployersView() {
  const [activeTab, setActiveTab] = useState("City-wise Skills");
  const [citySkills, setCitySkills] = useState([]);
  const [sectors, setSectors] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedCity, setSelectedCity] = useState(null);

  useEffect(() => {
    setLoading(true);
    if (activeTab === "City-wise Skills") {
      getEmployerCitySkills({ city: "all-india" })
        .then((res) => setCitySkills(res?.cities || []))
        .catch(() => setCitySkills([]))
        .finally(() => setLoading(false));
    } else {
      getEmployerSectorHiring({ city: "all-india" })
        .then((res) => setSectors(res?.sectors || []))
        .catch(() => setSectors([]))
        .finally(() => setLoading(false));
    }
  }, [activeTab]);

  const maxSectorJobs = sectors.length > 0 ? sectors[0].total_jobs : 0;

  /* Stats */
  const totalSkillCities = citySkills.length;
  const totalSectors = sectors.filter((s) => s.sector !== "Other").length;
  const totalSectorJobs = sectors.reduce((a, s) => a + s.total_jobs, 0);

  /* Find detail data for selected city */
  const selectedCityData = useMemo(() => {
    if (!selectedCity) return null;
    return citySkills.find(
      (c) => c.city.toLowerCase() === selectedCity.toLowerCase()
    ) || null;
  }, [selectedCity, citySkills]);

  const handleCitySelect = (cityName) => {
    setSelectedCity(cityName);
  };

  return (
    <div className={`min-h-screen pb-4 ${activeTab === "Sector Hiring" ? "px-3" : "px-6 pb-12"}`} style={{ paddingTop: 16 }}>
      {/* ── Header bar ── */}
      <div className={`flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 ${activeTab === "Sector Hiring" ? "mb-2" : "mb-4"}`}>
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
                onClick={() => { setActiveTab(tab); setSelectedCity(null); }}
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
                    layoutId="empTabPill"
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
      </div>

      {/* ── Content ── */}
      {loading ? (
        <div className="flex items-center justify-center py-24">
          <Loader2 size={28} color="#97A87A" className="animate-spin" />
        </div>
      ) : (
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.4 }}
          >
            {activeTab === "City-wise Skills" ? (
              /* ═══════════ MAP + DETAIL PANEL LAYOUT ═══════════ */
              <div className="flex gap-4" style={{ height: "calc(100vh - 160px)" }}>
                {/* Left: India Map */}
                <div
                  className="flex-1 rounded-2xl relative overflow-hidden"
                  style={{
                    background: "rgba(18,20,18,0.6)",
                    border: "1px solid rgba(151,168,122,0.12)",
                  }}
                >
                  {/* Floating stats on map */}
                  <div className="absolute top-4 left-4 z-10">
                    <div
                      className="rounded-xl px-4 py-2.5"
                      style={{
                        background: "rgba(18,20,18,0.85)",
                        backdropFilter: "blur(12px)",
                        border: "1px solid rgba(151,168,122,0.15)",
                      }}
                    >
                      <p className="font-data text-[10px]" style={{ color: "#6B7265" }}>
                        <MapPin size={10} className="inline mr-1" />Cities with Data
                      </p>
                      <p className="font-brand text-xl" style={{ color: "#dad7cd", fontWeight: 700 }}>
                        {totalSkillCities}
                      </p>
                    </div>
                  </div>

                  {selectedCity && (
                    <div className="absolute top-4 left-1/2 -translate-x-1/2 z-10">
                      <motion.div
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="rounded-full px-4 py-1.5 flex items-center gap-2"
                        style={{
                          background: "rgba(151,168,122,0.15)",
                          border: "1px solid rgba(151,168,122,0.3)",
                          backdropFilter: "blur(12px)",
                        }}
                      >
                        <div className="w-2 h-2 rounded-full" style={{ background: "#97A87A" }} />
                        <span className="font-brand text-sm" style={{ color: "#FFFFFF", fontWeight: 600 }}>
                          {selectedCity}
                        </span>
                      </motion.div>
                    </div>
                  )}

                  {/* Map */}
                  <div className="w-full h-full p-1">
                    <IndiaMap
                      cityData={citySkills}
                      selectedCity={selectedCity}
                      onCitySelect={handleCitySelect}
                    />
                  </div>
                </div>

                {/* Right: Detail Panel */}
                <div
                  className="w-[360px] shrink-0 rounded-2xl p-4 flex flex-col overflow-hidden"
                  style={{
                    background: "rgba(26,29,26,0.6)",
                    border: "1px solid rgba(151,168,122,0.12)",
                    backdropFilter: "blur(16px)",
                  }}
                >
                  <AnimatePresence mode="wait">
                    {selectedCityData ? (
                      <CityDetailPanel
                        key={selectedCityData.city}
                        data={selectedCityData}
                        onBack={() => setSelectedCity(null)}
                      />
                    ) : (
                      <CityListPanel
                        key="list"
                        cities={citySkills}
                        onCitySelect={handleCitySelect}
                      />
                    )}
                  </AnimatePresence>
                </div>
              </div>
            ) : /* ═══════════ SECTOR HIRING TAB ═══════════ */
            sectors.length > 0 ? (
              <SectorConstellation sectors={sectors} />
            ) : (
              <div className="text-center py-20">
                <Building2 size={40} color="#6B7265" className="mx-auto mb-3 opacity-50" />
                <p className="font-data text-sm" style={{ color: "#6B7265" }}>
                  No sector data available.
                </p>
              </div>
            )}
          </motion.div>
        </AnimatePresence>
      )}
    </div>
  );
}
