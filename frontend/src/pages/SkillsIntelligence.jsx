import { useMemo } from "react";
import ChartCard from "../components/ChartCard";
import DataTable from "../components/DataTable";
import StatCard from "../components/StatCard";
import CustomBarChart from "../charts/BarChart";
import useFetch from "../hooks/useFetch";

export default function SkillsIntelligence() {
  const risingState = useFetch("/api/skills/rising");
  const decliningState = useFetch("/api/skills/declining");
  const gapState = useFetch("/api/skills/gap");

  const tableRows = useMemo(() => {
    const rising = risingState.data || [];
    const declining = decliningState.data || [];
    const gap = gapState.data || [];

    return gap.map((item) => {
      const risingMatch = rising.find((skill) => skill.skill === item.skill);
      const decliningMatch = declining.find((skill) => skill.skill === item.skill);
      const trend = risingMatch ? "Rising" : decliningMatch ? "Declining" : "Neutral";
      const delta = item.market_demand - item.training_supply;
      return {
        skill: item.skill,
        demand_score: item.market_demand,
        training_availability: item.training_supply,
        skill_gap: delta,
        trend,
      };
    });
  }, [risingState.data, decliningState.data, gapState.data]);

  const columns = [
    { key: "skill", label: "Skill" },
    { key: "demand_score", label: "Demand Score" },
    { key: "training_availability", label: "Training Availability" },
    { key: "skill_gap", label: "Skill Gap" },
    {
      key: "trend",
      label: "Trend",
      render: (value) => (
        <span
          className={`rounded px-2 py-1 text-xs ${
            value === "Rising"
              ? "bg-emerald-500/20 text-emerald-200"
              : value === "Declining"
              ? "bg-red-500/20 text-red-200"
              : "bg-slate-500/20 text-slate-200"
          }`}
        >
          {value}
        </span>
      ),
    },
  ];

  const averageGap = tableRows.length
    ? Math.round(tableRows.reduce((sum, row) => sum + row.skill_gap, 0) / tableRows.length)
    : 0;

  return (
    <div className="space-y-4">
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Rising Skills Tracked" value={(risingState.data || []).length} />
        <StatCard label="Declining Skills Tracked" value={(decliningState.data || []).length} tone="amber" />
        <StatCard label="Average Skill Gap" value={averageGap} />
        <StatCard label="Training Sources" value={3} suffix=" (PMKVY/NPTEL/SWAYAM)" />
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        <ChartCard
          title="Top 20 Rising Skills"
          subtitle="Week-over-week demand growth"
          loading={risingState.loading}
          error={risingState.error && !risingState.data ? risingState.error : ""}
          accent
        >
          <CustomBarChart data={risingState.data || []} xKey="skill" yKey="growth" />
        </ChartCard>

        <ChartCard
          title="Top 20 Declining Skills"
          subtitle="Skills losing hiring momentum"
          loading={decliningState.loading}
          error={decliningState.error && !decliningState.data ? decliningState.error : ""}
        >
          <CustomBarChart data={decliningState.data || []} xKey="skill" yKey="decline" />
        </ChartCard>
      </div>

      <ChartCard
        title="Skill Gap Map"
        subtitle="Market demand vs training availability"
        loading={gapState.loading}
        error={gapState.error && !gapState.data ? gapState.error : ""}
      >
        <CustomBarChart
          data={(gapState.data || []).map((item) => ({
            skill: item.skill,
            gap: item.market_demand - item.training_supply,
          }))}
          xKey="skill"
          yKey="gap"
        />
      </ChartCard>

      <DataTable columns={columns} rows={tableRows} searchable />
    </div>
  );
}
