import { useEffect, useMemo, useState } from "react";
import { apiGet } from "../api";
import type { PageMeta, PageOut } from "../api";
import { AppShell } from "../app/AppShell";

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

function Badge({ children }: { children: React.ReactNode }) {
  return (
    <span className="inline-flex items-center rounded-full border border-zinc-200 bg-zinc-50 px-2 py-0.5 text-xs text-zinc-700">
      {children}
    </span>
  );
}

function Button(props: React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "primary" | "outline" | "ghost" }) {
  const { variant = "outline", className = "", ...rest } = props;
  const base =
    "inline-flex items-center justify-center rounded-lg px-3 py-2 text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed";
  const styles =
    variant === "primary"
      ? "bg-zinc-900 text-white hover:bg-zinc-800"
      : variant === "ghost"
      ? "bg-transparent hover:bg-zinc-100"
      : "border border-zinc-200 bg-white hover:bg-zinc-50";
  return <button className={`${base} ${styles} ${className}`} {...rest} />;
}

function Input(props: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      {...props}
      className={`h-10 w-full rounded-lg border border-zinc-200 bg-white px-3 text-sm outline-none focus:border-zinc-400 ${props.className ?? ""}`}
    />
  );
}

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

  const summary = useMemo(() => {
    const pages = meta.pages || 0;
    return `${meta.total} total • page ${meta.page}/${pages || 1} • size ${meta.pageSize}`;
  }, [meta]);

  return (
    <AppShell
      title="Items"
      actions={
        <Button variant="primary" onClick={() => load(1)} disabled={loading}>
          Search
        </Button>
      }
    >
      <div className="space-y-4">
        {/* Filters */}
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div className="flex w-full flex-col gap-2 md:flex-row md:items-center">
            <div className="w-full md:w-96">
              <Input
                value={q}
                onChange={(e) => setQ(e.target.value)}
                placeholder="Search by code, name, category..."
              />
            </div>

            <label className="flex items-center gap-2 text-sm text-zinc-700">
              <input
                type="checkbox"
                className="h-4 w-4 rounded border-zinc-300"
                checked={includeInactive}
                onChange={(e) => setIncludeInactive(e.target.checked)}
              />
              include inactive
            </label>
          </div>

          <div className="flex items-center gap-2">
            <Badge>{summary}</Badge>
            <Button variant="ghost" onClick={() => { setQ(""); setIncludeInactive(false); load(1); }} disabled={loading}>
              Reset
            </Button>
          </div>
        </div>

        {/* Error */}
        {err && (
          <div className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            Error: {err}
          </div>
        )}

        {/* Table */}
        <div className="overflow-x-auto rounded-xl border border-zinc-200">
          <table className="min-w-full border-collapse">
            <thead className="bg-zinc-50">
              <tr>
                {["ID", "Code", "Name", "UoM", "Category", "Serialized", "Active"].map((h) => (
                  <th
                    key={h}
                    className="whitespace-nowrap border-b border-zinc-200 px-3 py-2 text-left text-xs font-semibold text-zinc-700"
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>

            <tbody>
              {rows.map((r) => (
                <tr key={r.id} className="hover:bg-zinc-50">
                  <td className="border-b border-zinc-100 px-3 py-2 text-sm font-medium">{r.id}</td>
                  <td className="border-b border-zinc-100 px-3 py-2 text-sm text-zinc-800">{r.item_code ?? ""}</td>
                  <td className="border-b border-zinc-100 px-3 py-2 text-sm text-zinc-800">{r.name}</td>
                  <td className="border-b border-zinc-100 px-3 py-2 text-sm text-zinc-800">{r.uom}</td>
                  <td className="border-b border-zinc-100 px-3 py-2 text-sm text-zinc-800">{r.category ?? ""}</td>
                  <td className="border-b border-zinc-100 px-3 py-2 text-sm text-zinc-800">{r.is_serialized ? "yes" : "no"}</td>
                  <td className="border-b border-zinc-100 px-3 py-2 text-sm text-zinc-800">{r.is_active ? "yes" : "no"}</td>
                </tr>
              ))}

              {!loading && rows.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-3 py-6 text-sm text-zinc-600">
                    No results
                  </td>
                </tr>
              )}

              {loading && (
                <tr>
                  <td colSpan={7} className="px-3 py-6 text-sm text-zinc-600">
                    Loading…
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="flex items-center gap-2">
          <Button onClick={() => load(page - 1)} disabled={!canPrev}>Prev</Button>
          <Button onClick={() => load(page + 1)} disabled={!canNext}>Next</Button>
        </div>
      </div>
    </AppShell>
  );
}
