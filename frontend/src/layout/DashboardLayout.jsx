export default function DashboardLayout({ tabs, activeTab, onTabChange, children, isLive = true }) {
  return (
    <div className="min-h-screen bg-brandBg px-3 py-4 text-slate-100 sm:px-6 lg:px-10">
      <nav className="mb-6 flex flex-col gap-3 rounded-2xl border border-slate-700/60 bg-cardBg/85 p-4 shadow-soft md:flex-row md:items-center md:justify-between">
        <div className="flex items-center gap-3">
          <div className="grid h-10 w-10 place-items-center rounded-lg bg-gradient-to-br from-cyan-400 to-cyan-600 text-lg font-bold text-slate-950">
            SM
          </div>
          <div>
            <p className="text-base font-bold tracking-wide">Skills Mirage</p>
            <div className="flex items-center gap-2 text-xs text-slate-400">
              <span className={`inline-flex h-2.5 w-2.5 rounded-full bg-emerald-400 ${isLive ? "animate-pulseDot" : ""}`} />
              <span>{isLive ? "Live Data Stream" : "Data Stream Paused"}</span>
            </div>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {tabs.map((tab) => (
            <button
              type="button"
              key={tab.key}
              onClick={() => onTabChange(tab.key)}
              className={`rounded-lg px-3 py-2 text-sm transition-all ${
                activeTab === tab.key
                  ? "bg-cyan-500/20 text-accent shadow-glow"
                  : "bg-slate-800/70 text-slate-300 hover:bg-slate-700"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </nav>

      <header className="mb-6 animate-fadeInUp">
        <h1 className="text-2xl font-bold text-cyan-100 sm:text-3xl">Skills Mirage - Job Market Intelligence</h1>
        <p className="mt-1 text-sm text-slate-300">Three Tabs. All Live. All Data-Derived.</p>
        <p className="mt-1 text-sm text-slate-400">
          Real scraping from Naukri + LinkedIn. Data refreshes live during demo.
        </p>
      </header>

      <main className="animate-fadeInUp">{children}</main>
    </div>
  );
}
