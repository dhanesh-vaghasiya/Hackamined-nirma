import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowRight, Radar, ShieldCheck, TrendingUp } from "lucide-react";
import { getMarketSummary } from "../services/market";

const features = [
  {
    icon: TrendingUp,
    title: "Market Intelligence",
    desc: "Live hiring trends, city demand, and emerging role visibility from your backend data pipeline.",
  },
  {
    icon: ShieldCheck,
    title: "AI Vulnerability Signals",
    desc: "Role-level automation risk scoring with transparent factors and confidence-aware outputs.",
  },
  {
    icon: Radar,
    title: "Worker Career Analysis",
    desc: "Profile analysis, risk gauge, and practical next-role guidance for targeted upskilling.",
  },
];

const Landing = () => {
  const [summary, setSummary] = useState(null);

  useEffect(() => {
    let mounted = true;
    getMarketSummary()
      .then((res) => {
        if (mounted) setSummary(res);
      })
      .catch(() => {
        if (mounted) setSummary(null);
      });
    return () => {
      mounted = false;
    };
  }, []);

  return (
    <div className="min-h-screen px-6 py-10">
      <div className="mx-auto max-w-6xl">
        <motion.header
          initial={{ opacity: 0, y: 14 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center justify-between mb-14"
        >
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: "rgba(151,168,122,0.18)", border: "1px solid rgba(151,168,122,0.35)" }}>
              <span className="font-brand" style={{ color: "#97A87A", fontWeight: 800 }}>O</span>
            </div>
            <div>
              <p className="font-brand text-xl" style={{ color: "#dad7cd", fontWeight: 700 }}>OASIS</p>
              <p className="font-data text-xs" style={{ color: "#6B7265" }}>Workforce Intelligence Platform</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Link to="/login" className="px-4 py-2 rounded-lg font-data text-sm" style={{ color: "#dad7cd", border: "1px solid rgba(151,168,122,0.28)", background: "rgba(218,215,205,0.08)" }}>Sign In</Link>
            <Link to="/register" className="px-4 py-2 rounded-lg font-brand text-sm" style={{ color: "#121412", background: "#97A87A", fontWeight: 700 }}>Start Free</Link>
          </div>
        </motion.header>

        <motion.section
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.08 }}
          className="glass-card rounded-3xl p-8 md:p-12 mb-10"
        >
          <p className="font-data text-xs uppercase tracking-[0.18em] mb-4" style={{ color: "#97A87A" }}>Real-time Career Risk Intelligence</p>
          <h1 className="font-brand text-4xl md:text-6xl leading-tight mb-5" style={{ color: "#dad7cd", fontWeight: 700 }}>
            See Role Risk.
            <br />
            Plan Better Moves.
          </h1>
          <p className="max-w-2xl font-data text-base md:text-lg mb-8" style={{ color: "#6B7265" }}>
            OASIS turns live market data into clear decisions for workers and teams: hiring demand, vulnerability scores, and personalized next-step direction.
          </p>
          <div className="flex items-center gap-4">
            <Link
              to="/register"
              className="inline-flex items-center gap-2 px-5 py-3 rounded-xl font-brand text-sm"
              style={{ color: "#121412", background: "#97A87A", fontWeight: 700 }}
            >
              Launch Dashboard <ArrowRight size={16} />
            </Link>
            <Link
              to="/dashboard"
              className="px-5 py-3 rounded-xl font-data text-sm"
              style={{ color: "#dad7cd", background: "rgba(218,215,205,0.08)", border: "1px solid rgba(151,168,122,0.25)" }}
            >
              Continue as Logged User
            </Link>
          </div>
        </motion.section>

        <section className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {features.map((feature, idx) => {
            const Icon = feature.icon;
            return (
              <motion.article
                key={feature.title}
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.15 + idx * 0.08 }}
                className="glass-card p-5 rounded-2xl"
              >
                <div className="w-10 h-10 rounded-lg flex items-center justify-center mb-4" style={{ background: "rgba(151,168,122,0.12)", border: "1px solid rgba(151,168,122,0.22)" }}>
                  <Icon size={18} style={{ color: "#97A87A" }} />
                </div>
                <h3 className="font-brand text-lg mb-2" style={{ color: "#dad7cd", fontWeight: 600 }}>{feature.title}</h3>
                <p className="font-data text-sm leading-relaxed" style={{ color: "#6B7265" }}>{feature.desc}</p>
              </motion.article>
            );
          })}
        </section>

        <section className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-8">
          {[
            { label: "Jobs Indexed", value: summary?.rows ?? "--" },
            { label: "Unique Roles", value: summary?.unique_roles ?? "--" },
            { label: "Cities Covered", value: summary?.unique_cities ?? "--" },
            { label: "AI Risk Roles", value: summary?.vulnerability_roles ?? "--" },
          ].map((stat) => (
            <div key={stat.label} className="glass-card rounded-xl p-4">
              <p className="font-data text-xs mb-1" style={{ color: "#6B7265" }}>{stat.label}</p>
              <p className="font-brand text-2xl" style={{ color: "#dad7cd", fontWeight: 700 }}>{stat.value}</p>
            </div>
          ))}
        </section>
      </div>
    </div>
  );
};

export default Landing;
