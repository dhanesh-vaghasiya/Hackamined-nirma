const intensityClass = (value, max) => {
  const ratio = max === 0 ? 0 : value / max;
  if (ratio > 0.8) return "bg-cyan-300 text-slate-950";
  if (ratio > 0.6) return "bg-cyan-400/80 text-slate-950";
  if (ratio > 0.4) return "bg-cyan-500/70 text-slate-100";
  if (ratio > 0.2) return "bg-cyan-700/65 text-slate-100";
  return "bg-cyan-900/60 text-slate-200";
};

export default function Heatmap({ data, labelKey = "city", valueKey = "value", suffix = "" }) {
  const max = Math.max(...data.map((item) => Number(item[valueKey]) || 0), 0);

  return (
    <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 xl:grid-cols-4">
      {data.map((item) => {
        const value = Number(item[valueKey]) || 0;
        return (
          <div
            key={`${item[labelKey]}-${value}`}
            className={`rounded-lg border border-slate-800/80 p-3 transition-transform hover:-translate-y-0.5 ${intensityClass(value, max)}`}
          >
            <p className="text-xs uppercase tracking-wide opacity-80">{item[labelKey]}</p>
            <p className="mt-1 text-xl font-bold">
              {value}
              {suffix}
            </p>
          </div>
        );
      })}
    </div>
  );
}
