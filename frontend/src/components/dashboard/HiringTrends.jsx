import { motion } from "framer-motion";
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { TrendingUp, Building2, MapPin } from "lucide-react";

/* ═══════════════════════════════════════════════════════════════════════
   DUMMY DATA — Indian job market
   ═══════════════════════════════════════════════════════════════════════ */

// 30-day posting trend
const DAILY_POSTINGS = Array.from({ length: 30 }, (_, i) => {
  const base = 4200 + Math.sin(i / 4) * 800 + Math.random() * 600;
  const d = new Date(2026, 1, 5 + i); // starting Feb 5
  return {
    day: `${d.getDate()} ${d.toLocaleString("default", { month: "short" })}`,
    postings: Math.round(base),
  };
});

// Sector hiring volume
const SECTOR_DATA = [
  { sector: "IT / Software", volume: 18420 },
  { sector: "BPO / KPO", volume: 12830 },
  { sector: "Manufacturing", volume: 9540 },
  { sector: "Retail / E-com", volume: 7680 },
  { sector: "Banking / Fin", volume: 6210 },
];

// Top hiring cities (horizontal bar)
const CITY_DATA = [
  { city: "Bengaluru", jobs: 24500 },
  { city: "Pune", jobs: 16800 },
  { city: "Hyderabad", jobs: 14200 },
  { city: "Mumbai", jobs: 12900 },
  { city: "Indore", jobs: 7400 },
  { city: "Jaipur", jobs: 5900 },
];

/* ═══════════════════════════════════════════════════════════════════════
   SHARED PIECES
   ═══════════════════════════════════════════════════════════════════════ */

const container = {
  initial: { opacity: 0 },
  animate: { opacity: 1, transition: { staggerChildren: 0.12 } },
};
const card = {
  initial: { opacity: 0, y: 24 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.45 } },
};

/* styled tooltip */
function GlassTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="oasis-tooltip">
      <p className="font-brand text-xs mb-1" style={{ color: "#dad7cd" }}>
        {label}
      </p>
      {payload.map((p, i) => (
        <p key={i} className="font-data text-sm font-semibold" style={{ color: "#97A87A" }}>
          {Number(p.value).toLocaleString("en-IN")}
        </p>
      ))}
    </div>
  );
}

/* card header */
function CardHeader({ icon: Icon, title }) {
  return (
    <div className="flex items-center gap-2 mb-4">
      <Icon size={16} style={{ color: "#97A87A" }} />
      <h3 className="font-brand text-sm" style={{ color: "#dad7cd", fontWeight: 600 }}>
        {title}
      </h3>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════
   HIRING TRENDS TAB
   ═══════════════════════════════════════════════════════════════════════ */

const HiringTrends = () => {
  return (
    <motion.div
      variants={container}
      initial="initial"
      animate="animate"
      className="flex flex-col gap-5 mt-6"
    >
      {/* ─── Card 1 — Area chart (full width) ─── */}
      <motion.div variants={card} className="oasis-dash-card rounded-2xl p-5">
        <CardHeader icon={TrendingUp} title="Total Job Postings — Last 30 Days" />
        <div className="h-[280px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={DAILY_POSTINGS} margin={{ top: 8, right: 12, left: -8, bottom: 0 }}>
              <defs>
                <linearGradient id="areaGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#97A87A" stopOpacity={0.35} />
                  <stop offset="100%" stopColor="#97A87A" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(151,168,122,0.1)" />
              <XAxis
                dataKey="day"
                tick={{ fill: "#6B7265", fontSize: 11, fontFamily: "Inter" }}
                axisLine={{ stroke: "rgba(151,168,122,0.15)" }}
                tickLine={false}
                interval={4}
              />
              <YAxis
                tick={{ fill: "#6B7265", fontSize: 11, fontFamily: "Inter" }}
                axisLine={false}
                tickLine={false}
                tickFormatter={(v) => `${(v / 1000).toFixed(1)}k`}
              />
              <Tooltip content={<GlassTooltip />} />
              <Area
                type="monotone"
                dataKey="postings"
                stroke="#97A87A"
                strokeWidth={2}
                fill="url(#areaGradient)"
                dot={false}
                activeDot={{ r: 4, fill: "#97A87A", stroke: "#121412", strokeWidth: 2 }}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </motion.div>

      {/* ─── Bottom row ─── */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {/* Card 2 — Sector bar chart */}
        <motion.div variants={card} className="oasis-dash-card rounded-2xl p-5">
          <CardHeader icon={Building2} title="Hiring Volume by Sector" />
          <div className="h-[260px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={SECTOR_DATA} margin={{ top: 8, right: 12, left: -8, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(151,168,122,0.1)" vertical={false} />
                <XAxis
                  dataKey="sector"
                  tick={{ fill: "#6B7265", fontSize: 10, fontFamily: "Inter" }}
                  axisLine={{ stroke: "rgba(151,168,122,0.15)" }}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fill: "#6B7265", fontSize: 11, fontFamily: "Inter" }}
                  axisLine={false}
                  tickLine={false}
                  tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`}
                />
                <Tooltip content={<GlassTooltip />} cursor={{ fill: "rgba(151,168,122,0.06)" }} />
                <Bar dataKey="volume" radius={[6, 6, 0, 0]} maxBarSize={40}>
                  {SECTOR_DATA.map((_, i) => (
                    <Cell key={i} fill="#dad7cd" fillOpacity={0.7 + i * 0.04} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </motion.div>

        {/* Card 3 — Top hiring cities (horizontal bar) */}
        <motion.div variants={card} className="oasis-dash-card rounded-2xl p-5">
          <CardHeader icon={MapPin} title="Top Hiring Cities" />
          <div className="h-[260px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={CITY_DATA} layout="vertical" margin={{ top: 8, right: 12, left: 10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(151,168,122,0.1)" horizontal={false} />
                <XAxis
                  type="number"
                  tick={{ fill: "#6B7265", fontSize: 11, fontFamily: "Inter" }}
                  axisLine={false}
                  tickLine={false}
                  tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`}
                />
                <YAxis
                  dataKey="city"
                  type="category"
                  tick={{ fill: "#dad7cd", fontSize: 12, fontFamily: "Space Grotesk" }}
                  axisLine={false}
                  tickLine={false}
                  width={85}
                />
                <Tooltip content={<GlassTooltip />} cursor={{ fill: "rgba(151,168,122,0.06)" }} />
                <Bar dataKey="jobs" radius={[0, 6, 6, 0]} maxBarSize={22}>
                  {CITY_DATA.map((_, i) => (
                    <Cell key={i} fill="#97A87A" fillOpacity={1 - i * 0.1} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </motion.div>
      </div>
    </motion.div>
  );
};

export default HiringTrends;
