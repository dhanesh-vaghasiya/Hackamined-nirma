import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { Database, Search } from "lucide-react";
import { getMarketRecords } from "../../services/market";

const MarketRecords = ({ filters }) => {
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(1);
  const [payload, setPayload] = useState({ items: [], total: 0, total_pages: 1, meta: { unique_roles: 0, unique_cities: 0 } });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    getMarketRecords({ page, pageSize: 100, city: filters?.city, q: query.trim() })
      .then((res) => {
        if (mounted) setPayload(res || { items: [], total: 0, total_pages: 1, meta: { unique_roles: 0, unique_cities: 0 } });
      })
      .catch(() => {
        if (mounted) setPayload({ items: [], total: 0, total_pages: 1, meta: { unique_roles: 0, unique_cities: 0 } });
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });
    return () => {
      mounted = false;
    };
  }, [page, filters?.city, filters?.timeframe, query]);

  useEffect(() => {
    setPage(1);
  }, [filters?.city, filters?.timeframe]);

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
        </div>

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
