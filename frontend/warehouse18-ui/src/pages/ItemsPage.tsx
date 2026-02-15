import { useEffect, useState } from "react";
import { apiGet } from "../api";
import type { PageMeta, PageOut } from "../api";


console.log("API MODULE LOADED", typeof apiGet);

type ItemOut = {
  id: number;
  item_code?: string;
  name: string;
  category?: string;
  uom: string;
  is_serialized: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export default function ItemsPage() {
  const [q, setQ] = useState("");
  const [includeInactive, setIncludeInactive] = useState(false);

  const [page, setPage] = useState(1);
  const [pageSize] = useState(25);

  const [rows, setRows] = useState<ItemOut[]>([]);
  const [meta, setMeta] = useState<PageMeta>({
    page: 1,
    pageSize: 25,
    total: 0,
    pages: 0,
    link: null,
  });

  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function load(p: number) {
    setLoading(true);
    setErr(null);
    try {
      const { data, meta } = await apiGet<PageOut<ItemOut>>("/api/items", {
        q: q.trim() || undefined,
        include_inactive: includeInactive,
        page: p,
        page_size: pageSize,
      });

      setRows(data.items);
      setMeta(meta);
      setPage(p);
    } catch (e: any) {
      setErr(e?.message ?? String(e));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load(1);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const canPrev = !loading && meta.page > 1;
  const canNext = !loading && meta.pages > 0 && meta.page < meta.pages;

  return (
    <div style={{ padding: 16, fontFamily: "system-ui" }}>
      <h2 style={{ marginTop: 0 }}>Items</h2>

      <div style={{ display: "flex", gap: 12, alignItems: "center", marginBottom: 12 }}>
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Search (q)..."
          style={{ padding: 8, width: 320 }}
        />
        <label style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <input
            type="checkbox"
            checked={includeInactive}
            onChange={(e) => setIncludeInactive(e.target.checked)}
          />
          include inactive
        </label>
        <button onClick={() => load(1)} disabled={loading}>
          Search
        </button>
      </div>

      {err && (
        <div style={{ color: "crimson", marginBottom: 12 }}>
          Error: {err}
        </div>
      )}

      <div style={{ marginBottom: 10, color: "#444" }}>
        Total: {meta.total} | Page {meta.page}/{meta.pages} | Page size {meta.pageSize}
      </div>

      <div style={{ border: "1px solid #eee", borderRadius: 8, overflow: "hidden" }}>
        <table width="100%" cellPadding={10} style={{ borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ textAlign: "left", background: "#fafafa", borderBottom: "1px solid #eee" }}>
              <th>ID</th>
              <th>Code</th>
              <th>Name</th>
              <th>UoM</th>
              <th>Category</th>
              <th>Serialized</th>
              <th>Active</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id} style={{ borderBottom: "1px solid #f2f2f2" }}>
                <td>{r.id}</td>
                <td>{r.item_code ?? ""}</td>
                <td>{r.name}</td>
                <td>{r.uom}</td>
                <td>{r.category ?? ""}</td>
                <td>{r.is_serialized ? "yes" : "no"}</td>
                <td>{r.is_active ? "yes" : "no"}</td>
              </tr>
            ))}
            {!loading && rows.length === 0 && (
              <tr>
                <td colSpan={7} style={{ padding: 16, color: "#666" }}>
                  No results
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
        <button onClick={() => load(page - 1)} disabled={!canPrev}>
          Prev
        </button>
        <button onClick={() => load(page + 1)} disabled={!canNext}>
          Next
        </button>
      </div>
    </div>
  );
}
