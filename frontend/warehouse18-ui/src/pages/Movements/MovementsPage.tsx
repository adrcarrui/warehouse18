import { useEffect, useMemo, useRef, useState } from "react";
import { AppShell } from "../../app/AppShell";
import { apiGet } from "../../api";
import type { PageMeta, PageOut } from "../../api";

import { Button } from "../../ui/Button";
import { Input } from "../../ui/Input";
import { Badge } from "../../ui/Badge";

type MovementOut = {
  id: number;
  movement_type_id: number;
  item_id?: number | null;
  quantity?: string | number | null; // numeric suele venir como string
  from_location_id?: number | null;
  to_location_id?: number | null;
  reference_type?: string | null;
  reference_id?: number | null;
  user_id?: number | null;
  created_at: string; // timestamptz
  notes?: string | null;
};
type MovementTypeOut = {
  id: number;
  code: string;
  name: string;
};
function fmtDate(v?: string | null) {
  if (!v) return "";
  const d = new Date(v);
  if (Number.isNaN(d.getTime())) return v;
  return d.toLocaleString();
}

function toNumberOrUndefined(v: string): number | undefined {
  const t = v.trim();
  if (!t) return undefined;
  const n = Number(t);
  return Number.isFinite(n) ? n : undefined;
}

function qtyToText(q?: string | number | null) {
  if (q == null) return "";
  return typeof q === "number" ? String(q) : q;
}

export default function MovementsPage() {
  // filtros por columna (IDs / ref / notas)
  const [idFilter, setIdFilter] = useState("");
  const [movementTypeFilter, setMovementTypeFilter] = useState("");
  const [itemIdFilter, setItemIdFilter] = useState("");
  const [fromIdFilter, setFromIdFilter] = useState("");
  const [toIdFilter, setToIdFilter] = useState("");
  const [refTypeFilter, setRefTypeFilter] = useState("");
  const [refIdFilter, setRefIdFilter] = useState("");
  const [userIdFilter, setUserIdFilter] = useState("");
  const [notesFilter, setNotesFilter] = useState("");
  const [mtById, setMtById] = useState<Record<number, MovementTypeOut>>({});

  // paging
  const [page, setPage] = useState(1);
  const [pageSize] = useState(25);

  // data
  const [rows, setRows] = useState<MovementOut[]>([]);
  const [meta, setMeta] = useState<PageMeta>({
    page: 1,
    pageSize: 25,
    total: 0,
    pages: 0,
    link: null,
  });

  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  // q combinado (si tu backend soporta q)
  const qCombined = useMemo(() => {
    return [idFilter.trim(), refTypeFilter.trim(), notesFilter.trim()].filter(Boolean).join(" ");
  }, [idFilter, refTypeFilter, notesFilter]);

  const pages = useMemo(() => {
    const ps = meta.pageSize || pageSize || 25;
    const t = meta.total || 0;
    const computed = Math.max(1, Math.ceil(t / ps));
    return meta.pages && meta.pages > 0 ? meta.pages : computed;
  }, [meta.pages, meta.pageSize, meta.total, pageSize]);

  async function loadMovementTypes() {
    try {
      const { data } = await apiGet<MovementTypeOut[]>("/api/movement-types");
      const map: Record<number, MovementTypeOut> = {};
      for (const mt of data) map[mt.id] = mt;
      setMtById(map);
    } catch {
      // si falla, no pasa nada: seguiremos mostrando el id
      setMtById({});
    }
  }
  async function load(p: number) {
    setLoading(true);
    setErr(null);
    try {
      const { data, meta } = await apiGet<PageOut<MovementOut>>("/api/movements", {
        q: qCombined || undefined,
        movement_type_id: (() => {
          const search = movementTypeFilter.trim().toLowerCase();
          if (!search) return undefined;

          const found = Object.values(mtById).find(
            (mt) => mt.name.toLowerCase().includes(search)
          );

          return found?.id;
        })(),
        item_id: toNumberOrUndefined(itemIdFilter),
        from_location_id: toNumberOrUndefined(fromIdFilter),
        to_location_id: toNumberOrUndefined(toIdFilter),
        reference_type: refTypeFilter.trim() || undefined,
        reference_id: toNumberOrUndefined(refIdFilter),
        user_id: toNumberOrUndefined(userIdFilter),
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
  (async () => {
    await loadMovementTypes();
    await load(1);
  })();
  // eslint-disable-next-line react-hooks/exhaustive-deps
}, []);

  // debounce search
  const debounceRef = useRef<number | null>(null);
  const didMountRef = useRef(false);

  useEffect(() => {
    if (!didMountRef.current) {
      didMountRef.current = true;
      return;
    }
    if (debounceRef.current) window.clearTimeout(debounceRef.current);
    debounceRef.current = window.setTimeout(() => load(1), 300);
    return () => {
      if (debounceRef.current) window.clearTimeout(debounceRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    qCombined,
    movementTypeFilter,
    itemIdFilter,
    fromIdFilter,
    toIdFilter,
    refTypeFilter,
    refIdFilter,
    userIdFilter,
    notesFilter,
    Object.keys(mtById).length,
  ]);

  function onFilterKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter") {
      if (debounceRef.current) window.clearTimeout(debounceRef.current);
      load(1);
    }
  }

  function resetFilters() {
    setIdFilter("");
    setMovementTypeFilter("");
    setItemIdFilter("");
    setFromIdFilter("");
    setToIdFilter("");
    setRefTypeFilter("");
    setRefIdFilter("");
    setUserIdFilter("");
    setNotesFilter("");
    if (debounceRef.current) window.clearTimeout(debounceRef.current);
    load(1);
  }

  return (
    <AppShell
      title="Movements"
      subtitle="Movements from DB (public.movements)"
      actions={
        <div className="flex items-center gap-2">
          <Button type="button" variant="outline" onClick={resetFilters} disabled={loading}>
            Reset
          </Button>
        </div>
      }
    >
      <div className="space-y-4">
        {err && (
          <div className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            Error: {err}
          </div>
        )}

        <div className="rounded-xl border border-zinc-200 bg-white">
          <div className="flex max-h-[750px] flex-col">
            <div className="relative flex-1 overflow-auto bg-white">
              <table className="min-w-full border-separate border-spacing-0">
                <thead className="bg-zinc-50">
                  <tr>
                    {[
                      "ID",
                      "TypeId",
                      "ItemId",
                      "Qty",
                      "FromId",
                      "ToId",
                      "RefType",
                      "RefId",
                      "UserId",
                      "Created",
                      "Notes",
                    ].map((h) => (
                      <th
                        key={h}
                        className="whitespace-nowrap border-b border-zinc-200 bg-zinc-50 px-3 py-2 text-left text-xs font-semibold text-zinc-700"
                      >
                        {h}
                      </th>
                    ))}
                  </tr>

                  {/* filtros */}
                  <tr>
                    <th className="border-b border-zinc-200 bg-white px-3 py-2">
                      <Input value={idFilter} onChange={(e) => setIdFilter(e.target.value)} onKeyDown={onFilterKeyDown} placeholder="id…" />
                    </th>

                    <th className="border-b border-zinc-200 bg-white px-3 py-2">
                      <Input value={movementTypeFilter} onChange={(e) => setMovementTypeFilter(e.target.value)} onKeyDown={onFilterKeyDown} placeholder="movement_type_name…" />
                    </th>

                    <th className="border-b border-zinc-200 bg-white px-3 py-2">
                      <Input value={itemIdFilter} onChange={(e) => setItemIdFilter(e.target.value)} onKeyDown={onFilterKeyDown} placeholder="item_id…" />
                    </th>

                    <th className="border-b border-zinc-200 bg-white px-3 py-2" />

                    <th className="border-b border-zinc-200 bg-white px-3 py-2">
                      <Input value={fromIdFilter} onChange={(e) => setFromIdFilter(e.target.value)} onKeyDown={onFilterKeyDown} placeholder="from_location_id…" />
                    </th>

                    <th className="border-b border-zinc-200 bg-white px-3 py-2">
                      <Input value={toIdFilter} onChange={(e) => setToIdFilter(e.target.value)} onKeyDown={onFilterKeyDown} placeholder="to_location_id…" />
                    </th>

                    <th className="border-b border-zinc-200 bg-white px-3 py-2">
                      <Input value={refTypeFilter} onChange={(e) => setRefTypeFilter(e.target.value)} onKeyDown={onFilterKeyDown} placeholder="reference_type…" />
                    </th>

                    <th className="border-b border-zinc-200 bg-white px-3 py-2">
                      <Input value={refIdFilter} onChange={(e) => setRefIdFilter(e.target.value)} onKeyDown={onFilterKeyDown} placeholder="reference_id…" />
                    </th>

                    <th className="border-b border-zinc-200 bg-white px-3 py-2">
                      <Input value={userIdFilter} onChange={(e) => setUserIdFilter(e.target.value)} onKeyDown={onFilterKeyDown} placeholder="user_id…" />
                    </th>

                    <th className="border-b border-zinc-200 bg-white px-3 py-2" />

                    <th className="border-b border-zinc-200 bg-white px-3 py-2">
                      <Input value={notesFilter} onChange={(e) => setNotesFilter(e.target.value)} onKeyDown={onFilterKeyDown} placeholder="notes…" />
                    </th>
                  </tr>
                </thead>

                <tbody>
                  {rows.map((m) => (
                    <tr key={m.id} className="hover:bg-zinc-50">
                      <td className="border-b border-zinc-100 px-3 py-2 text-sm font-medium text-black tabular-nums">{m.id}</td>
                      <td className="border-b border-zinc-100 px-3 py-2 text-sm text-black tabular-nums">{mtById[m.movement_type_id]?.name ?? `#${m.movement_type_id}`}</td>{/*{m.movement_type_id}</td>*/}
                      <td className="border-b border-zinc-100 px-3 py-2 text-sm text-black tabular-nums">{m.item_id ?? ""}</td>
                      <td className="border-b border-zinc-100 px-3 py-2 text-sm text-black tabular-nums">{qtyToText(m.quantity)}</td>
                      <td className="border-b border-zinc-100 px-3 py-2 text-sm text-black tabular-nums">{m.from_location_id ?? ""}</td>
                      <td className="border-b border-zinc-100 px-3 py-2 text-sm text-black tabular-nums">{m.to_location_id ?? ""}</td>
                      <td className="border-b border-zinc-100 px-3 py-2 text-sm text-black">{m.reference_type ?? ""}</td>
                      <td className="border-b border-zinc-100 px-3 py-2 text-sm text-black tabular-nums">{m.reference_id ?? ""}</td>
                      <td className="border-b border-zinc-100 px-3 py-2 text-sm text-black tabular-nums">{m.user_id ?? ""}</td>
                      <td className="border-b border-zinc-100 px-3 py-2 text-sm text-zinc-600">{fmtDate(m.created_at)}</td>
                      <td className="border-b border-zinc-100 px-3 py-2 text-sm text-black">{m.notes ?? ""}</td>
                    </tr>
                  ))}

                  {!loading && rows.length === 0 && (
                    <tr>
                      <td colSpan={11} className="px-3 py-6 text-sm text-zinc-600">
                        No results
                      </td>
                    </tr>
                  )}

                  {loading && (
                    <tr>
                      <td colSpan={11} className="px-3 py-6 text-sm text-zinc-600">
                        Loading…
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            {/* Footer paginación */}
            <div className="border-t border-zinc-200 bg-white px-3 py-2">
              <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                <div className="text-sm text-zinc-600">
                  Total <span className="font-semibold text-zinc-900">{meta.total}</span> • Page{" "}
                  <span className="font-semibold text-zinc-900">{meta.page}</span> /{" "}
                  <span className="font-semibold text-zinc-900">{pages}</span> • Size{" "}
                  <span className="font-semibold text-zinc-900">{meta.pageSize}</span>
                </div>

                <div className="flex items-center gap-2">
                  <Button type="button" onClick={() => load(meta.page - 1)} disabled={loading || meta.page <= 1}>
                    Prev
                  </Button>
                  <Button type="button" onClick={() => load(meta.page + 1)} disabled={loading || meta.page >= pages}>
                    Next
                  </Button>
                </div>
              </div>
            </div>

            {/* mini indicador */}
            <div className="px-3 pb-2">
              <Badge>{rows.length} rows</Badge>
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}