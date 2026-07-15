import { Fragment, useEffect, useMemo, useRef, useState } from "react";
import type { KeyboardEvent } from "react";
import { Minus, Plus } from "lucide-react";

import { AppShell } from "../../app/AppShell";
import { apiGet } from "../../api";
import type { PageMeta, PageOut } from "../../api";

import { Button } from "../../ui/Button";
import { Input } from "../../ui/Input";

type UserOut = {
  id: number;
  username: string;
  full_name: string;
  email?: string | null;
  role?: string;
  department?: string | null;
  is_active?: boolean;
};

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
  mysim_user_id?: number | null;
  mysim_user_name?: string | null;
  created_at: string;
  notes?: string | null;
  mysim_movement_id?: string | null;
  detected_aisle_id?: number | null;
  aisle_name?: string | null;
  aisle_code?: string | null;
};

type ItemOut = {
  id: number;
  item_code?: string | null;
  name: string;
  is_active?: boolean;
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
  aisle_id?: number | null;
  device_group_id?: number | null;
  rack_code?: string | null;
  shelf_code?: string | null;
};

function errMsg(e: unknown) {
  return e instanceof Error ? e.message : String(e);
}

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

function locationLabel(
  locationId?: number | null,
  locationMap?: Record<number, LocationOut>
) {
  if (locationId == null) return "";

  const loc = locationMap?.[locationId];

  if (loc?.name) return loc.name;
  if (loc?.code) return loc.code;

  return String(locationId);
}

function resolvedLocationName(
  locationId: number | null | undefined,
  locationMap: Record<number, LocationOut>
) {
  if (locationId == null) return "Not set";

  const location = locationMap[locationId];
  return location?.name || location?.code || "Location not found";
}

function itemName(
  movement: MovementOut,
  itemMap: Record<number, ItemOut>
) {
  if (movement.item_id != null) {
    const item = itemMap[movement.item_id];

    if (item?.name) return item.name;
    if (item?.item_code) return item.item_code;
  }

  return movement.item_key || "Item not found";
}

function userFullName(
  movement: MovementOut,
  userMap: Record<number, UserOut>
) {
  if (movement.user_id != null) {
    const user = userMap[movement.user_id];

    if (user?.full_name) return user.full_name;
    if (user?.username) return user.username;
  }

  return (
    movement.user_name ||
    movement.mysim_user_name ||
    "User not found"
  );
}

function detectedAisleName(
  movement: MovementOut,
  locationMap: Record<number, LocationOut>
) {
  if (movement.aisle_name) return movement.aisle_name;
  if (movement.aisle_code) return movement.aisle_code;

  if (movement.detected_aisle_id != null) {
    const aisleLocation = locationMap[movement.detected_aisle_id];

    if (aisleLocation?.name) return aisleLocation.name;
    if (aisleLocation?.code) return aisleLocation.code;
  }

  return movement.detected_aisle_id == null
    ? "Not detected"
    : "Aisle not found";
}

function movementTypeLabel(mt?: MovementTypeOut) {
  if (!mt) return "";

  const code = (mt.code || "").toUpperCase();

  if (code === "GI") return "Good Issue";
  if (code === "GR") return "Good Receipt";
  if (code === "GT") return "Good Transfer";

  return mt.name || mt.code;
}

function doneByLabel(row: MovementOut, userMap: Record<number, UserOut>) {
  if (row.user_name && row.user_name.trim() !== "") {
    return row.user_name;
  }

  if (row.user_id != null) {
    const user = userMap[row.user_id];

    if (user) {
      return user.full_name || user.username || "";
    }
  }

  return "";
}

function movementTypeBadgeClassName(mt?: MovementTypeOut) {
  const code = (mt?.code || "").toUpperCase();

  if (code === "GI") {
    return "border-red-200 bg-red-50 text-red-700";
  }

  if (code === "GR") {
    return "border-green-200 bg-green-50 text-green-700";
  }

  if (code === "GT") {
    return "border-blue-200 bg-blue-50 text-blue-700";
  }

  return "border-zinc-200 bg-zinc-50 text-zinc-700";
}

export default function MovementsPage() {
  const [dateFilter, setDateFilter] = useState("");
  const [idFilter, setIdFilter] = useState("");
  const [mysimMovementIdFilter, setMysimMovementIdFilter] = useState("");
  const [movementTypeFilter, setMovementTypeFilter] = useState("");
  const [partFilter, setPartFilter] = useState("");
  const [toIdFilter, setToIdFilter] = useState("");
  const [userIdFilter, setUserIdFilter] = useState("");
  const [notesFilter, setNotesFilter] = useState("");

  const [expandedMovementIds, setExpandedMovementIds] = useState<Set<number>>(
    () => new Set()
  );
  const [userMap, setUserMap] = useState<Record<number, UserOut>>({});
  const [mtById, setMtById] = useState<Record<number, MovementTypeOut>>({});
  const [locationMap, setLocationMap] = useState<Record<number, LocationOut>>(
    {}
  );
  const [itemMap, setItemMap] = useState<Record<number, ItemOut>>({});

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
      dateFilter.trim(),
      idFilter.trim(),
      mysimMovementIdFilter.trim(),
      partFilter.trim(),
      notesFilter.trim(),
    ]
      .filter(Boolean)
      .join(" ");
  }, [
    dateFilter,
    idFilter,
    mysimMovementIdFilter,
    partFilter,
    notesFilter,
  ]);

  const pages = useMemo(() => {
    const ps = meta.pageSize || pageSize || 25;
    const t = meta.total || 0;
    const computed = Math.max(1, Math.ceil(t / ps));

    return meta.pages && meta.pages > 0 ? meta.pages : computed;
  }, [meta.pages, meta.pageSize, meta.total, pageSize]);

  async function loadUserMap() {
    try {
      const pageSize = 200;
      let currentPage = 1;
      let totalPages = 1;

      const map: Record<number, UserOut> = {};

      while (currentPage <= totalPages) {
        const { data, meta } = await apiGet<PageOut<UserOut>>("/api/users", {
          page: currentPage,
          page_size: pageSize,
        });

        for (const user of data.items) {
          map[user.id] = user;
        }

        totalPages =
          meta.pages && meta.pages > 0
            ? meta.pages
            : Math.max(
                1,
                Math.ceil((meta.total || 0) / (meta.pageSize || pageSize))
              );

        currentPage += 1;
      }

      setUserMap(map);
    } catch {
      setUserMap({});
    }
  }

  async function loadMovementTypes() {
    try {
      const { data } = await apiGet<MovementTypeOut[]>("/api/movement-types");

      const map: Record<number, MovementTypeOut> = {};
      for (const mt of data) {
        map[mt.id] = mt;
      }

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
        const { data, meta } = await apiGet<PageOut<LocationOut>>(
          "/api/locations",
          {
            include_inactive: true,
            page: currentPage,
            page_size: pageSize,
          }
        );

        for (const loc of data.items) {
          map[loc.id] = loc;
        }

        totalPages =
          meta.pages && meta.pages > 0
            ? meta.pages
            : Math.max(
                1,
                Math.ceil((meta.total || 0) / (meta.pageSize || pageSize))
              );

        currentPage += 1;
      }

      setLocationMap(map);
    } catch {
      setLocationMap({});
    }
  }

  async function loadItemMap() {
    try {
      const pageSize = 200;
      let currentPage = 1;
      let totalPages = 1;
      const map: Record<number, ItemOut> = {};

      while (currentPage <= totalPages) {
        const { data, meta } = await apiGet<PageOut<ItemOut>>("/api/items", {
          include_inactive: true,
          page: currentPage,
          page_size: pageSize,
        });

        for (const item of data.items) {
          map[item.id] = item;
        }

        totalPages =
          meta.pages && meta.pages > 0
            ? meta.pages
            : Math.max(
                1,
                Math.ceil((meta.total || 0) / (meta.pageSize || pageSize))
              );

        currentPage += 1;
      }

      setItemMap(map);
    } catch {
      setItemMap({});
    }
  }

  function movementTypeFilterId() {
    const search = movementTypeFilter.trim().toLowerCase();

    if (!search) return undefined;

    const found = Object.values(mtById).find((mt) => {
      const code = (mt.code || "").toLowerCase();
      const label = movementTypeLabel(mt).toLowerCase();
      const rawName = (mt.name || "").toLowerCase();

      return (
        code.includes(search) ||
        label.includes(search) ||
        rawName.includes(search)
      );
    });

    return found?.id;
  }

  async function load(p: number) {
    setLoading(true);
    setErr(null);

    try {
      const { data, meta } = await apiGet<PageOut<MovementOut>>(
        "/api/movements",
        {
          q: qCombined || undefined,
          movement_type_id: movementTypeFilterId(),
          to_location_id: toNumberOrUndefined(toIdFilter),
          user_id: toNumberOrUndefined(userIdFilter),
          page: p,
          page_size: pageSize,
        }
      );

      setRows(data.items);
      setMeta(meta);
    } catch (e: unknown) {
      setErr(errMsg(e));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    (async () => {
      await loadMovementTypes();
      await loadAllLocations();
      await loadUserMap();
      await loadItemMap();
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

    if (debounceRef.current) {
      window.clearTimeout(debounceRef.current);
    }

    debounceRef.current = window.setTimeout(() => {
      void load(1);
    }, 300);

    return () => {
      if (debounceRef.current) {
        window.clearTimeout(debounceRef.current);
      }
    };

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    qCombined,
    movementTypeFilter,
    toIdFilter,
    userIdFilter,
    Object.keys(mtById).length,
  ]);

  function onFilterKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter") {
      if (debounceRef.current) {
        window.clearTimeout(debounceRef.current);
      }

      void load(1);
    }
  }

  function resetFilters() {
    setDateFilter("");
    setIdFilter("");
    setMysimMovementIdFilter("");
    setMovementTypeFilter("");
    setPartFilter("");
    setToIdFilter("");
    setUserIdFilter("");
    setNotesFilter("");

    if (debounceRef.current) {
      window.clearTimeout(debounceRef.current);
    }
  }

  function toggleMovementDetails(movementId: number) {
    setExpandedMovementIds((prev) => {
      const next = new Set(prev);

      if (next.has(movementId)) {
        next.delete(movementId);
      } else {
        next.add(movementId);
      }

      return next;
    });
  }

  const FILTER_ROW_TOP = "33px";
  const columnCount = 9;

  return (
    <AppShell
      title="Movements"
      subtitle="Movements history"

    >
      <div className="space-y-4">
        {err && (
          <div className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            Error: {err}
          </div>
        )}

        <div className="rounded-xl border border-zinc-200 bg-white">
          <div className="relative max-h-[750px] overflow-auto bg-white">
            <table className="min-w-[1100px] border-separate border-spacing-0 [table-layout:fixed]">
              <thead>
                <tr>
                  {[
                    "Date",
                    "Mov ID",
                    "mySim ID",
                    "Mov Type",
                    "Part ID",
                    "Quantity",
                    "Destination",
                    "Done by",
                    "",
                  ].map((h) => (
                    <th
                      key={h || "details"}
                      className="sticky top-0 z-30 whitespace-nowrap border-b border-blue-950 bg-blue-950 px-3 py-2 text-left text-sm font-semibold text-white"
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
                      value={dateFilter}
                      onChange={(e) => setDateFilter(e.target.value)}
                      onKeyDown={onFilterKeyDown}
                      placeholder="Date…"
                    />
                  </th>

                  <th
                    className="sticky z-20 border-b border-zinc-200 bg-white px-3 py-2"
                    style={{ top: FILTER_ROW_TOP }}
                  >
                    <Input
                      value={idFilter}
                      onChange={(e) => setIdFilter(e.target.value)}
                      onKeyDown={onFilterKeyDown}
                      placeholder="Mov id…"
                    />
                  </th>

                  <th
                    className="sticky z-20 border-b border-zinc-200 bg-white px-3 py-2"
                    style={{ top: FILTER_ROW_TOP }}
                  >
                    <Input
                      value={mysimMovementIdFilter}
                      onChange={(e) =>
                        setMysimMovementIdFilter(e.target.value)
                      }
                      onKeyDown={onFilterKeyDown}
                      placeholder="mySim id…"
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
                      placeholder="GR / GI / GT…"
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
                      placeholder="Part ID…"
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
                      value={toIdFilter}
                      onChange={(e) => setToIdFilter(e.target.value)}
                      onKeyDown={onFilterKeyDown}
                      placeholder="Destination id…"
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
                      placeholder="user id…"
                    />
                  </th>

                  <th
                    className="sticky z-20 border-b border-zinc-200 bg-white px-3 py-2"
                    style={{ top: FILTER_ROW_TOP }}
                  >
                    <Button
            type="button"
            variant="outline"
            onClick={resetFilters}
            disabled={loading}
          >
            Reset
          </Button>
                  </th>
                </tr>
              </thead>

              <tbody>
                {rows.map((m) => {
                  const mt = mtById[m.movement_type_id];
                  const isExpanded = expandedMovementIds.has(m.id);

                  return (
                    <Fragment key={m.id}>
                      <tr className="hover:bg-zinc-50">
                        <td className="border-b border-zinc-100 px-3 py-2 text-sm text-zinc-600 text-center">
                          {fmtDate(m.created_at)}
                        </td>

                        <td className="border-b border-zinc-100 px-3 py-2 text-sm text-black text-center">
                          <span className="inline-flex w-fit items-center rounded-full bg-blue-900 px-2 py-1 text-xs font-semibold text-white">
                            #{m.id}
                          </span>
                        </td>

                        <td className="border-b border-zinc-100 px-3 py-2 text-sm text-black text-center">
                          {m.mysim_movement_id ? (
                            <span className="font-medium text-zinc-900">
                              {m.mysim_movement_id}
                            </span>
                          ) : (
                            <span className="inline-flex rounded-full border border-amber-200 bg-amber-50 px-2 py-1 text-xs font-semibold text-amber-700">
                              Not synchronized
                            </span>
                          )}
                        </td>

                        <td className="border-b border-zinc-100 px-3 py-2 text-sm text-center">
                          <span
                            className={`inline-flex rounded-full border px-2 py-1 text-xs font-semibold ${movementTypeBadgeClassName(
                              mt
                            )}`}
                          >
                            {mt
                              ? movementTypeLabel(mt)
                              : `#${m.movement_type_id}`}
                          </span>
                        </td>

                        <td className="border-b border-zinc-100 px-3 py-2 text-sm font-medium text-zinc-900 text-center">
                          {partToText(m) || "—"}
                        </td>

                        <td className="border-b border-zinc-100 px-3 py-2 text-sm tabular-nums text-zinc-900 text-center">
                          {qtyToText(m.quantity)}
                        </td>

                        <td className="border-b border-zinc-100 px-3 py-2 text-sm text-zinc-900 text-center">
                          {locationLabel(m.to_location_id, locationMap) ||
                            "No destination"}
                        </td>

                        <td className="border-b border-zinc-100 px-3 py-2 text-sm text-zinc-900 text-center">
                          {doneByLabel(m, userMap) || "No user"}
                        </td>

                        <td className="border-b border-zinc-100 px-3 py-2 text-sm text-zinc-900 text-center">
                          <button
                            type="button"
                            onClick={() => toggleMovementDetails(m.id)}
                            title={
                              isExpanded
                                ? "Hide movement details"
                                : "Show movement details"
                            }
                            className="mx-auto flex h-8 w-8 items-center justify-center rounded-lg border border-blue-600 bg-blue-600 text-white hover:bg-blue-700"
                          >
                            {isExpanded ? (
                              <Minus className="h-4 w-4" />
                            ) : (
                              <Plus className="h-4 w-4" />
                            )}

                            <span className="sr-only">
                              {isExpanded
                                ? "Hide movement details"
                                : "Show movement details"}
                            </span>
                          </button>
                        </td>
                      </tr>

                      {isExpanded && (
                        <tr>
                          <td
                            colSpan={columnCount}
                            className="border-b border-zinc-100 bg-zinc-50 px-3 py-3"
                          >
                            <div className="rounded-xl border border-zinc-200 bg-white p-4">
                              <div className="mb-3 text-xs font-semibold uppercase tracking-wide text-zinc-500">
                                Movement details
                              </div>

                              <div className="grid gap-3 text-sm md:grid-cols-3">
                                <div className="md:col-span-3">
                                  <div className="text-[11px] font-semibold uppercase tracking-wide text-zinc-500">
                                    Notes
                                  </div>
                                  <div className="mt-1 rounded-lg border border-zinc-200 bg-zinc-50 p-3 text-zinc-900">
                                    {m.notes || "No notes"}
                                  </div>
                                </div>

                                <div>
                                  <div className="text-[11px] font-semibold uppercase tracking-wide text-zinc-500">
                                    Source location
                                  </div>
                                  <div className="mt-1 font-medium text-zinc-900">
                                    {locationLabel(
                                      m.from_location_id,
                                      locationMap
                                    ) || "No source"}
                                  </div>
                                </div>

                                <div>
                                  <div className="text-[11px] font-semibold uppercase tracking-wide text-zinc-500">
                                    Destination
                                  </div>
                                  <div className="mt-1 font-medium text-zinc-900">
                                    {resolvedLocationName(
                                      m.to_location_id,
                                      locationMap
                                    )}
                                  </div>
                                </div>

                                <div>
                                  <div className="text-[11px] font-semibold uppercase tracking-wide text-zinc-500">
                                    Source
                                  </div>
                                  <div className="mt-1 font-medium text-zinc-900">
                                    {resolvedLocationName(
                                      m.from_location_id,
                                      locationMap
                                    )}
                                  </div>
                                </div>

                                <div>
                                  <div className="text-[11px] font-semibold uppercase tracking-wide text-zinc-500">
                                    Internal item
                                  </div>
                                  <div className="mt-1 font-medium text-zinc-900">
                                    {itemName(m, itemMap)}
                                  </div>
                                </div>

                                <div>
                                  <div className="text-[11px] font-semibold uppercase tracking-wide text-zinc-500">
                                    User
                                  </div>
                                  <div className="mt-1 font-medium text-zinc-900">
                                    {userFullName(m, userMap)}
                                  </div>
                                </div>

                                <div>
                                  <div className="text-[11px] font-semibold uppercase tracking-wide text-zinc-500">
                                    Detected aisle
                                  </div>
                                  <div className="mt-1 font-medium text-zinc-900">
                                    {detectedAisleName(m, locationMap)}
                                  </div>
                                </div>
                              </div>
                            </div>
                          </td>
                        </tr>
                      )}
                    </Fragment>
                  );
                })}

                {!loading && rows.length === 0 && (
                  <tr>
                    <td
                      colSpan={columnCount}
                      className="px-3 py-6 text-sm text-zinc-600"
                    >
                      No results
                    </td>
                  </tr>
                )}

                {loading && (
                  <tr>
                    <td
                      colSpan={columnCount}
                      className="px-3 py-6 text-sm text-zinc-600"
                    >
                      Loading movements…
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div className="text-sm text-zinc-600">
            Total{" "}
            <span className="font-semibold text-zinc-900">{meta.total}</span> •
            Page{" "}
            <span className="font-semibold text-zinc-900">{meta.page}</span> /{" "}
            <span className="font-semibold text-zinc-900">{pages}</span> • Size{" "}
            <span className="font-semibold text-zinc-900">
              {meta.pageSize}
            </span>
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
      </div>
    </AppShell>
  );
}
