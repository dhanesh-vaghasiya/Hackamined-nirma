const SkeletonBlock = ({ className = "" }) => (
  <div className={`animate-pulse rounded-md bg-slate-700/40 ${className}`} />
);

export default function ChartCard({ title, subtitle, children, loading, error, accent = false, extra }) {
  return (
    <section
      className={`rounded-2xl border border-slate-700/60 bg-cardBg p-4 shadow-soft transition-all duration-300 ${
        accent ? "shadow-glow" : ""
      }`}
    >
      <div className="mb-3 flex flex-wrap items-start justify-between gap-2">
        <div>
          <h3 className="text-sm font-semibold uppercase tracking-wide text-accent">{title}</h3>
          {subtitle ? <p className="mt-1 text-xs text-slate-400">{subtitle}</p> : null}
        </div>
        {extra}
      </div>

      {loading ? (
        <div className="space-y-2">
          <SkeletonBlock className="h-5 w-1/3" />
          <SkeletonBlock className="h-44 w-full" />
          <SkeletonBlock className="h-4 w-2/3" />
        </div>
      ) : error ? (
        <div className="rounded-lg border border-red-400/40 bg-red-500/10 p-4 text-sm text-red-200">
          {error}
        </div>
      ) : (
        children
      )}
    </section>
  );
}
