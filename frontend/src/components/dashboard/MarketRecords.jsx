import { useEffect, useMemo, useState, useCallback } from "react";
import { motion } from "framer-motion";
import { Database, Search, RefreshCw, Loader2, CheckCircle2, AlertCircle } from "lucide-react";
import { getMarketRecords, triggerScrape } from "../../services/market";

const MarketRecords = ({ filters, onScrapeComplete }) => {
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(1);
  const [payload, setPayload] = useState({ items: [], total: 0, total_pages: 1, meta: { unique_roles: 0, unique_cities: 0 } });
  const [loading, setLoading] = useState(false);

  // Scrape state
  const [scraping, setScraping] = useState(false);
  const [scrapeResult, setScrapeResult] = useState(null); // {success, message, data}

  const fetchRecords = useCallback(() => {
    setLoading(true);
    getMarketRecords({ page, pageSize: 100, city: filters?.city, q: query.trim() })
      .then((res) => {
        setPayload(res || { items: [], total: 0, total_pages: 1, meta: { unique_roles: 0, unique_cities: 0 } });
      })
      .catch(() => {
        setPayload({ items: [], total: 0, total_pages: 1, meta: { unique_roles: 0, unique_cities: 0 } });
      })
      .finally(() => {
        setLoading(false);
      });
  }, [page, filters?.city, query]);

  useEffect(() => {
    fetchRecords();
  }, [fetchRecords]);

  useEffect(() => {
    setPage(1);
  }, [filters?.city, filters?.timeframe]);

  const handleScrape = async () => {
    setScraping(true);
    setScrapeResult(null);
    try {
      const res = await triggerScrape();
      setScrapeResult({
        success: true,
        message: res?.message || "Scrape complete",
        data: res?.data || res,
      });
      // Refresh records + parent summary
      setPage(1);
      fetchRecords();
      if (onScrapeComplete) onScrapeComplete();
    } catch (err) {
      setScrapeResult({
        success: false,
        message: err?.response?.data?.error || err?.message || "Scrape failed",
      });
    } finally {
      setScraping(false);
      // Auto-clear result after 10s
      setTimeout(() => setScrapeResult(null), 10000);
    }
  };

  const rows = useMemo(() => payload.items || [], [payload.items]);

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mt-6 space-y-4">
      <div className="oasis-dash-card rounded-2xl p-5">
        <div className="flex items-center gap-2 mb-4">
          <Database size={16} style={{ color: "#97A87A" }} />
          <h3 className="font-brand text-sm" style={{ color: "#dad7cd", fontWeight: 600 }}>
            Full Job-City Records
          </h3>
          <span className="ml-auto font-data text-[11px] px-2 py-0.5 rounded-full" style={{ color: "#6B7265", background: "rgba(218,215,205,0.08)" }}>
            {payload.total.toLocaleString("en-IN")} rows
          </span>
          <button
            onClick={handleScrape}
            disabled={scraping}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-brand text-xs transition-all cursor-pointer disabled:opacity-60 disabled:cursor-not-allowed"
            style={{
              color: scraping ? "#6B7265" : "#121412",
              background: scraping ? "rgba(151,168,122,0.15)" : "#97A87A",
              fontWeight: 600,
            }}
          >
            {scraping ? (
              <Loader2 size={13} className="animate-spin" />
            ) : (
              <RefreshCw size={13} />
            )}
            {scraping ? "Scraping…" : "Scrape Now"}
          </button>
        </div>

        {/* Scrape result banner */}
        {scrapeResult && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="flex items-start gap-2 rounded-lg px-3 py-2.5 mb-4"
            style={{
              background: scrapeResult.success
                ? "rgba(151,168,122,0.12)"
                : "rgba(217,119,6,0.12)",
              border: `1px solid ${scrapeResult.success ? "rgba(151,168,122,0.3)" : "rgba(217,119,6,0.3)"}`,
            }}
          >
            {scrapeResult.success ? (
              <CheckCircle2 size={15} style={{ color: "#97A87A", marginTop: 1, flexShrink: 0 }} />
            ) : (
              <AlertCircle size={15} style={{ color: "#D97706", marginTop: 1, flexShrink: 0 }} />
            )}
            <div className="flex-1">
              <p className="font-data text-xs" style={{ color: "#dad7cd" }}>
                {scrapeResult.message}
              </p>
              {scrapeResult.success && scrapeResult.data && (
                <p className="font-data text-[11px] mt-0.5" style={{ color: "#6B7265" }}>
                  {scrapeResult.data.jobs_scraped ?? 0} scraped · {scrapeResult.data.jobs_stored ?? 0} stored · {scrapeResult.data.skill_trends_upserted ?? 0} skill trends · {scrapeResult.data.vuln_scores_upserted ?? 0} vuln scores
                </p>
              )}
            </div>
          </motion.div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
          <div className="md:col-span-2 relative">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2" style={{ color: "#6B7265" }} />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search by job role"
              className="w-full pl-9 pr-3 py-2 rounded-lg font-data text-sm"
              style={{ background: "rgba(218,215,205,0.08)", color: "#dad7cd", border: "1px solid rgba(151,168,122,0.2)" }}
            />
          </div>
          <div className="rounded-lg px-3 py-2 flex items-center justify-between" style={{ background: "rgba(151,168,122,0.08)", border: "1px solid rgba(151,168,122,0.2)" }}>
            <span className="font-data text-xs" style={{ color: "#6B7265" }}>Roles/Cities</span>
            <span className="font-data text-sm" style={{ color: "#dad7cd" }}>
              {payload.meta?.unique_roles || 0} / {payload.meta?.unique_cities || 0}
            </span>
          </div>
        </div>

        <div className="grid gap-2 px-3 py-2 rounded-lg" style={{ gridTemplateColumns: "2fr 1.2fr 0.9fr 0.9fr 0.8fr 0.8fr", background: "rgba(151,168,122,0.06)" }}>
          {[
            "Job Role",
            "City",
            "Month",
            "Latest",
            "Total",
            "Risk",
          ].map((h) => (
            <span key={h} className="font-data text-[11px] uppercase tracking-wider" style={{ color: "#6B7265" }}>{h}</span>
          ))}
        </div>

        <div className="mt-2 max-h-[520px] overflow-y-auto custom-scroll space-y-1 pr-1">
          {rows.map((r, i) => (
            <div
              key={`${r.role}-${r.city}-${r.latestMonth}-${i}`}
              className="grid gap-2 px-3 py-2 rounded-lg"
              style={{ gridTemplateColumns: "2fr 1.2fr 0.9fr 0.9fr 0.8fr 0.8fr", background: "rgba(218,215,205,0.02)" }}
            >
              <span className="font-data text-sm" style={{ color: "#dad7cd" }}>{r.role}</span>
              <span className="font-data text-sm" style={{ color: "#97A87A" }}>{r.city}</span>
              <span className="font-data text-sm" style={{ color: "#6B7265" }}>{r.latestMonth || "-"}</span>
              <span className="font-data text-sm" style={{ color: "#dad7cd" }}>{Number(r.latestDemand || 0).toLocaleString("en-IN")}</span>
              <span className="font-data text-sm" style={{ color: "#dad7cd" }}>{Number(r.totalDemand || 0).toLocaleString("en-IN")}</span>
              <span className="font-data text-sm" style={{ color: "#D97706" }}>{Math.round(Number(r.riskScore || 0))}</span>
            </div>
          ))}

          {!loading && rows.length === 0 && (
            <div className="rounded-lg px-4 py-8 text-center" style={{ background: "rgba(218,215,205,0.04)" }}>
              <p className="font-data text-sm" style={{ color: "#6B7265" }}>No records for the current filters.</p>
            </div>
          )}
        </div>

        <div className="mt-4 flex items-center justify-between">
          <p className="font-data text-xs" style={{ color: "#6B7265" }}>
            Page {page} of {payload.total_pages || 1}
          </p>
          <div className="flex items-center gap-2">
            <button
              disabled={page <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              className="px-3 py-1.5 rounded-lg font-data text-xs disabled:opacity-40"
              style={{ color: "#dad7cd", background: "rgba(218,215,205,0.08)", border: "1px solid rgba(151,168,122,0.2)" }}
            >
              Previous
            </button>
            <button
              disabled={page >= (payload.total_pages || 1)}
              onClick={() => setPage((p) => p + 1)}
              className="px-3 py-1.5 rounded-lg font-data text-xs disabled:opacity-40"
              style={{ color: "#dad7cd", background: "rgba(218,215,205,0.08)", border: "1px solid rgba(151,168,122,0.2)" }}
            >
              Next
            </button>
          </div>
        </div>
      </div>
    </motion.div>
  );
};

export default MarketRecords;
