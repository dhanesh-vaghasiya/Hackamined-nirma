import { useEffect, useMemo, useState, useRef } from "react";
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
import { getHiringTrends } from "../../services/market";

const container = {
  initial: { opacity: 0 },
  animate: { opacity: 1, transition: { staggerChildren: 0.12 } },
};
const card = {
  initial: { opacity: 0, y: 24 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.45 } },
};

function GlassTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  const fullLabel = payload[0]?.payload?.month || label;
  return (
    <div className="oasis-tooltip">
      <p className="font-brand text-xs mb-1" style={{ color: "#dad7cd" }}>
        {fullLabel}
      </p>
      {payload.map((p, i) => (
        <p key={i} className="font-data text-sm font-semibold" style={{ color: "#97A87A" }}>
          {Number(p.value).toLocaleString("en-IN")}
        </p>
      ))}
    </div>
  );
}

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

/* ── LeetCode-style Bubble Pack ───────────────────────────────────── */
function packCircles(items, width, height) {
  if (!items.length) return [];
  const maxVal = Math.max(...items.map((d) => d.jobs));
  const minR = 28;
  const maxR = Math.min(width, height) * 0.22;

  const circles = items.map((d) => {
    const ratio = d.jobs / (maxVal || 1);
    const r = minR + (maxR - minR) * Math.sqrt(ratio);
    return { ...d, r, x: width / 2, y: height / 2 };
  });

  // Sort largest first for better packing
  circles.sort((a, b) => b.r - a.r);

  // Simple force-directed packing
  const cx = width / 2;
  const cy = height / 2;

  // Spiral placement
  for (let i = 0; i < circles.length; i++) {
    const angle = i * 2.4; // golden angle
    const dist = i * 12;
    circles[i].x = cx + Math.cos(angle) * dist;
    circles[i].y = cy + Math.sin(angle) * dist;
  }

  // Collision resolution iterations
  for (let iter = 0; iter < 120; iter++) {
    for (let i = 0; i < circles.length; i++) {
      for (let j = i + 1; j < circles.length; j++) {
        const a = circles[i];
        const b = circles[j];
        const dx = b.x - a.x;
        const dy = b.y - a.y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;
        const minDist = a.r + b.r + 3;
        if (dist < minDist) {
          const overlap = (minDist - dist) / 2;
          const nx = (dx / dist) * overlap;
          const ny = (dy / dist) * overlap;
          a.x -= nx;
          a.y -= ny;
          b.x += nx;
          b.y += ny;
        }
      }
      // Pull toward center
      const c = circles[i];
      c.x += (cx - c.x) * 0.01;
      c.y += (cy - c.y) * 0.01;
    }
  }

  // Clamp to bounds
  for (const c of circles) {
    c.x = Math.max(c.r + 2, Math.min(width - c.r - 2, c.x));
    c.y = Math.max(c.r + 2, Math.min(height - c.r - 2, c.y));
  }

  return circles;
}

function BubblePack({ data }) {
  const containerRef = useRef(null);
  const [dims, setDims] = useState({ w: 400, h: 320 });
  const [hovered, setHovered] = useState(null);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const obs = new ResizeObserver((entries) => {
      const { width, height } = entries[0].contentRect;
      if (width > 0 && height > 0) setDims({ w: width, h: height });
    });
    obs.observe(el);
    return () => obs.disconnect();
  }, []);

  const circles = useMemo(() => packCircles(data, dims.w, dims.h), [data, dims.w, dims.h]);
  const maxJobs = useMemo(() => Math.max(...data.map((d) => d.jobs), 1), [data]);

  // Build a wave path for the water surface inside a circle
  const waterWavePath = (cx, cy, r, fillRatio) => {
    const waterY = cy + r - fillRatio * 2 * r; // top of water
    const amp = r * 0.045; // wave amplitude
    const left = cx - r;
    const right = cx + r;
    let d = `M ${left},${waterY}`;
    const steps = 20;
    for (let i = 0; i <= steps; i++) {
      const t = i / steps;
      const x = left + t * (right - left);
      const y = waterY + Math.sin(t * Math.PI * 2.5) * amp;
      d += ` L ${x},${y}`;
    }
    d += ` L ${right},${cy + r + 2} L ${left},${cy + r + 2} Z`;
    return d;
  };

  return (
    <div ref={containerRef} className="relative w-full" style={{ height: 320 }}>
      <svg width={dims.w} height={dims.h}>
        <defs>
          {/* Glow gradient */}
          <radialGradient id="bubbleGlow">
            <stop offset="0%" stopColor="#97A87A" stopOpacity={0.5} />
            <stop offset="70%" stopColor="#97A87A" stopOpacity={0.1} />
            <stop offset="100%" stopColor="#97A87A" stopOpacity={0} />
          </radialGradient>
          {/* Water gradient for each bubble */}
          {circles.map((c, i) => (
            <linearGradient key={`wg-${i}`} id={`water-${i}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#97A87A" stopOpacity={0.55} />
              <stop offset="50%" stopColor="#6B8C5A" stopOpacity={0.45} />
              <stop offset="100%" stopColor="#4A6B3A" stopOpacity={0.6} />
            </linearGradient>
          ))}
          {/* Glass specular highlight gradient */}
          <radialGradient id="glassHighlight" cx="35%" cy="25%" r="40%">
            <stop offset="0%" stopColor="#ffffff" stopOpacity={0.18} />
            <stop offset="100%" stopColor="#ffffff" stopOpacity={0} />
          </radialGradient>
          {/* Clip paths for each circle */}
          {circles.map((c, i) => (
            <clipPath key={`cp-${i}`} id={`clip-${i}`}>
              <circle cx={c.x} cy={c.y} r={c.r} />
            </clipPath>
          ))}
        </defs>

        {circles.map((c, i) => {
          const fillRatio = c.jobs / maxJobs;
          const pct = Math.round(fillRatio * 100);
          const isHov = hovered === i;
          return (
            <g
              key={c.city}
              onMouseEnter={() => setHovered(i)}
              onMouseLeave={() => setHovered(null)}
              style={{ cursor: "pointer" }}
            >
              {/* Glow behind */}
              <circle
                cx={c.x} cy={c.y} r={c.r + 10}
                fill="url(#bubbleGlow)"
                opacity={isHov ? 0.6 : 0.15 + fillRatio * 0.2}
                style={{ transition: "opacity 0.3s ease" }}
              />

              {/* Glass bubble background (dark transparent) */}
              <circle
                cx={c.x} cy={c.y} r={c.r}
                fill="rgba(18,20,18,0.4)"
              />

              {/* Water fill — clipped to circle */}
              <path
                d={waterWavePath(c.x, c.y, c.r, fillRatio)}
                fill={`url(#water-${i})`}
                clipPath={`url(#clip-${i})`}
                style={{ transition: "d 0.4s ease" }}
              />

              {/* Water surface highlight line */}
              {fillRatio > 0.05 && (
                <line
                  x1={c.x - c.r * 0.7}
                  y1={c.y + c.r - fillRatio * 2 * c.r}
                  x2={c.x + c.r * 0.7}
                  y2={c.y + c.r - fillRatio * 2 * c.r}
                  stroke="#97A87A"
                  strokeWidth={0.8}
                  strokeOpacity={0.25}
                  clipPath={`url(#clip-${i})`}
                />
              )}

              {/* Glass specular highlight (top-left shine) */}
              <circle
                cx={c.x} cy={c.y} r={c.r}
                fill="url(#glassHighlight)"
              />

              {/* Glass border */}
              <circle
                cx={c.x} cy={c.y} r={c.r}
                fill="none"
                stroke="#97A87A"
                strokeWidth={isHov ? 1.8 : 0.8}
                strokeOpacity={isHov ? 0.75 : 0.2 + fillRatio * 0.2}
                style={{ transition: "all 0.25s ease" }}
              />

              {/* City name */}
              <text
                x={c.x}
                y={c.y - (c.r > 42 ? 7 : 0)}
                textAnchor="middle"
                dominantBaseline="central"
                fill="#dad7cd"
                fontSize={c.r > 50 ? 12 : c.r > 38 ? 10 : 8}
                fontFamily="Space Grotesk"
                fontWeight={600}
                opacity={isHov ? 1 : 0.9}
                style={{ textShadow: "0 1px 3px rgba(0,0,0,0.6)" }}
              >
                {c.city}
              </text>
              {/* Percentage fill */}
              {c.r > 34 && (
                <text
                  x={c.x}
                  y={c.y + 13}
                  textAnchor="middle"
                  dominantBaseline="central"
                  fill="#97A87A"
                  fontSize={10}
                  fontFamily="Inter"
                  fontWeight={500}
                  opacity={0.8}
                  style={{ textShadow: "0 1px 2px rgba(0,0,0,0.5)" }}
                >
                  {pct}%
                </text>
              )}
            </g>
          );
        })}
      </svg>

      {/* Tooltip on hover */}
      {hovered !== null && circles[hovered] && (
        <div
          className="oasis-tooltip pointer-events-none"
          style={{
            position: "absolute",
            left: Math.min(circles[hovered].x + circles[hovered].r + 10, dims.w - 120),
            top: Math.max(circles[hovered].y - 28, 4),
            zIndex: 10,
          }}
        >
          <p className="font-brand text-xs mb-0.5" style={{ color: "#dad7cd" }}>
            {circles[hovered].city}
          </p>
          <p className="font-data text-sm font-semibold" style={{ color: "#97A87A" }}>
            {circles[hovered].jobs.toLocaleString("en-IN")} jobs
          </p>
          <p className="font-data text-xs" style={{ color: "#6B7265" }}>
            {Math.round((circles[hovered].jobs / maxJobs) * 100)}% of top city
          </p>
        </div>
      )}
    </div>
  );
}

const HiringTrends = ({ filters }) => {
  const [data, setData] = useState({ timeline: [], top_city_roles: [] });

  useEffect(() => {
    let mounted = true;
    getHiringTrends({ limit: 120, city: filters?.city || "all-india", timeframe: filters?.timeframe || "1yr" })
      .then((res) => {
        if (mounted) setData(res || { timeline: [], top_city_roles: [] });
      })
      .catch(() => {
        if (mounted) setData({ timeline: [], top_city_roles: [] });
      });
    return () => {
      mounted = false;
    };
  }, [filters?.city, filters?.timeframe]);

  const monthlyPostings = useMemo(() => {
    const MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

    /* Group raw timeline data by "YYYY-MM" key */
    const grouped = new Map();
    for (const point of data.timeline || []) {
      const m = point.month || "";
      const prev = grouped.get(m) || 0;
      grouped.set(m, prev + Number(point.count || 0));
    }

    /* Determine the date range from the data */
    const keys = Array.from(grouped.keys()).filter(Boolean).sort();
    if (keys.length === 0) return [];

    const [startYear, startMonth] = keys[0].split("-").map(Number);
    const [endYear, endMonth] = keys[keys.length - 1].split("-").map(Number);

    /* Build an entry for EVERY month in range, filling gaps with 0 */
    const result = [];
    let year = startYear;
    let month = startMonth;

    while (year < endYear || (year === endYear && month <= endMonth)) {
      const key = `${year}-${String(month).padStart(2, "0")}`;
      const postings = grouped.get(key) || 0;
      result.push({
        month: `${MONTH_NAMES[month - 1]} ${year}`,
        shortMonth: MONTH_NAMES[month - 1],
        postings,
      });
      month++;
      if (month > 12) {
        month = 1;
        year++;
      }
    }

    return result;
  }, [data.timeline]);

  const sectorData = useMemo(() => {
    const grouped = new Map();
    for (const row of data.top_city_roles || []) {
      const sector = (row.job_title || "Unknown").split(" ").slice(0, 2).join(" ");
      const prev = grouped.get(sector) || 0;
      grouped.set(sector, prev + Number(row.latest_demand || 0));
    }
    return Array.from(grouped.entries())
      .map(([sector, volume]) => ({ sector, volume }))
      .sort((a, b) => b.volume - a.volume)
      .slice(0, 6);
  }, [data.top_city_roles]);

  const cityData = useMemo(() => {
    const grouped = new Map();
    for (const row of data.top_city_roles || []) {
      const city = row.location || "Unknown";
      const prev = grouped.get(city) || 0;
      grouped.set(city, prev + Number(row.latest_demand || 0));
    }
    return Array.from(grouped.entries())
      .map(([city, jobs]) => ({ city, jobs }))
      .sort((a, b) => b.jobs - a.jobs)
      .slice(0, 15);
  }, [data.top_city_roles]);

  return (
    <motion.div variants={container} initial="initial" animate="animate" className="flex flex-col gap-5 mt-6">
      <motion.div variants={card} className="oasis-dash-card rounded-2xl p-5">
        <CardHeader icon={TrendingUp} title="Total Job Postings - Market Timeline" />
        <div className="h-[280px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={monthlyPostings} margin={{ top: 8, right: 12, left: -8, bottom: 0 }}>
              <defs>
                <linearGradient id="areaGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#97A87A" stopOpacity={0.35} />
                  <stop offset="100%" stopColor="#97A87A" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(151,168,122,0.1)" />
              <XAxis dataKey="shortMonth" tick={{ fill: "#6B7265", fontSize: 11, fontFamily: "Inter" }} axisLine={{ stroke: "rgba(151,168,122,0.15)" }} tickLine={false} interval={0} angle={monthlyPostings.length > 12 ? -45 : 0} textAnchor={monthlyPostings.length > 12 ? "end" : "middle"} height={monthlyPostings.length > 12 ? 55 : 35} />
              <YAxis tick={{ fill: "#6B7265", fontSize: 11, fontFamily: "Inter" }} axisLine={false} tickLine={false} tickFormatter={(v) => `${(v / 1000).toFixed(1)}k`} />
              <Tooltip content={<GlassTooltip />} labelFormatter={(_, payload) => payload?.[0]?.payload?.month || _} />
              <Area type="monotone" dataKey="postings" stroke="#97A87A" strokeWidth={2} fill="url(#areaGradient)" dot={false} activeDot={{ r: 4, fill: "#97A87A", stroke: "#121412", strokeWidth: 2 }} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </motion.div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        <motion.div variants={card} className="oasis-dash-card rounded-2xl p-5">
          <CardHeader icon={Building2} title="Hiring Volume by Role Cluster" />
          <div className="h-[260px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={sectorData} margin={{ top: 8, right: 12, left: -8, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(151,168,122,0.1)" vertical={false} />
                <XAxis dataKey="sector" tick={{ fill: "#6B7265", fontSize: 10, fontFamily: "Inter" }} axisLine={{ stroke: "rgba(151,168,122,0.15)" }} tickLine={false} />
                <YAxis tick={{ fill: "#6B7265", fontSize: 11, fontFamily: "Inter" }} axisLine={false} tickLine={false} tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} />
                <Tooltip content={<GlassTooltip />} cursor={{ fill: "rgba(151,168,122,0.06)" }} />
                <Bar dataKey="volume" radius={[6, 6, 0, 0]} maxBarSize={40}>
                  {sectorData.map((_, i) => (
                    <Cell key={i} fill="#dad7cd" fillOpacity={0.7 + i * 0.04} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </motion.div>

        <motion.div variants={card} className="oasis-dash-card rounded-2xl p-5">
          <CardHeader icon={MapPin} title="Top Hiring Cities" />
          <BubblePack data={cityData} />
        </motion.div>
      </div>
    </motion.div>
  );
};

export default HiringTrends;
