import { useEffect, useMemo, useState } from "react";
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

  const dailyPostings = useMemo(() => {
    const grouped = new Map();
    for (const point of data.timeline || []) {
      const month = point.month || "";
      const prev = grouped.get(month) || 0;
      grouped.set(month, prev + Number(point.count || 0));
    }
    return Array.from(grouped.entries())
      .map(([day, postings]) => ({ day, postings }))
      .slice(-30);
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
      .slice(0, 8);
  }, [data.top_city_roles]);

  return (
    <motion.div variants={container} initial="initial" animate="animate" className="flex flex-col gap-5 mt-6">
      <motion.div variants={card} className="oasis-dash-card rounded-2xl p-5">
        <CardHeader icon={TrendingUp} title="Total Job Postings - Market Timeline" />
        <div className="h-[280px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={dailyPostings} margin={{ top: 8, right: 12, left: -8, bottom: 0 }}>
              <defs>
                <linearGradient id="areaGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#97A87A" stopOpacity={0.35} />
                  <stop offset="100%" stopColor="#97A87A" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(151,168,122,0.1)" />
              <XAxis dataKey="day" tick={{ fill: "#6B7265", fontSize: 11, fontFamily: "Inter" }} axisLine={{ stroke: "rgba(151,168,122,0.15)" }} tickLine={false} interval={4} />
              <YAxis tick={{ fill: "#6B7265", fontSize: 11, fontFamily: "Inter" }} axisLine={false} tickLine={false} tickFormatter={(v) => `${(v / 1000).toFixed(1)}k`} />
              <Tooltip content={<GlassTooltip />} />
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
          <div className="h-[260px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={cityData} layout="vertical" margin={{ top: 8, right: 12, left: 10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(151,168,122,0.1)" horizontal={false} />
                <XAxis type="number" tick={{ fill: "#6B7265", fontSize: 11, fontFamily: "Inter" }} axisLine={false} tickLine={false} tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} />
                <YAxis dataKey="city" type="category" tick={{ fill: "#dad7cd", fontSize: 12, fontFamily: "Space Grotesk" }} axisLine={false} tickLine={false} width={92} />
                <Tooltip content={<GlassTooltip />} cursor={{ fill: "rgba(151,168,122,0.06)" }} />
                <Bar dataKey="jobs" radius={[0, 6, 6, 0]} maxBarSize={22}>
                  {cityData.map((_, i) => (
                    <Cell key={i} fill="#97A87A" fillOpacity={1 - i * 0.08} />
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
