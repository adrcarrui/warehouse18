import React from "react";

export function Table(props: {
  headers: string[];
  rows: React.ReactNode[][];
}) {
  const { headers, rows } = props;

  return (
    <div className="overflow-hidden rounded-2xl border border-zinc-200 bg-white">
      <table className="min-w-full border-collapse">
        <thead>
          <tr className="bg-zinc-50">
            {headers.map((h) => (
              <th
                key={h}
                className="border-b border-zinc-200 px-4 py-3 text-left text-xs font-semibold text-zinc-600"
              >
                {h}
              </th>
            ))}
          </tr>
        </thead>

        <tbody>
          {rows.map((cells, i) => (
            <tr
              key={i}
              className={[
                "transition-colors hover:bg-zinc-50",
                i % 2 === 0 ? "bg-white" : "bg-zinc-50/30",
              ].join(" ")}
            >
              {cells.map((c, j) => (
                <td
                  key={j}
                  className="border-b border-zinc-100 px-4 py-3 text-sm text-zinc-800"
                >
                  {c}
                </td>
              ))}
            </tr>
          ))}

          {rows.length === 0 && (
            <tr>
              <td colSpan={headers.length} className="px-4 py-10 text-sm text-zinc-500">
                No results
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
