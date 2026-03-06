import { useMemo, useState } from "react";
import ChartCard from "../components/ChartCard";
import DataTable from "../components/DataTable";
import StatCard from "../components/StatCard";
import CustomBarChart from "../charts/BarChart";
import TrendLineChart from "../charts/LineChart";
import useFetch from "../hooks/useFetch";

const ranges = [
  { label: "7 Days", value: 7 },
  { label: "30 Days", value: 30 },
  { label: "90 Days", value: 90 },
  { label: "1 Year", value: 365 },
];

export default function HiringTrends() {
  const [range, setRange] = useState(30);
  const timeSeriesState = useFetch("/api/hiring-trends/time-series");
  const categoriesState = useFetch("/api/hiring-trends/categories");
  const citiesState = useFetch("/api/hiring-trends/cities");
  const jobsState = useFetch("/api/jobs");

  const trendData = useMemo(() => {
    const raw = timeSeriesState.data;
    if (!raw?.dates || !raw?.job_counts) return [];
    const points = raw.dates.map((date, idx) => ({ date, jobs: raw.job_counts[idx] || 0 }));
    if (range === 365) return points;
    return points.slice(-Math.min(range, points.length));
  }, [timeSeriesState.data, range]);

  const totalJobs = useMemo(
    () => trendData.reduce((sum, item) => sum + (item.jobs || 0), 0),
    [trendData]
  );

  const avgJobs = trendData.length ? Math.round(totalJobs / trendData.length) : 0;
  const peakJobs = trendData.length ? Math.max(...trendData.map((item) => item.jobs || 0)) : 0;

  const jobColumns = [
    { key: "title", label: "Job Title" },
    { key: "company", label: "Company" },
    { key: "city", label: "City" },
    { key: "salary_range", label: "Salary Range" },
    { key: "posting_date", label: "Posting Date" },
    { key: "source", label: "Source" },
  ];

  return (
    <div className="space-y-4">
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Total Jobs (Current Window)" value={totalJobs} />
        <StatCard label="Average Daily Jobs" value={avgJobs} />
        <StatCard label="Peak Demand" value={peakJobs} />
        <StatCard label="Tracked Cities" value={citiesState.data?.length || 0} />
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        <ChartCard
          title="Job Volume Trend"
          subtitle="Postings over time"
          loading={timeSeriesState.loading}
          error={timeSeriesState.error && !timeSeriesState.data ? timeSeriesState.error : ""}
          accent
          extra={
            <div className="flex flex-wrap gap-1">
              {ranges.map((item) => (
                <button
                  key={item.value}
                  type="button"
                  onClick={() => setRange(item.value)}
                  className={`rounded px-2 py-1 text-xs ${
                    range === item.value
                      ? "bg-cyan-400/20 text-accent"
                      : "bg-slate-800 text-slate-300 hover:bg-slate-700"
                  }`}
                >
                  {item.label}
                </button>
              ))}
            </div>
          }
        >
          <TrendLineChart data={trendData} xKey="date" yKey="jobs" />
        </ChartCard>

        <ChartCard
          title="Job Category Volume"
          subtitle="Demand by role category"
          loading={categoriesState.loading}
          error={categoriesState.error && !categoriesState.data ? categoriesState.error : ""}
        >
          <CustomBarChart data={categoriesState.data || []} xKey="category" yKey="count" />
        </ChartCard>
      </div>

      <ChartCard
        title="City Hiring Distribution"
        subtitle="Top cities including Tier-2 and Tier-3 clusters"
        loading={citiesState.loading}
        error={citiesState.error && !citiesState.data ? citiesState.error : ""}
      >
        <CustomBarChart data={citiesState.data || []} xKey="city" yKey="count" horizontal />
      </ChartCard>

      <DataTable columns={jobColumns} rows={jobsState.data || []} searchable />
    </div>
  );
}
