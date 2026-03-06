import { useEffect, useState } from "react";
import { motion, useMotionValue, useTransform, animate } from "framer-motion";

/* ═══════════════════════════════════════════════════════════════════════
   HELPERS
   ═══════════════════════════════════════════════════════════════════════ */

function riskColor(score) {
  if (score > 75) return "#DC2626";
  if (score >= 40) return "#D97706";
  return "#16A34A";
}

function riskLabel(score) {
  if (score > 75) return "HIGH";
  if (score >= 40) return "MEDIUM";
  return "LOW";
}

function riskGlow(score) {
  if (score > 75) return "rgba(220,38,38,0.25)";
  if (score >= 40) return "rgba(217,119,6,0.2)";
  return "rgba(22,163,74,0.2)";
}

/* ═══════════════════════════════════════════════════════════════════════
   SVG GAUGE — supports compact mode via `size` prop
   ═══════════════════════════════════════════════════════════════════════ */

const RiskScoreGauge = ({ score = 0, riskLevel, size = 180, reason }) => {
  const STROKE = size >= 150 ? 10 : 7;
  const RADIUS = (size - STROKE) / 2;
  const CIRCUMFERENCE = 2 * Math.PI * RADIUS;
  const fontNum = size >= 150 ? 42 : 28;
  const fontSub = size >= 150 ? 11 : 9;

  const [displayScore, setDisplayScore] = useState(0);
  const progress = useMotionValue(0);
  const dashOffset = useTransform(progress, (v) => CIRCUMFERENCE * (1 - v));

  useEffect(() => {
    progress.set(0);
    setDisplayScore(0);

    const controls = animate(progress, score / 100, {
      duration: 1.6,
      ease: [0.33, 1, 0.68, 1],
    });

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
  }, [score]);

  const color = riskColor(score);
  const label = riskLevel || riskLabel(score);
  const glow = riskGlow(score);

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.85 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5, delay: 0.15 }}
      className="flex flex-col items-center gap-2"
    >
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="-rotate-90">
          <circle cx={size / 2} cy={size / 2} r={RADIUS} fill="none" stroke="rgba(218,215,205,0.08)" strokeWidth={STROKE} />
          <motion.circle cx={size / 2} cy={size / 2} r={RADIUS} fill="none" stroke={color} strokeWidth={STROKE} strokeLinecap="round" strokeDasharray={CIRCUMFERENCE} style={{ strokeDashoffset: dashOffset }} filter={`drop-shadow(0 0 8px ${glow})`} />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="font-brand leading-none" style={{ fontSize: fontNum, fontWeight: 800, color }}>{displayScore}</span>
          <span className="font-data mt-0.5" style={{ fontSize: fontSub, color: "#6B7265" }}>/ 100</span>
        </div>
      </div>

      <span className="font-brand text-xs px-2.5 py-0.5 rounded-full" style={{ fontWeight: 700, color, background: `${color}15`, border: `1px solid ${color}30` }}>{label}</span>

      {reason && (
        <p className="font-data text-[10px] text-center leading-relaxed mt-0.5 max-w-[200px]" style={{ color: "#6B7265" }}>{reason}</p>
      )}
    </motion.div>
  );
};

export default RiskScoreGauge;
