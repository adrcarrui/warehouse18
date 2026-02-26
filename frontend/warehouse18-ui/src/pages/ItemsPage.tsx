import { useEffect, useMemo, useRef, useState } from "react";
import { apiGet } from "../api";
import type { PageMeta, PageOut } from "../api";
import { AppShell } from "../app/AppShell";

import { Button } from "../ui/Button";
import { Input } from "../ui/Input";
import { Badge } from "../ui/Badge";

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

type Tri = "yes" | "no" | "all";
type ActiveTri = "active" | "inactive" | "all";

function triToBool(v: Tri): boolean | undefined {
  if (v === "all") return undefined;
  return v === "yes";
}

export default function ItemsPage() {
  // Column filters (Locations-style)
  const [codeFilter, setCodeFilter] = useState("");
  const [nameFilter, setNameFilter] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("");
  const [uomFilter, setUomFilter] = useState("");
  const [serializedFilter, setSerializedFilter] = useState<Tri>("all");
  const [activeFilter, setActiveFilter] = useState<ActiveTri>("active");

  // paging
  const [page, setPage] = useState(1);
  const [pageSize] = useState(25);

  // data
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

  // Combined free-text query (backend likely searches across code/name/category/uom)
  const qCombined = useMemo(() => {
    return [codeFilter.trim(), nameFilter.trim(), categoryFilter.trim(), uomFilter.trim()].filter(Boolean).join(" ");
  }, [codeFilter, nameFilter, categoryFilter, uomFilter]);

  const includeInactive = useMemo(() => activeFilter !== "active", [activeFilter]);

  // Pages robusto (por si meta.pages viene a 0)
  const pages = useMemo(() => {
    const ps = meta.pageSize || pageSize || 25;
    const t = meta.total || 0;
    const computed = Math.max(1, Math.ceil(t / ps));
    return meta.pages && meta.pages > 0 ? meta.pages : computed;
  }, [meta.pages, meta.pageSize, meta.total, pageSize]);

  async function load(p: number) {
    setLoading(true);
    setErr(null);
    try {
      const { data, meta } = await apiGet<PageOut<ItemOut>>("/api/items", {
        q: qCombined || undefined,
        include_inactive: includeInactive,
        page: p,
        page_size: pageSize,
      });

      let items = data.items;

      // Active filter: backend only supports include/exclude inactive.
      // If user wants ONLY inactive, do client-side filter.
      if (activeFilter === "inactive") {
        items = items.filter((x) => !x.is_active);
      }

      // Serialized filter: likely not supported by backend => client-side
      const wantSerialized = triToBool(serializedFilter);
      if (wantSerialized !== undefined) {
        items = items.filter((x) => x.is_serialized === wantSerialized);
      }

      setRows(items);
      setMeta(meta);
      setPage(p);
    } catch (e: any) {
      setErr(e?.message ?? String(e));
    } finally {
      setLoading(false);
    }
  }

  // initial load
  useEffect(() => {
    load(1);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Debounced auto-search (búsqueda dentro de columnas)
  // FIX: no disparar debounce cuando vienes de paginación (evita el "parpadeo/recarga")
  const debounceRef = useRef<number | null>(null);
  const skipNextDebounceRef = useRef(false);
  const didMountRef = useRef(false);

  useEffect(() => {
    // Evita el "segundo load" al entrar en la página
    if (!didMountRef.current) {
      didMountRef.current = true;
      return;
    }

    if (skipNextDebounceRef.current) {
      skipNextDebounceRef.current = false;
      return;
    }

    if (debounceRef.current) window.clearTimeout(debounceRef.current);

    debounceRef.current = window.setTimeout(() => {
      load(1);
    }, 300);

    return () => {
      if (debounceRef.current) window.clearTimeout(debounceRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [qCombined, activeFilter, serializedFilter]);

  function onFilterKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter") {
      if (debounceRef.current) window.clearTimeout(debounceRef.current);
      load(1);
    }
  }

  function resetFilters() {
    setCodeFilter("");
    setNameFilter("");
    setCategoryFilter("");
    setUomFilter("");
    setSerializedFilter("all");
    setActiveFilter("active");
    if (debounceRef.current) window.clearTimeout(debounceRef.current);
    load(1);
  }

  function goPrev() {
    skipNextDebounceRef.current = true;
    load(meta.page - 1);
  }

  function goNext() {
    skipNextDebounceRef.current = true;
    load(meta.page + 1);
  }

  const effectivePages =
    meta.pages && meta.pages > 0 ? meta.pages : Math.max(1, Math.ceil((meta.total || 0) / (meta.pageSize || 25)));

  return (
    <AppShell title="Items" subtitle="Manage item master data" actions={<Button variant="outline" onClick={resetFilters}>Reset</Button>}>
      <div className="space-y-4">
        {err && (
          <div className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">Error: {err}</div>
        )}

        {/* Table + Pagination (Locations-style) */}
        <div className="rounded-xl border border-zinc-200 bg-white">
          <div className="flex max-h-[750px] flex-col">
            {/* Scroll area */}
            <div className="relative flex-1 overflow-auto bg-white">
              <table className="min-w-full border-separate border-spacing-0">
                <thead className="bg-zinc-50">
                  {/* Row 1: Titles */}
                  <tr>
                    {["ID", "Code", "Name", "UoM", "Category", "Serialized", "Active"].map((h) => (
                      <th
                        key={h}
                        className="whitespace-nowrap border-b border-zinc-200 bg-zinc-50 px-3 py-2 text-left text-xs font-semibold text-zinc-700"
                      >
                        {h}
                      </th>
                    ))}
                  </tr>

                  {/* Row 2: Filters (per column) */}
                  <tr>
                    <th className="border-b border-zinc-200 bg-white px-3 py-2" />

                    <th className="border-b border-zinc-200 bg-white px-3 py-2">
                      <Input
                        value={codeFilter}
                        onChange={(e) => setCodeFilter(e.target.value)}
                        onKeyDown={onFilterKeyDown}
                        placeholder="Filter code…"
                      />
                    </th>

                    <th className="border-b border-zinc-200 bg-white px-3 py-2">
                      <Input
                        value={nameFilter}
                        onChange={(e) => setNameFilter(e.target.value)}
                        onKeyDown={onFilterKeyDown}
                        placeholder="Filter name…"
                      />
                    </th>

                    <th className="border-b border-zinc-200 bg-white px-3 py-2">
                      <Input
                        value={uomFilter}
                        onChange={(e) => setUomFilter(e.target.value)}
                        onKeyDown={onFilterKeyDown}
                        placeholder="Filter uom…"
                      />
                    </th>

                    <th className="border-b border-zinc-200 bg-white px-3 py-2">
                      <Input
                        value={categoryFilter}
                        onChange={(e) => setCategoryFilter(e.target.value)}
                        onKeyDown={onFilterKeyDown}
                        placeholder="Filter category…"
                      />
                    </th>

                    <th className="border-b border-zinc-200 bg-white px-3 py-2">
                      <select
                        className="h-10 w-full rounded-xl border border-zinc-200 bg-white px-3 text-sm"
                        value={serializedFilter}
                        onChange={(e) => setSerializedFilter(e.target.value as Tri)}
                      >
                        <option value="all">All</option>
                        <option value="yes">Serialized</option>
                        <option value="no">Non-serialized</option>
                      </select>
                    </th>

                    <th className="border-b border-zinc-200 bg-white px-3 py-2">
                      <select
                        className="h-10 w-full rounded-xl border border-zinc-200 bg-white px-3 text-sm"
                        value={activeFilter}
                        onChange={(e) => setActiveFilter(e.target.value as ActiveTri)}
                      >
                        <option value="active">Active</option>
                        <option value="inactive">Inactive</option>
                        <option value="all">All</option>
                      </select>
                    </th>
                  </tr>
                </thead>

                <tbody>
                  {rows.map((r) => (
                    <tr key={r.id} className="hover:bg-zinc-50">
                      <td className="border-b border-zinc-100 px-3 py-2 text-sm font-medium text-black">{r.id}</td>
                      <td className="border-b border-zinc-100 px-3 py-2 text-sm text-black">{r.item_code ?? ""}</td>
                      <td className="border-b border-zinc-100 px-3 py-2 text-sm text-black">{r.name}</td>
                      <td className="border-b border-zinc-100 px-3 py-2 text-sm text-black">{r.uom}</td>
                      <td className="border-b border-zinc-100 px-3 py-2 text-sm text-black">{r.category ?? ""}</td>
                      <td className="border-b border-zinc-100 px-3 py-2 text-sm text-black">
                        {r.is_serialized ? "yes" : "no"}
                      </td>
                      <td className="border-b border-zinc-100 px-3 py-2 text-sm text-black">
                        {r.is_active ? "yes" : "no"}
                      </td>
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

            {/* Footer pagination fixed (always visible) */}
            <div className="border-t border-zinc-200 bg-white px-3 py-2">
              <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                <div className="text-sm text-zinc-600">
                  Total <span className="font-semibold text-zinc-900">{meta.total}</span> • Page{" "}
                  <span className="font-semibold text-zinc-900">{meta.page}</span> /{" "}
                  <span className="font-semibold text-zinc-900">{effectivePages}</span> • Size{" "}
                  <span className="font-semibold text-zinc-900">{meta.pageSize}</span>
                </div>

                <div className="flex items-center gap-2">
                  <Button onClick={goPrev} disabled={loading || meta.page <= 1}>
                    Prev
                  </Button>

                  <Button onClick={goNext} disabled={loading || meta.page >= effectivePages}>
                    Next
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Nota: Si tu backend no expone total/pages por headers (CORS), verás “1 page”.
            Este UI ya calcula pages por meta.total. Si total llega 0, el problema está en API/meta. */}
      </div>
    </AppShell>
  );
}