import { useMemo } from "react";
import ChartCard from "../components/ChartCard";
import DataTable from "../components/DataTable";
import Heatmap from "../charts/Heatmap";
import TrendLineChart from "../charts/LineChart";
import StatCard from "../components/StatCard";
import useFetch from "../hooks/useFetch";

const getTone = (category) => {
  if (category === "Critical") return "bg-red-500/20 text-red-200";
  if (category === "High") return "bg-amber-500/20 text-amber-200";
  if (category === "Medium") return "bg-orange-500/20 text-orange-200";
  return "bg-emerald-500/20 text-emerald-200";
};

export default function AIRiskIndex() {
  const riskState = useFetch("/api/ai-risk");
  const cityRiskState = useFetch("/api/ai-risk/cities");
  const trendState = useFetch("/api/ai-risk/trends");

  const averageRisk = useMemo(() => {
    const rows = riskState.data || [];
    if (!rows.length) return 0;
    const total = rows.reduce((sum, row) => sum + (row.ai_risk_score || 0), 0);
    return Math.round(total / rows.length);
  }, [riskState.data]);

  const criticalRoles = useMemo(
    () => (riskState.data || []).filter((row) => row.risk_category === "Critical").length,
    [riskState.data]
  );

  const columns = [
    { key: "role", label: "Job Role" },
    { key: "city", label: "City" },
    { key: "ai_risk_score", label: "AI Risk Score" },
    {
      key: "risk_category",
      label: "Risk Category",
      render: (value) => <span className={`rounded px-2 py-1 text-xs ${getTone(value)}`}>{value}</span>,
    },
    { key: "hiring_trend", label: "Hiring Trend" },
  ];

  return (
    <div className="space-y-4">
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Average AI Risk" value={averageRisk} suffix="/100" tone="amber" />
        <StatCard label="Critical Roles" value={criticalRoles} tone="red" />
        <StatCard label="Cities Assessed" value={(cityRiskState.data || []).length} />
        <StatCard label="Signals Used" value={3} />
      </div>

      <div className="grid gap-4 xl:grid-cols-3">
        <div className="xl:col-span-2 space-y-4">
          <ChartCard
            title="AI Risk Heatmap by City"
            subtitle="Geographic displacement pressure"
            loading={cityRiskState.loading}
            error={cityRiskState.error && !cityRiskState.data ? cityRiskState.error : ""}
            accent
          >
            <Heatmap data={(cityRiskState.data || []).map((row) => ({ city: row.city, value: row.risk }))} />
          </ChartCard>

          <ChartCard
            title="Risk Trend Chart"
            subtitle="Is AI vulnerability increasing over time?"
            loading={trendState.loading}
            error={trendState.error && !trendState.data ? trendState.error : ""}
          >
            <TrendLineChart data={trendState.data || []} xKey="date" yKey="score" color="#38BDF8" />
          </ChartCard>
        </div>

        <aside className="rounded-2xl border border-slate-700/60 bg-cardBg p-4 shadow-soft">
          <h3 className="text-sm font-semibold uppercase tracking-wide text-accent">Methodology Panel</h3>
          <p className="mt-3 text-sm text-slate-300">AI Risk Score calculation is transparent:</p>
          <div className="mt-3 rounded-lg border border-slate-700 bg-slate-900/60 p-3 text-sm text-slate-200">
            <p>AI Risk Score =</p>
            <p className="mt-2">0.4 x Hiring Decline</p>
            <p>+ 0.3 x AI Tool Mentions in Job Descriptions</p>
            <p>+ 0.3 x Role Replacement Ratio</p>
          </div>
          <p className="mt-3 text-xs text-slate-400">
            Scores are normalized to 0-100 and bucketed into Low, Medium, High, and Critical risk tiers.
          </p>
        </aside>
      </div>

      <DataTable columns={columns} rows={riskState.data || []} searchable />
    </div>
  );
}
