import { useMemo, useState } from "react";

const PAGE_SIZE = 8;

const sortValue = (value) => {
  if (typeof value === "number") return value;
  const maybeNumber = Number(value);
  if (!Number.isNaN(maybeNumber) && value !== "") return maybeNumber;
  return String(value ?? "").toLowerCase();
};

export default function DataTable({ columns, rows, searchable = true }) {
  const [page, setPage] = useState(1);
  const [query, setQuery] = useState("");
  const [sort, setSort] = useState({ key: columns[0]?.key, direction: "asc" });

  const filtered = useMemo(() => {
    if (!query.trim()) return rows;
    const term = query.toLowerCase();
    return rows.filter((row) =>
      columns.some((column) => String(row[column.key] ?? "").toLowerCase().includes(term))
    );
  }, [rows, query, columns]);

  const sorted = useMemo(() => {
    if (!sort.key) return filtered;
    return [...filtered].sort((a, b) => {
      const av = sortValue(a[sort.key]);
      const bv = sortValue(b[sort.key]);
      if (av < bv) return sort.direction === "asc" ? -1 : 1;
      if (av > bv) return sort.direction === "asc" ? 1 : -1;
      return 0;
    });
  }, [filtered, sort]);

  const totalPages = Math.max(Math.ceil(sorted.length / PAGE_SIZE), 1);
  const currentPage = Math.min(page, totalPages);

  const pageRows = useMemo(() => {
    const start = (currentPage - 1) * PAGE_SIZE;
    return sorted.slice(start, start + PAGE_SIZE);
  }, [sorted, currentPage]);

  const onSort = (key) => {
    setPage(1);
    setSort((prev) => ({
      key,
      direction: prev.key === key && prev.direction === "asc" ? "desc" : "asc",
    }));
  };

  return (
    <div className="rounded-xl border border-slate-700/60 bg-cardBg p-4 shadow-soft">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-accent">Data Table</h3>
        {searchable ? (
          <input
            value={query}
            onChange={(event) => {
              setPage(1);
              setQuery(event.target.value);
            }}
            placeholder="Search records..."
            className="w-full rounded-lg border border-slate-600 bg-slate-900/70 px-3 py-2 text-sm text-slate-100 outline-none focus:border-accent sm:w-60"
          />
        ) : null}
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full text-left text-sm">
          <thead>
            <tr className="border-b border-slate-700 text-slate-300">
              {columns.map((column) => (
                <th key={column.key} className="cursor-pointer px-3 py-2 font-medium" onClick={() => onSort(column.key)}>
                  {column.label}
                  {sort.key === column.key ? (sort.direction === "asc" ? " ^" : " v") : ""}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {pageRows.length ? (
              pageRows.map((row, rowIndex) => (
                <tr key={`${rowIndex}-${row[columns[0].key]}`} className="border-b border-slate-800/70">
                  {columns.map((column) => (
                    <td key={column.key} className="px-3 py-2 text-slate-200">
                      {column.render ? column.render(row[column.key], row) : row[column.key]}
                    </td>
                  ))}
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={columns.length} className="px-3 py-6 text-center text-slate-400">
                  No matching records found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="mt-3 flex items-center justify-between text-xs text-slate-400">
        <span>
          Page {currentPage} of {totalPages}
        </span>
        <div className="space-x-2">
          <button
            type="button"
            onClick={() => setPage((prev) => Math.max(prev - 1, 1))}
            className="rounded border border-slate-600 px-2 py-1 hover:border-accent disabled:cursor-not-allowed disabled:opacity-50"
            disabled={currentPage === 1}
          >
            Prev
          </button>
          <button
            type="button"
            onClick={() => setPage((prev) => Math.min(prev + 1, totalPages))}
            className="rounded border border-slate-600 px-2 py-1 hover:border-accent disabled:cursor-not-allowed disabled:opacity-50"
            disabled={currentPage === totalPages}
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}
