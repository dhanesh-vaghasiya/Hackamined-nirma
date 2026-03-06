import {
  ResponsiveContainer,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  BarChart,
  Bar,
  Cell,
} from "recharts";

const defaultPalette = ["#20D9D2", "#38BDF8", "#14B8A6", "#22D3EE", "#0EA5A3"];

export default function CustomBarChart({
  data,
  xKey,
  yKey,
  horizontal = false,
  palette = defaultPalette,
}) {
  return (
    <div className="h-72 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={data}
          layout={horizontal ? "vertical" : "horizontal"}
          margin={{ top: 8, right: 16, left: horizontal ? 24 : 0, bottom: 8 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
          {horizontal ? (
            <>
              <XAxis type="number" stroke="#94a3b8" tick={{ fontSize: 11 }} />
              <YAxis type="category" dataKey={xKey} stroke="#94a3b8" width={95} tick={{ fontSize: 11 }} />
            </>
          ) : (
            <>
              <XAxis dataKey={xKey} stroke="#94a3b8" tick={{ fontSize: 11 }} />
              <YAxis stroke="#94a3b8" tick={{ fontSize: 11 }} />
            </>
          )}
          <Tooltip
            contentStyle={{ background: "#0f172a", border: "1px solid #334155" }}
            labelStyle={{ color: "#cbd5e1" }}
          />
          <Bar dataKey={yKey} radius={[8, 8, 0, 0]}>
            {data.map((entry, idx) => (
              <Cell key={`${entry[xKey]}-${idx}`} fill={palette[idx % palette.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
