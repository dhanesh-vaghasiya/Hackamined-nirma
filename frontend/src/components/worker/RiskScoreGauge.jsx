import { useEffect, useState, useRef } from "react";
import { motion, useMotionValue, useTransform, animate } from "framer-motion";
import { TrendingUp } from "lucide-react";

/* ═══════════════════════════════════════════════════════════════════════
   HELPERS
   ═══════════════════════════════════════════════════════════════════════ */

function riskColor(score) {
  if (score > 75) return "#DC2626";
  if (score >= 40) return "#D97706";
  return "#16A34A";
}

function riskLabel(score) {
  if (score > 75) return "High Risk";
  if (score >= 40) return "Medium Risk";
  return "Low Risk";
}

function riskGlow(score) {
  if (score > 75) return "rgba(220,38,38,0.25)";
  if (score >= 40) return "rgba(217,119,6,0.2)";
  return "rgba(22,163,74,0.2)";
}

/* ═══════════════════════════════════════════════════════════════════════
   SVG GAUGE
   ═══════════════════════════════════════════════════════════════════════ */

const SIZE = 180;
const STROKE = 10;
const RADIUS = (SIZE - STROKE) / 2;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

const RiskScoreGauge = ({ score = 74 }) => {
  const [displayScore, setDisplayScore] = useState(0);
  const progress = useMotionValue(0);
  const dashOffset = useTransform(progress, (v) => CIRCUMFERENCE * (1 - v));
  const hasAnimated = useRef(false);

  useEffect(() => {
    if (hasAnimated.current) return;
    hasAnimated.current = true;

    // Animate the SVG ring
    const controls = animate(progress, score / 100, {
      duration: 1.6,
      ease: [0.33, 1, 0.68, 1], // custom ease-out
    });

    // Animate the counter
    const counter = { value: 0 };
    const tween = animate(counter, { value: score }, {
      duration: 1.6,
      ease: [0.33, 1, 0.68, 1],
      onUpdate: () => setDisplayScore(Math.round(counter.value)),
    });

    return () => {
      controls.stop();
      tween.stop();
    };
  }, [score, progress]);

  const color = riskColor(score);
  const label = riskLabel(score);
  const glow = riskGlow(score);

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.85 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5, delay: 0.15 }}
      className="flex flex-col items-center gap-4"
    >
      {/* Gauge */}
      <div className="relative" style={{ width: SIZE, height: SIZE }}>
        <svg width={SIZE} height={SIZE} className="-rotate-90">
          {/* Track */}
          <circle
            cx={SIZE / 2}
            cy={SIZE / 2}
            r={RADIUS}
            fill="none"
            stroke="rgba(218,215,205,0.08)"
            strokeWidth={STROKE}
          />
          {/* Progress arc */}
          <motion.circle
            cx={SIZE / 2}
            cy={SIZE / 2}
            r={RADIUS}
            fill="none"
            stroke={color}
            strokeWidth={STROKE}
            strokeLinecap="round"
            strokeDasharray={CIRCUMFERENCE}
            style={{ strokeDashoffset: dashOffset }}
            filter={`drop-shadow(0 0 8px ${glow})`}
          />
        </svg>

        {/* Center text */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span
            className="font-brand leading-none"
            style={{ fontSize: 42, fontWeight: 800, color }}
          >
            {displayScore}
          </span>
          <span className="font-data text-[11px] mt-0.5" style={{ color: "#6B7265" }}>
            / 100
          </span>
        </div>
      </div>

      {/* Label + trend */}
      <div className="flex flex-col items-center gap-1.5">
        <span
          className="font-brand text-sm px-3 py-1 rounded-full"
          style={{
            fontWeight: 700,
            color,
            background: `${color}15`,
            border: `1px solid ${color}30`,
          }}
        >
          {label}
        </span>

        <div className="flex items-center gap-1">
          <TrendingUp size={13} style={{ color: "#DC2626" }} />
          <span className="font-data text-xs" style={{ color: "#DC2626" }}>
            ↑ +8 vs 30 days ago
          </span>
        </div>
      </div>
    </motion.div>
  );
};

export default RiskScoreGauge;
