import { useEffect, useMemo, useState } from "react";

function useAnimatedNumber(value, duration = 900) {
  const [display, setDisplay] = useState(0);

  useEffect(() => {
    const target = Number(value) || 0;
    const start = performance.now();
    let frame = 0;

    const tick = (now) => {
      const progress = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplay(Math.round(target * eased));
      if (progress < 1) {
        frame = requestAnimationFrame(tick);
      }
    };

    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [value, duration]);

  return display;
}

export default function StatCard({ label, value, suffix = "", prefix = "", tone = "teal" }) {
  const animated = useAnimatedNumber(value);
  const toneClass = useMemo(() => {
    if (tone === "red") return "text-red-300";
    if (tone === "amber") return "text-amber-300";
    return "text-accent";
  }, [tone]);

  return (
    <div className="rounded-xl border border-slate-700/70 bg-cardSoft px-4 py-3 shadow-soft">
      <p className="text-xs uppercase tracking-wider text-slate-400">{label}</p>
      <p className={`mt-2 text-2xl font-bold ${toneClass}`}>
        {prefix}
        {animated.toLocaleString()}
        {suffix}
      </p>
    </div>
  );
}
