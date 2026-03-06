import { motion } from "framer-motion";
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
import { TrendingUp, TrendingDown, Radar as RadarIcon, Sparkles } from "lucide-react";

/* ═══════════════════════════════════════════════════════════════════════
   DUMMY DATA
   ═══════════════════════════════════════════════════════════════════════ */

const RISING_SKILLS = [
  { skill: "Generative AI / Prompt Engineering", change: "+184%", hot: true },
  { skill: "Cloud Architecture (AWS / Azure)", change: "+96%", hot: false },
  { skill: "Data Engineering & MLOps", change: "+72%", hot: false },
  { skill: "Cybersecurity / Zero-Trust", change: "+58%", hot: false },
  { skill: "Full-Stack (React + Node)", change: "+41%", hot: false },
];

const DECLINING_SKILLS = [
  { skill: "Manual Data Entry", change: "−62%" },
  { skill: "Basic Voice Support (L1)", change: "−47%" },
  { skill: "Routine Bookkeeping", change: "−38%" },
  { skill: "Legacy COBOL Maintenance", change: "−31%" },
];

const RADAR_DATA = [
  { skill: "GenAI", demand: 92, supply: 34 },
  { skill: "Cloud", demand: 85, supply: 61 },
  { skill: "Data Eng", demand: 78, supply: 48 },
  { skill: "Cyber", demand: 74, supply: 52 },
  { skill: "DevOps", demand: 69, supply: 58 },
];

/* ═══════════════════════════════════════════════════════════════════════
   SHARED
   ═══════════════════════════════════════════════════════════════════════ */

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
      <p className="font-brand text-xs mb-1" style={{ color: "#dad7cd" }}>
        {label}
      </p>
      {payload.map((p, i) => (
        <p key={i} className="font-data text-xs" style={{ color: p.color }}>
          {p.name}: <span className="font-semibold">{p.value}%</span>
        </p>
      ))}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════
   SKILLS INTEL TAB
   ═══════════════════════════════════════════════════════════════════════ */

const SkillsIntel = () => {
  return (
    <motion.div
      variants={container}
      initial="initial"
      animate="animate"
      className="grid grid-cols-1 lg:grid-cols-2 gap-5 mt-6"
    >
      {/* ─── Card 1 — Rising vs Declining Skills ─── */}
      <motion.div variants={card} className="oasis-dash-card rounded-2xl p-5">
        <div className="flex items-center gap-2 mb-5">
          <Sparkles size={16} style={{ color: "#97A87A" }} />
          <h3 className="font-brand text-sm" style={{ color: "#dad7cd", fontWeight: 600 }}>
            Rising vs. Declining Skills
          </h3>
        </div>

        {/* Rising */}
        <p className="font-data text-[11px] uppercase tracking-wider mb-3" style={{ color: "#97A87A" }}>
          Trending Up
        </p>
        <motion.ul
          className="space-y-2 mb-6"
          variants={container}
          initial="initial"
          animate="animate"
        >
          {RISING_SKILLS.map((s, i) => (
            <motion.li
              key={s.skill}
              variants={listItem}
              transition={{ delay: i * 0.06 }}
              className="flex items-center justify-between rounded-lg px-3 py-2.5"
              style={{
                background: "rgba(151,168,122,0.08)",
                border: s.hot ? "1px solid rgba(151,168,122,0.3)" : "1px solid transparent",
              }}
            >
              <div className="flex items-center gap-2">
                <TrendingUp size={14} style={{ color: "#97A87A" }} />
                <span className="font-data text-sm" style={{ color: "#dad7cd" }}>
                  {s.skill}
                </span>
                {s.hot && (
                  <span
                    className="text-[10px] font-brand px-1.5 py-0.5 rounded-full"
                    style={{ background: "rgba(151,168,122,0.2)", color: "#97A87A", fontWeight: 700 }}
                  >
                    HOT
                  </span>
                )}
              </div>
              <span className="font-data text-sm font-semibold" style={{ color: "#97A87A" }}>
                {s.change}
              </span>
            </motion.li>
          ))}
        </motion.ul>

        {/* Declining */}
        <p className="font-data text-[11px] uppercase tracking-wider mb-3" style={{ color: "#DC2626" }}>
          Trending Down
        </p>
        <motion.ul
          className="space-y-2"
          variants={container}
          initial="initial"
          animate="animate"
        >
          {DECLINING_SKILLS.map((s, i) => (
            <motion.li
              key={s.skill}
              variants={listItem}
              transition={{ delay: i * 0.06 + 0.3 }}
              className="flex items-center justify-between rounded-lg px-3 py-2.5"
              style={{ background: "rgba(220,38,38,0.06)" }}
            >
              <div className="flex items-center gap-2">
                <TrendingDown size={14} style={{ color: "#DC2626", opacity: 0.7 }} />
                <span className="font-data text-sm" style={{ color: "#6B7265" }}>
                  {s.skill}
                </span>
              </div>
              <span className="font-data text-sm font-semibold" style={{ color: "#DC2626", opacity: 0.75 }}>
                {s.change}
              </span>
            </motion.li>
          ))}
        </motion.ul>
      </motion.div>

      {/* ─── Card 2 — Skill Gap Radar ─── */}
      <motion.div variants={card} className="oasis-dash-card rounded-2xl p-5">
        <div className="flex items-center gap-2 mb-4">
          <RadarIcon size={16} style={{ color: "#97A87A" }} />
          <h3 className="font-brand text-sm" style={{ color: "#dad7cd", fontWeight: 600 }}>
            The Skill Gap Map
          </h3>
        </div>
        <p className="font-data text-xs mb-4" style={{ color: "#6B7265" }}>
          Employer demand vs. available workforce supply — indexed 0-100
        </p>

        <div className="h-[380px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <RadarChart cx="50%" cy="50%" outerRadius="75%" data={RADAR_DATA}>
              <PolarGrid stroke="rgba(151,168,122,0.15)" />
              <PolarAngleAxis
                dataKey="skill"
                tick={{ fill: "#dad7cd", fontSize: 12, fontFamily: "Space Grotesk" }}
              />
              <PolarRadiusAxis
                angle={90}
                domain={[0, 100]}
                tick={{ fill: "#6B7265", fontSize: 10 }}
                axisLine={false}
              />
              <Tooltip content={<GlassTooltip />} />
              <Radar
                name="Employer Demand"
                dataKey="demand"
                stroke="#97A87A"
                fill="#97A87A"
                fillOpacity={0.25}
                strokeWidth={2}
              />
              <Radar
                name="Workforce Supply"
                dataKey="supply"
                stroke="#dad7cd"
                fill="#dad7cd"
                fillOpacity={0.1}
                strokeWidth={2}
                strokeDasharray="4 4"
              />
              <Legend
                wrapperStyle={{ fontFamily: "Inter", fontSize: 12 }}
                formatter={(val) => <span style={{ color: "#6B7265" }}>{val}</span>}
              />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </motion.div>
    </motion.div>
  );
};

export default SkillsIntel;
