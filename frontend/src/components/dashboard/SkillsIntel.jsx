import { useEffect, useMemo, useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { TrendingUp, TrendingDown, Radar as RadarIcon, Sparkles, X, Search, Plus, Briefcase } from "lucide-react";
import { getSkillsIntel, getAvailableSkills, getSkillGap, getJobRoles, getJobRoleSkills } from "../../services/market";

const container = {
  initial: { opacity: 0 },
  animate: { opacity: 1, transition: { staggerChildren: 0.12 } },
};
const card = {
  initial: { opacity: 0, y: 24 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.45 } },
};
const listItem = {
  initial: { opacity: 0, x: -16 },
  animate: { opacity: 1, x: 0 },
};

function GlassTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="oasis-tooltip">
      <p className="font-brand text-xs mb-1" style={{ color: "#dad7cd" }}>{label}</p>
      {payload.map((p, i) => (
        <p key={i} className="font-data text-xs" style={{ color: p.color }}>
          {p.name}: <span className="font-semibold">{p.value}%</span>
        </p>
      ))}
    </div>
  );
}

const SkillsIntel = ({ filters }) => {
  const [payload, setPayload] = useState({ rising: [], declining: [], radar: [] });

  // ── Dynamic skill-gap state ──
  const [allSkills, setAllSkills] = useState([]);
  const [selectedSkills, setSelectedSkills] = useState([]);
  const [customRadar, setCustomRadar] = useState(null);
  const [inputValue, setInputValue] = useState("");
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [loadingGap, setLoadingGap] = useState(false);
  const inputRef = useRef(null);
  const suggestionsRef = useRef(null);

  // ── Job role selector state ──
  const [roleQuery, setRoleQuery] = useState("");
  const [roleSuggestions, setRoleSuggestions] = useState([]);
  const [showRoleSuggestions, setShowRoleSuggestions] = useState(false);
  const [selectedRole, setSelectedRole] = useState(null);
  const [loadingRoleSkills, setLoadingRoleSkills] = useState(false);
  const roleInputRef = useRef(null);
  const roleSuggestionsRef = useRef(null);

  useEffect(() => {
    let mounted = true;
    getSkillsIntel({ city: filters?.city || "all-india", timeframe: filters?.timeframe || "1yr" })
      .then((res) => {
        if (mounted) setPayload(res || { rising: [], declining: [], radar: [] });
      })
      .catch(() => {
        if (mounted) setPayload({ rising: [], declining: [], radar: [] });
      });
    getAvailableSkills()
      .then((res) => {
        if (mounted) setAllSkills(res?.skills || []);
      })
      .catch(() => {});
    return () => {
      mounted = false;
    };
  }, [filters?.city, filters?.timeframe]);

  // Close dropdowns on outside click
  useEffect(() => {
    const handler = (e) => {
      if (suggestionsRef.current && !suggestionsRef.current.contains(e.target) && !inputRef.current?.contains(e.target)) {
        setShowSuggestions(false);
      }
      if (roleSuggestionsRef.current && !roleSuggestionsRef.current.contains(e.target) && !roleInputRef.current?.contains(e.target)) {
        setShowRoleSuggestions(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  // Debounced job role search
  useEffect(() => {
    if (!roleQuery.trim() || roleQuery.length < 2) {
      setRoleSuggestions([]);
      return;
    }
    const timer = setTimeout(() => {
      getJobRoles({ q: roleQuery, limit: 15 })
        .then((res) => setRoleSuggestions(res?.roles || []))
        .catch(() => setRoleSuggestions([]));
    }, 300);
    return () => clearTimeout(timer);
  }, [roleQuery]);

  const handleSelectRole = async (role) => {
    setSelectedRole(role);
    setRoleQuery(role);
    setShowRoleSuggestions(false);
    setLoadingRoleSkills(true);
    try {
      const res = await getJobRoleSkills(role);
      const skills = res?.skills || [];
      setSelectedSkills(skills);
      // Auto-generate the gap map
      if (skills.length > 0) {
        const gapRes = await getSkillGap({ skills, city: filters?.city || "all-india" });
        setCustomRadar(gapRes?.radar || []);
      }
    } catch {
      setSelectedSkills([]);
    } finally {
      setLoadingRoleSkills(false);
    }
  };

  const clearRole = () => {
    setSelectedRole(null);
    setRoleQuery("");
    setRoleSuggestions([]);
  };

  const filteredSuggestions = useMemo(() => {
    if (!inputValue.trim()) return allSkills.filter((s) => !selectedSkills.includes(s)).slice(0, 12);
    const q = inputValue.toLowerCase();
    return allSkills.filter((s) => s.toLowerCase().includes(q) && !selectedSkills.includes(s)).slice(0, 12);
  }, [inputValue, allSkills, selectedSkills]);

  const addSkill = (skill) => {
    if (!selectedSkills.includes(skill)) {
      setSelectedSkills((prev) => [...prev, skill]);
    }
    setInputValue("");
    inputRef.current?.focus();
  };

  const removeSkill = (skill) => {
    setSelectedSkills((prev) => prev.filter((s) => s !== skill));
  };

  const handleGenerate = async () => {
    if (selectedSkills.length === 0) return;
    setLoadingGap(true);
    try {
      const res = await getSkillGap({ skills: selectedSkills, city: filters?.city || "all-india" });
      setCustomRadar(res?.radar || []);
    } catch {
      setCustomRadar([]);
    } finally {
      setLoadingGap(false);
    }
  };

  const handleReset = () => {
    setSelectedSkills([]);
    setCustomRadar(null);
    setInputValue("");
    setSelectedRole(null);
    setRoleQuery("");
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && filteredSuggestions.length > 0) {
      e.preventDefault();
      addSkill(filteredSuggestions[0]);
    }
  };

  const risingSkills = useMemo(
    () =>
      (payload.rising || []).slice(0, 5).map((x) => ({
        skill: x.skill,
        change: `${x.percent_change > 0 ? "+" : ""}${Math.round(x.percent_change)}%`,
        hot: x.percent_change > 80,
      })),
    [payload.rising]
  );

  const decliningSkills = useMemo(
    () =>
      (payload.declining || []).slice(0, 4).map((x) => ({
        skill: x.skill,
        change: `${Math.round(x.percent_change)}%`,
      })),
    [payload.declining]
  );

  const radarData = (payload.radar || []).slice(0, 5);

  return (
    <motion.div variants={container} initial="initial" animate="animate" className="grid grid-cols-1 lg:grid-cols-2 gap-5 mt-6">
      <motion.div variants={card} className="oasis-dash-card rounded-2xl p-5">
        <div className="flex items-center gap-2 mb-5">
          <Sparkles size={16} style={{ color: "#97A87A" }} />
          <h3 className="font-brand text-sm" style={{ color: "#dad7cd", fontWeight: 600 }}>
            Rising vs. Declining Skills
          </h3>
        </div>

        <p className="font-data text-[11px] uppercase tracking-wider mb-3" style={{ color: "#97A87A" }}>
          Trending Up
        </p>
        <motion.ul className="space-y-2 mb-6" variants={container} initial="initial" animate="animate">
          {risingSkills.map((s, i) => (
            <motion.li key={s.skill} variants={listItem} transition={{ delay: i * 0.06 }} className="flex items-center justify-between rounded-lg px-3 py-2.5" style={{ background: "rgba(151,168,122,0.08)", border: s.hot ? "1px solid rgba(151,168,122,0.3)" : "1px solid transparent" }}>
              <div className="flex items-center gap-2">
                <TrendingUp size={14} style={{ color: "#97A87A" }} />
                <span className="font-data text-sm" style={{ color: "#dad7cd" }}>{s.skill}</span>
                {s.hot && <span className="text-[10px] font-brand px-1.5 py-0.5 rounded-full" style={{ background: "rgba(151,168,122,0.2)", color: "#97A87A", fontWeight: 700 }}>HOT</span>}
              </div>
              <span className="font-data text-sm font-semibold" style={{ color: "#97A87A" }}>{s.change}</span>
            </motion.li>
          ))}
        </motion.ul>

        <p className="font-data text-[11px] uppercase tracking-wider mb-3" style={{ color: "#DC2626" }}>
          Trending Down
        </p>
        <motion.ul className="space-y-2" variants={container} initial="initial" animate="animate">
          {decliningSkills.map((s, i) => (
            <motion.li key={s.skill} variants={listItem} transition={{ delay: i * 0.06 + 0.3 }} className="flex items-center justify-between rounded-lg px-3 py-2.5" style={{ background: "rgba(220,38,38,0.06)" }}>
              <div className="flex items-center gap-2">
                <TrendingDown size={14} style={{ color: "#DC2626", opacity: 0.7 }} />
                <span className="font-data text-sm" style={{ color: "#6B7265" }}>{s.skill}</span>
              </div>
              <span className="font-data text-sm font-semibold" style={{ color: "#DC2626", opacity: 0.75 }}>{s.change}</span>
            </motion.li>
          ))}
        </motion.ul>
      </motion.div>

      <motion.div variants={card} className="oasis-dash-card rounded-2xl p-5">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <RadarIcon size={16} style={{ color: "#97A87A" }} />
            <h3 className="font-brand text-sm" style={{ color: "#dad7cd", fontWeight: 600 }}>
              The Skill Gap Map
            </h3>
          </div>
          {customRadar !== null && (
            <button onClick={handleReset} className="font-data text-[11px] px-2 py-1 rounded" style={{ color: "#97A87A", background: "rgba(151,168,122,0.1)", border: "1px solid rgba(151,168,122,0.2)" }}>
              Reset to Default
            </button>
          )}
        </div>
        <p className="font-data text-xs mb-3" style={{ color: "#6B7265" }}>
          {customRadar !== null ? "Current demand vs. existing workforce supply — indexed 0-100" : "Employer demand vs. available workforce supply - indexed 0-100"}
        </p>

        {/* ── Job Role Selector ── */}
        <div className="relative mb-3">
          <div className="flex items-center gap-2">
            <Briefcase size={14} style={{ color: "#6B7265" }} />
            <p className="font-data text-[11px] uppercase tracking-wider" style={{ color: "#6B7265" }}>
              Select a job role to auto-detect skills
            </p>
          </div>
          <div className="relative mt-1.5">
            <div className="flex gap-2 items-center">
              <div className="relative flex-1">
                <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2" style={{ color: "#6B7265" }} />
                <input
                  ref={roleInputRef}
                  type="text"
                  value={roleQuery}
                  onChange={(e) => { setRoleQuery(e.target.value); setShowRoleSuggestions(true); setSelectedRole(null); }}
                  onFocus={() => setShowRoleSuggestions(true)}
                  placeholder="Search job role (e.g. data engineer, frontend developer)..."
                  className="w-full pl-8 pr-3 py-2 rounded-lg text-xs font-data outline-none"
                  style={{ background: "rgba(151,168,122,0.06)", border: selectedRole ? "1px solid rgba(151,168,122,0.4)" : "1px solid rgba(151,168,122,0.15)", color: "#dad7cd" }}
                />
              </div>
              {selectedRole && (
                <button onClick={clearRole} className="p-1.5 rounded" style={{ color: "#6B7265" }}>
                  <X size={14} />
                </button>
              )}
            </div>
            {loadingRoleSkills && (
              <p className="font-data text-[11px] mt-1" style={{ color: "#97A87A" }}>Extracting skills from job descriptions...</p>
            )}
            {showRoleSuggestions && roleSuggestions.length > 0 && (
              <div ref={roleSuggestionsRef} className="absolute z-30 left-0 right-0 mt-1 rounded-lg py-1 max-h-48 overflow-y-auto" style={{ background: "#1a1f14", border: "1px solid rgba(151,168,122,0.2)", boxShadow: "0 8px 24px rgba(0,0,0,0.4)" }}>
                {roleSuggestions.map((r) => (
                  <button key={r.role} onClick={() => handleSelectRole(r.role)} className="w-full text-left px-3 py-2 text-xs font-data flex items-center justify-between hover:bg-[rgba(151,168,122,0.1)] transition-colors" style={{ color: "#dad7cd" }}>
                    <span className="flex items-center gap-2">
                      <Briefcase size={12} style={{ color: "#97A87A" }} /> {r.role}
                    </span>
                    <span className="font-data text-[10px]" style={{ color: "#6B7265" }}>{r.count} jobs</span>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="flex items-center gap-3 mb-3">
          <div className="flex-1 h-px" style={{ background: "rgba(151,168,122,0.1)" }} />
          <span className="font-data text-[10px] uppercase" style={{ color: "#6B7265" }}>or add skills manually</span>
          <div className="flex-1 h-px" style={{ background: "rgba(151,168,122,0.1)" }} />
        </div>

        {/* ── Skill Input Area ── */}
        <div className="mb-4">
          <div className="flex flex-wrap gap-1.5 mb-2">
            <AnimatePresence>
              {selectedSkills.map((sk) => (
                <motion.span key={sk} initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.8 }} className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-data" style={{ background: "rgba(151,168,122,0.15)", color: "#dad7cd", border: "1px solid rgba(151,168,122,0.25)" }}>
                  {sk}
                  <X size={12} className="cursor-pointer opacity-60 hover:opacity-100" style={{ color: "#DC2626" }} onClick={() => removeSkill(sk)} />
                </motion.span>
              ))}
            </AnimatePresence>
          </div>
          <div className="relative">
            <div className="flex gap-2">
              <div className="relative flex-1">
                <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2" style={{ color: "#6B7265" }} />
                <input
                  ref={inputRef}
                  type="text"
                  value={inputValue}
                  onChange={(e) => { setInputValue(e.target.value); setShowSuggestions(true); }}
                  onFocus={() => setShowSuggestions(true)}
                  onKeyDown={handleKeyDown}
                  placeholder="Type a skill (e.g. python, react, aws)..."
                  className="w-full pl-8 pr-3 py-2 rounded-lg text-xs font-data outline-none"
                  style={{ background: "rgba(151,168,122,0.06)", border: "1px solid rgba(151,168,122,0.15)", color: "#dad7cd" }}
                />
              </div>
              <button
                onClick={handleGenerate}
                disabled={selectedSkills.length === 0 || loadingGap}
                className="px-3 py-2 rounded-lg text-xs font-brand font-semibold transition-all"
                style={{
                  background: selectedSkills.length > 0 ? "rgba(151,168,122,0.2)" : "rgba(151,168,122,0.05)",
                  color: selectedSkills.length > 0 ? "#97A87A" : "#6B7265",
                  border: "1px solid rgba(151,168,122,0.2)",
                  cursor: selectedSkills.length > 0 ? "pointer" : "not-allowed",
                }}
              >
                {loadingGap ? "..." : "Generate Map"}
              </button>
            </div>
            {/* Suggestions dropdown */}
            {showSuggestions && filteredSuggestions.length > 0 && (
              <div ref={suggestionsRef} className="absolute z-20 left-0 right-0 mt-1 rounded-lg py-1 max-h-40 overflow-y-auto" style={{ background: "#1a1f14", border: "1px solid rgba(151,168,122,0.2)", boxShadow: "0 8px 24px rgba(0,0,0,0.4)" }}>
                {filteredSuggestions.map((sk) => (
                  <button key={sk} onClick={() => { addSkill(sk); setShowSuggestions(false); }} className="w-full text-left px-3 py-1.5 text-xs font-data flex items-center gap-2 hover:bg-[rgba(151,168,122,0.1)] transition-colors" style={{ color: "#dad7cd" }}>
                    <Plus size={12} style={{ color: "#97A87A" }} /> {sk}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="h-[320px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <RadarChart cx="50%" cy="50%" outerRadius="75%" data={customRadar !== null ? customRadar : radarData}>
              <PolarGrid stroke="rgba(151,168,122,0.15)" />
              <PolarAngleAxis dataKey="skill" tick={{ fill: "#dad7cd", fontSize: 12, fontFamily: "Space Grotesk" }} />
              <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fill: "#6B7265", fontSize: 10 }} axisLine={false} />
              <Tooltip content={<GlassTooltip />} />
              <Radar name="Employer Demand" dataKey="demand" stroke="#97A87A" fill="#97A87A" fillOpacity={0.25} strokeWidth={2} />
              <Radar name="Workforce Supply" dataKey="supply" stroke="#dad7cd" fill="#dad7cd" fillOpacity={0.1} strokeWidth={2} strokeDasharray="4 4" />
              <Legend wrapperStyle={{ fontFamily: "Inter", fontSize: 12 }} formatter={(val) => <span style={{ color: "#6B7265" }}>{val}</span>} />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </motion.div>
    </motion.div>
  );
};

export default SkillsIntel;
