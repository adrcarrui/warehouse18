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
  item_key?: string | null;
  quantity?: string | number | null;
  from_location_id?: number | null;
  to_location_id?: number | null;
  user_id?: number | null;
  user_name?: string | null;
  created_at: string;
  notes?: string | null;
  mysim_movement_id?: string | null;
};

type MovementTypeOut = {
  id: number;
  code: string;
  name: string;
};

type LocationOut = {
  id: number;
  code: string;
  name: string;
  type: string;
  parent_id?: number | null;
  is_active: boolean;
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
  if (q == null || q === "") return "1";
  return typeof q === "number" ? String(q) : q;
}

function partToText(m: MovementOut) {
  return m.item_key || (m.item_id != null ? String(m.item_id) : "");
}

function locationLabel(locationId?: number | null, locationMap?: Record<number, LocationOut>) {
  if (locationId == null) return "";
  const loc = locationMap?.[locationId];
  return loc?.name || String(locationId);
}

function movementTypeLabel(mt?: MovementTypeOut) {
  if (!mt) return "";

  const code = (mt.code || "").toUpperCase();

  if (code === "GI") return "Good Issue";
  if (code === "GR") return "Good Receipt";
  if (code === "GT") return "Good Transfer";

  return mt.name || mt.code;
}

function userLabel(row: MovementOut) {
  if (row.user_name && row.user_name.trim() !== "") return row.user_name;
  if (row.user_id != null) return String(row.user_id);
  return "";
}

function movementTypeClassName(mt?: MovementTypeOut) {
  const code = (mt?.code || "").toUpperCase();

  if (code === "GI") return "text-red-600 font-semibold";
  if (code === "GR") return "text-green-600 font-semibold";
  if (code === "GT") return "text-blue-600 font-semibold";

  return "text-black";
}

export default function MovementsPage() {
  const [idFilter, setIdFilter] = useState("");
  const [movementTypeFilter, setMovementTypeFilter] = useState("");
  const [partFilter, setPartFilter] = useState("");
  const [fromIdFilter, setFromIdFilter] = useState("");
  const [toIdFilter, setToIdFilter] = useState("");
  const [userIdFilter, setUserIdFilter] = useState("");
  const [notesFilter, setNotesFilter] = useState("");
  const [mysimMovementIdFilter, setMysimMovementIdFilter] = useState("");

  const [mtById, setMtById] = useState<Record<number, MovementTypeOut>>({});
  const [locationMap, setLocationMap] = useState<Record<number, LocationOut>>({});

  const [page, setPage] = useState(1);
  const [pageSize] = useState(25);

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

  const qCombined = useMemo(() => {
    return [
      idFilter.trim(),
      partFilter.trim(),
      notesFilter.trim(),
      mysimMovementIdFilter.trim(),
    ]
      .filter(Boolean)
      .join(" ");
  }, [idFilter, partFilter, notesFilter, mysimMovementIdFilter]);

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
      setMtById({});
    }
  }

  async function loadAllLocations() {
    try {
      const pageSize = 200;
      let currentPage = 1;
      let totalPages = 1;
      const map: Record<number, LocationOut> = {};

      while (currentPage <= totalPages) {
        const { data, meta } = await apiGet<PageOut<LocationOut>>("/api/locations", {
          include_inactive: true,
          page: currentPage,
          page_size: pageSize,
        });

        for (const loc of data.items) {
          map[loc.id] = loc;
        }

        totalPages = meta.pages && meta.pages > 0
          ? meta.pages
          : Math.max(1, Math.ceil((meta.total || 0) / (meta.pageSize || pageSize)));

        currentPage += 1;
      }

      setLocationMap(map);
    } catch {
      setLocationMap({});
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

          const found = Object.values(mtById).find((mt) => {
            const code = (mt.code || "").toLowerCase();
            const label = movementTypeLabel(mt).toLowerCase();
            const rawName = (mt.name || "").toLowerCase();

            return code.includes(search) || label.includes(search) || rawName.includes(search);
          });

          return found?.id;
        })(),
        from_location_id: toNumberOrUndefined(fromIdFilter),
        to_location_id: toNumberOrUndefined(toIdFilter),
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
      await loadAllLocations();
      await load(1);
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

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
    fromIdFilter,
    toIdFilter,
    userIdFilter,
    notesFilter,
    mysimMovementIdFilter,
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
    setPartFilter("");
    setFromIdFilter("");
    setToIdFilter("");
    setUserIdFilter("");
    setNotesFilter("");
    setMysimMovementIdFilter("");
    if (debounceRef.current) window.clearTimeout(debounceRef.current);
    load(1);
  }

  const FILTER_ROW_TOP = "32px";

  return (
    <AppShell
      title="Movements"
      subtitle="Movements history"
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
          <div className="relative max-h-[750px] overflow-auto bg-white">
            <table className="min-w-full border-separate border-spacing-0 [table-layout:fixed]">
              <thead>
                <tr>
                  {[
                    "ID / MySim",
                    "Type",
                    "Part",
                    "Qty",
                    "From",
                    "To",
                    "DoneBy",
                    "Created",
                    "Notes",
                  ].map((h) => (
                    <th
                      key={h}
                      className="sticky top-0 z-30 whitespace-nowrap border-b border-zinc-200 bg-zinc-50 px-3 py-2 text-left text-xs font-semibold text-zinc-700"
                    >
                      {h}
                    </th>
                  ))}
                </tr>

                <tr>
                  <th
                    className="sticky z-20 border-b border-zinc-200 bg-white px-3 py-2"
                    style={{ top: FILTER_ROW_TOP }}
                  >
                    <Input
                      value={idFilter}
                      onChange={(e) => setIdFilter(e.target.value)}
                      onKeyDown={onFilterKeyDown}
                      placeholder="id…"
                    />
                  </th>

                  <th
                    className="sticky z-20 border-b border-zinc-200 bg-white px-3 py-2"
                    style={{ top: FILTER_ROW_TOP }}
                  >
                    <Input
                      value={movementTypeFilter}
                      onChange={(e) => setMovementTypeFilter(e.target.value)}
                      onKeyDown={onFilterKeyDown}
                      placeholder="movement type…"
                    />
                  </th>

                  <th
                    className="sticky z-20 border-b border-zinc-200 bg-white px-3 py-2"
                    style={{ top: FILTER_ROW_TOP }}
                  >
                    <Input
                      value={partFilter}
                      onChange={(e) => setPartFilter(e.target.value)}
                      onKeyDown={onFilterKeyDown}
                      placeholder="part…"
                    />
                  </th>

                  <th
                    className="sticky z-20 border-b border-zinc-200 bg-white px-3 py-2"
                    style={{ top: FILTER_ROW_TOP }}
                  />

                  <th
                    className="sticky z-20 border-b border-zinc-200 bg-white px-3 py-2"
                    style={{ top: FILTER_ROW_TOP }}
                  >
                    <Input
                      value={fromIdFilter}
                      onChange={(e) => setFromIdFilter(e.target.value)}
                      onKeyDown={onFilterKeyDown}
                      placeholder="from_location_id…"
                    />
                  </th>

                  <th
                    className="sticky z-20 border-b border-zinc-200 bg-white px-3 py-2"
                    style={{ top: FILTER_ROW_TOP }}
                  >
                    <Input
                      value={toIdFilter}
                      onChange={(e) => setToIdFilter(e.target.value)}
                      onKeyDown={onFilterKeyDown}
                      placeholder="to_location_id…"
                    />
                  </th>

                  <th
                    className="sticky z-20 border-b border-zinc-200 bg-white px-3 py-2"
                    style={{ top: FILTER_ROW_TOP }}
                  >
                    <Input
                      value={userIdFilter}
                      onChange={(e) => setUserIdFilter(e.target.value)}
                      onKeyDown={onFilterKeyDown}
                      placeholder="user_id…"
                    />
                  </th>

                  <th
                    className="sticky z-20 border-b border-zinc-200 bg-white px-3 py-2"
                    style={{ top: FILTER_ROW_TOP }}
                  />

                  <th
                    className="sticky z-20 border-b border-zinc-200 bg-white px-3 py-2"
                    style={{ top: FILTER_ROW_TOP }}
                  >
                    <Input
                      value={notesFilter}
                      onChange={(e) => setNotesFilter(e.target.value)}
                      onKeyDown={onFilterKeyDown}
                      placeholder="notes / mysim id…"
                    />
                  </th>
                </tr>
              </thead>

              <tbody>
                {rows.map((m) => {
                  const mt = mtById[m.movement_type_id];

                  return (
                    <tr key={m.id} className="hover:bg-zinc-50">
                      <td className="border-b border-zinc-100 px-3 py-2 text-sm text-black">
                        <div className="font-medium tabular-nums">{m.id}</div>
                        {m.mysim_movement_id ? (
                          <div className="text-xs text-zinc-500">{m.mysim_movement_id}</div>
                        ) : null}
                      </td>

                      <td
                        className={`border-b border-zinc-100 px-3 py-2 text-sm ${movementTypeClassName(mt)}`}
                      >
                        {mt ? movementTypeLabel(mt) : `#${m.movement_type_id}`}
                      </td>

                      <td className="border-b border-zinc-100 px-3 py-2 text-sm text-black">
                        {partToText(m)}
                      </td>

                      <td className="border-b border-zinc-100 px-3 py-2 text-sm text-black tabular-nums">
                        {qtyToText(m.quantity)}
                      </td>

                      <td className="border-b border-zinc-100 px-3 py-2 text-sm text-black">
                        {locationLabel(m.from_location_id, locationMap)}
                      </td>

                      <td className="border-b border-zinc-100 px-3 py-2 text-sm text-black">
                        {locationLabel(m.to_location_id, locationMap)}
                      </td>

                      <td className="border-b border-zinc-100 px-3 py-2 text-sm text-black tabular-nums">
                        {userLabel(m)}
                      </td>

                      <td className="border-b border-zinc-100 px-3 py-2 text-sm text-zinc-600">
                        {fmtDate(m.created_at)}
                      </td>

                      <td className="border-b border-zinc-100 px-3 py-2 text-sm text-black">
                        {m.notes ?? ""}
                      </td>
                    </tr>
                  );
                })}

                {!loading && rows.length === 0 && (
                  <tr>
                    <td colSpan={9} className="px-3 py-6 text-sm text-zinc-600">
                      No results
                    </td>
                  </tr>
                )}

                {loading && (
                  <tr>
                    <td colSpan={9} className="px-3 py-6 text-sm text-zinc-600">
                      Loading…
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div className="text-sm text-zinc-600">
            Total <span className="font-semibold text-zinc-900">{meta.total}</span> • Page{" "}
            <span className="font-semibold text-zinc-900">{meta.page}</span> /{" "}
            <span className="font-semibold text-zinc-900">{pages}</span> • Size{" "}
            <span className="font-semibold text-zinc-900">{meta.pageSize}</span>
          </div>

          <div className="flex items-center gap-2">
            <Button
              type="button"
              onClick={() => load(meta.page - 1)}
              disabled={loading || meta.page <= 1}
            >
              Prev
            </Button>
            <Button
              type="button"
              onClick={() => load(meta.page + 1)}
              disabled={loading || meta.page >= pages}
            >
              Next
            </Button>
          </div>
        </div>

        <div>
          <Badge>{rows.length} rows</Badge>
        </div>
      </div>
    </AppShell>
  );
}