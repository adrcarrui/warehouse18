import { useEffect, useMemo, useRef, useState } from "react";
import type { CSSProperties } from "react";
import { CheckCircle2, XCircle, Minus, Plus, Save } from "lucide-react";
import { apiGet, apiPost, apiJson } from "../api";
import type { PageMeta, PageOut } from "../api";
import { AppShell } from "../app/AppShell";
import { Button } from "../ui/Button";
import { Input } from "../ui/Input";

type MovementOut = {
  id: number;
  movement_type_id: number;
  item_id?: number | null;
  quantity?: string | number | null;
  from_location_id?: number | null;
  to_location_id?: number | null;
  reference_type?: string | null;
  reference_id?: number | null;
  user_id?: number | null;
  user_name?: string | null;
  created_at: string;
  notes?: string | null;
  item_key?: string | null;
  mysim_user_id?: number | null;
  detected_aisle_id?: number | null;
  review_status: string;
  reviewed_at?: string | null;
  reviewed_by_user_id?: number | null;
  review_note?: string | null;
  mysim_sync_status: string;
  mysim_synced_at?: string | null;
  mysim_sync_error?: string | null;
  mysim_movement_id?: string | null;
};

type MovementTypeOut = {
  id: number;
  code: string;
  name: string;
  stock_sign?: number | null;
};

type MovementReviewIn = {
  reviewed_by_user_id: number;
  note?: string | null;
};

type RFIDEventOut = {
  id: number;
  event_type: string;
  reason?: string | null;
  epc?: string | null;
  reader_id?: string | null;
  antenna?: number | null;
  door_id?: string | null;
  zone_id?: string | null;
  zone_role?: string | null;
  movement_code?: string | null;
  movement_id?: number | null;
  user_id?: number | null;
  mysim_user_id?: number | null;
  payload?: Record<string, unknown> | null;
  created_at: string;
  seen_at?: string | null;
  review_status: string;
  review_note?: string | null;
  reviewed_at?: string | null;
  reviewed_by_user_id?: number | null;
};

type RFIDEventReviewIn = {
  reviewed_by_user_id: number;
  note?: string | null;
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
  is_warehouse_location?: boolean;
};

type CandidateLocationsOut = {
  item_key: string;
  item_prefix: string;
  aisle_code: string;
  device_group_code: string;
  locations: LocationOut[];
};

type UserOut = {
  id: number;
  username: string;
  full_name: string;
  email?: string | null;
  role?: string;
  department?: string | null;
  is_active?: boolean;
};

type MovementCode = "GR" | "GT" | "GI";

type CandidateState = {
  data: CandidateLocationsOut | null;
  loading: boolean;
  error: string | null;
  settingDestinationId: number | null;
};

function unwrapApiData<T>(response: unknown): T {
  if (response && typeof response === "object" && "data" in response) {
    return (response as { data: T }).data;
  }

  return response as T;
}

function fmtDate(v?: string | null) {
  if (!v) return "";
  const d = new Date(v);
  if (Number.isNaN(d.getTime())) return v;
  return d.toLocaleString("en-GB");
}

function prettyJson(v: unknown) {
  try {
    return JSON.stringify(v, null, 2);
  } catch {
    return String(v);
  }
}

function toNumberOrZero(v: string) {
  const n = Number(v);
  return Number.isFinite(n) ? n : 0;
}

function locationLabel(
  locationId?: number | null,
  locationMap?: Record<number, LocationOut>
) {
  if (locationId == null) return "";

  const loc = locationMap?.[locationId];

  if (!loc) return "";

  return loc.name || loc.code || "";
}

function doneByLabel(row: MovementOut, userMap: Record<number, UserOut>) {
  if (row.user_name && row.user_name.trim() !== "") return row.user_name;

  if (row.user_id != null) {
    const user = userMap[row.user_id];

    if (user) {
      return user.full_name || user.username || String(row.user_id);
    }

    return String(row.user_id);
  }

  return "";
}

function sourceLabel(row: MovementOut, locationMap: Record<number, LocationOut>) {
  return locationLabel(row.from_location_id, locationMap);
}

function destinationLabel(row: MovementOut, locationMap: Record<number, LocationOut>) {
  return locationLabel(row.to_location_id, locationMap);
}

function movementTypeLabel(
  movementTypeId: number,
  movementTypeMap: Record<number, MovementTypeOut>
) {
  const mt = movementTypeMap[movementTypeId];

  if (!mt) return String(movementTypeId);

  const code = (mt.code || "").toUpperCase();

  if (code === "GI") return "Good Issue";
  if (code === "GR") return "Good Receipt";
  if (code === "GT") return "Good Transfer";

  return mt.name || mt.code || String(movementTypeId);
}

function movementCodeOf(
  movementTypeId: number,
  movementTypeMap: Record<number, MovementTypeOut>
): string {
  return (movementTypeMap[movementTypeId]?.code || "").toUpperCase();
}

function safeMovementCode(code: string): MovementCode {
  const normalized = (code || "").toUpperCase();

  if (normalized === "GR") return "GR";
  if (normalized === "GT") return "GT";
  if (normalized === "GI") return "GI";

  return "GR";
}

function movementSelectClassName(code: string) {
  const normalized = (code || "").toUpperCase();

  const base =
    "h-10 w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm font-semibold outline-none focus:border-zinc-500 disabled:bg-zinc-100 disabled:text-zinc-400";

  if (normalized === "GR") {
    return `${base} text-green-700`;
  }

  if (normalized === "GT") {
    return `${base} text-blue-700`;
  }

  if (normalized === "GI") {
    return `${base} text-red-700`;
  }

  return `${base} text-zinc-900`;
}

function movementOptionStyle(code: MovementCode): CSSProperties {
  if (code === "GR") {
    return {
      color: "#15803d",
      backgroundColor: "#dcfce7",
      fontWeight: 700,
    };
  }

  if (code === "GT") {
    return {
      color: "#1d4ed8",
      backgroundColor: "#dbeafe",
      fontWeight: 700,
    };
  }

  return {
    color: "#b91c1c",
    backgroundColor: "#fee2e2",
    fontWeight: 700,
  };
}

function destinationOptionLabel(loc: LocationOut) {
  const base = loc.name || loc.code;
  const rackShelf =
    loc.rack_code || loc.shelf_code
      ? ` · Rack ${loc.rack_code ?? "-"} · Shelf ${loc.shelf_code ?? "-"}`
      : "";
  const scope = loc.is_warehouse_location ? " · Warehouse" : " · Outside";

  return `${base}${rackShelf}${scope}`;
}

function noteField(notes: string | null | undefined, key: string): string {
  if (!notes) return "";

  const parts = notes.split("|").map((x) => x.trim());
  const prefix = `${key}=`;
  const found = parts.find((x) => x.startsWith(prefix));

  return found ? found.slice(prefix.length).trim() : "";
}

function emptyCandidateState(): CandidateState {
  return {
    data: null,
    loading: false,
    error: null,
    settingDestinationId: null,
  };
}

export default function RFIDReviewPage() {
  const [reviewerUserId, setReviewerUserId] = useState("1");
  const [confirmingMovementIds, setConfirmingMovementIds] = useState<number[]>([]);
  const [movementTypeUpdatingId, setMovementTypeUpdatingId] = useState<number | null>(null);

  const movementRejectNote = "Invalid reading or discarded movement";
  const eventRejectNote = "Incident reviewed and discarded";

  const [movementItemKeyFilter, setMovementItemKeyFilter] = useState("");
  const [movementUserFilter, setMovementUserFilter] = useState("");
  const [movementDateFromFilter, setMovementDateFromFilter] = useState("");
  const [movementDateToFilter, setMovementDateToFilter] = useState("");
  const [movementSourceFilter, setMovementSourceFilter] = useState("");
  const [movementDestinationFilter, setMovementDestinationFilter] = useState("");
  const [movementPage, setMovementPage] = useState(1);
  const [movementPageSize] = useState(25);

  const [movementRows, setMovementRows] = useState<MovementOut[]>([]);
  const [movementMeta, setMovementMeta] = useState<PageMeta>({
    page: 1,
    pageSize: 25,
    total: 0,
    pages: 0,
    link: null,
  });

  const [eventRows, setEventRows] = useState<RFIDEventOut[]>([]);

  const [loadingMovements, setLoadingMovements] = useState(false);
  const [loadingEvents, setLoadingEvents] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const [locationMap, setLocationMap] = useState<Record<number, LocationOut>>({});
  const [userMap, setUserMap] = useState<Record<number, UserOut>>({});
  const [movementTypeMap, setMovementTypeMap] = useState<Record<number, MovementTypeOut>>({});
  const [candidateByMovement, setCandidateByMovement] = useState<
    Record<number, CandidateState>
  >({});

  const [editingQty, setEditingQty] = useState<Record<number, string>>({});
  const [editingDescription, setEditingDescription] = useState<Record<number, string>>({});
  const [savingDescriptionIds, setSavingDescriptionIds] = useState<number[]>([]);
  const [expandedMovementIds, setExpandedMovementIds] = useState<number[]>([]);

  const movementRowsRef = useRef<MovementOut[]>([]);
  const movementMetaRef = useRef<PageMeta>({
    page: 1,
    pageSize: 25,
    total: 0,
    pages: 0,
    link: null,
  });
  const movementPageRef = useRef<number>(1);
  const candidateByMovementRef = useRef<Record<number, CandidateState>>({});

  const reviewerId = useMemo(() => toNumberOrZero(reviewerUserId), [reviewerUserId]);

  const movementQuery = useMemo(() => {
    return [movementItemKeyFilter.trim(), movementUserFilter.trim()]
      .filter(Boolean)
      .join(" ");
  }, [movementItemKeyFilter, movementUserFilter]);

  useEffect(() => {
    movementRowsRef.current = movementRows;
  }, [movementRows]);

  useEffect(() => {
    movementMetaRef.current = movementMeta;
  }, [movementMeta]);

  useEffect(() => {
    movementPageRef.current = movementPage;
  }, [movementPage]);

  useEffect(() => {
    candidateByMovementRef.current = candidateByMovement;
  }, [candidateByMovement]);

  function movementSnapshot(rows: MovementOut[]) {
    return rows.map((r) => ({
      id: r.id,
      movement_type_id: r.movement_type_id,
      from_location_id: r.from_location_id ?? null,
      to_location_id: r.to_location_id ?? null,
      quantity: r.quantity == null ? null : String(r.quantity),
      review_status: r.review_status,
      notes: r.notes ?? "",
      item_key: r.item_key ?? "",
      user_id: r.user_id ?? null,
      user_name: r.user_name ?? "",
      updated_like: [
        r.id,
        r.movement_type_id,
        r.from_location_id ?? null,
        r.to_location_id ?? null,
        r.quantity == null ? null : String(r.quantity),
        r.review_status,
        r.notes ?? "",
        r.item_key ?? "",
        r.user_id ?? null,
        r.user_name ?? "",
      ].join("|"),
    }));
  }

  async function loadUserMap() {
    try {
      const pageSize = 200;
      let currentPage = 1;
      let totalPages = 1;
      const next: Record<number, UserOut> = {};

      while (currentPage <= totalPages) {
        const { data, meta } = await apiGet<PageOut<UserOut>>("/api/users", {
          page: currentPage,
          page_size: pageSize,
        });

        for (const row of data.items) {
          next[row.id] = row;
        }

        totalPages =
          meta.pages && meta.pages > 0
            ? meta.pages
            : Math.max(1, Math.ceil((meta.total || 0) / (meta.pageSize || pageSize)));

        currentPage += 1;
      }

      setUserMap(next);
    } catch {
      setUserMap({});
    }
  }

  async function loadLocationMap() {
    try {
      const pageSize = 200;
      let currentPage = 1;
      let totalPages = 1;
      const next: Record<number, LocationOut> = {};

      while (currentPage <= totalPages) {
        const { data, meta } = await apiGet<PageOut<LocationOut>>("/api/locations", {
          include_inactive: true,
          page: currentPage,
          page_size: pageSize,
        });

        for (const row of data.items) {
          next[row.id] = row;
        }

        totalPages =
          meta.pages && meta.pages > 0
            ? meta.pages
            : Math.max(1, Math.ceil((meta.total || 0) / (meta.pageSize || pageSize)));

        currentPage += 1;
      }

      setLocationMap(next);
    } catch {
      setLocationMap({});
    }
  }

  async function loadMovementTypes() {
    try {
      const { data } = await apiGet<MovementTypeOut[]>("/api/movement-types");
      const next: Record<number, MovementTypeOut> = {};

      for (const row of data) {
        next[row.id] = row;
      }

      setMovementTypeMap(next);
    } catch {
      setMovementTypeMap({});
    }
  }

  async function loadCandidateLocations(row: MovementOut, force = false) {
    const current = candidateByMovementRef.current[row.id];

    if (!force && (current?.loading || current?.data || current?.error)) {
      return;
    }

    setCandidateByMovement((prev) => ({
      ...prev,
      [row.id]: {
        data: force ? null : prev[row.id]?.data ?? null,
        loading: true,
        error: null,
        settingDestinationId: prev[row.id]?.settingDestinationId ?? null,
      },
    }));

    try {
      const { data } = await apiGet<CandidateLocationsOut>(
        `/api/movements/${row.id}/candidate-locations`
      );

      setCandidateByMovement((prev) => ({
        ...prev,
        [row.id]: {
          data,
          loading: false,
          error: null,
          settingDestinationId: prev[row.id]?.settingDestinationId ?? null,
        },
      }));

      setLocationMap((prev) => {
        const next = { ...prev };

        for (const loc of data.locations) {
          next[loc.id] = loc;
        }

        return next;
      });
    } catch (e: any) {
      setCandidateByMovement((prev) => ({
        ...prev,
        [row.id]: {
          data: null,
          loading: false,
          error: e?.message ?? String(e),
          settingDestinationId: null,
        },
      }));
    }
  }

  async function setMovementType(row: MovementOut, movementTypeCode: MovementCode) {
    setErr(null);
    setMovementTypeUpdatingId(row.id);

    setCandidateByMovement((prev) => ({
      ...prev,
      [row.id]: {
        data: null,
        loading: true,
        error: null,
        settingDestinationId: null,
      },
    }));

    try {
      const response = await apiJson(
        "PATCH",
        `/api/movements/${row.id}/movement-type`,
        {
          movement_type_code: movementTypeCode,
        }
      );

      const updated = unwrapApiData<MovementOut>(response);

      setMovementRows((prev) =>
        prev.map((m) => (m.id === updated.id ? { ...m, ...updated } : m))
      );

      await loadCandidateLocations(updated, true);
    } catch (e: any) {
      setErr(e?.message ?? String(e));

      setCandidateByMovement((prev) => ({
        ...prev,
        [row.id]: {
          data: null,
          loading: false,
          error: e?.message ?? String(e),
          settingDestinationId: null,
        },
      }));
    } finally {
      setMovementTypeUpdatingId(null);
    }
  }

  async function setCandidateAsDestination(row: MovementOut, loc: LocationOut) {
    setErr(null);

    setCandidateByMovement((prev) => ({
      ...prev,
      [row.id]: {
        ...(prev[row.id] ?? emptyCandidateState()),
        settingDestinationId: loc.id,
        error: null,
      },
    }));

    try {
      const response = await apiJson(
        "PATCH",
        `/api/movements/${row.id}/destination`,
        {
          location_id: loc.id,
        }
      );

      const updated = unwrapApiData<MovementOut>(response);

      setLocationMap((prev) => ({
        ...prev,
        [loc.id]: loc,
      }));

      setMovementRows((prev) =>
        prev.map((m) => (m.id === updated.id ? { ...m, ...updated } : m))
      );
    } catch (e: any) {
      setCandidateByMovement((prev) => ({
        ...prev,
        [row.id]: {
          ...(prev[row.id] ?? emptyCandidateState()),
          error: e?.message ?? String(e),
        },
      }));
    } finally {
      setCandidateByMovement((prev) => ({
        ...prev,
        [row.id]: {
          ...(prev[row.id] ?? emptyCandidateState()),
          settingDestinationId: null,
        },
      }));
    }
  }

  async function handleDestinationSelect(row: MovementOut, value: string) {
    if (!value) return;

    const state = candidateByMovementRef.current[row.id];
    const locationId = Number(value);

    if (!Number.isFinite(locationId)) return;

    const loc = state?.data?.locations.find((x) => x.id === locationId);

    if (!loc) {
      setCandidateByMovement((prev) => ({
        ...prev,
        [row.id]: {
          ...(prev[row.id] ?? emptyCandidateState()),
          error: "Selected destination was not found in the candidate list",
        },
      }));

      return;
    }

    await setCandidateAsDestination(row, loc);
  }

  async function loadMovements(p: number, options?: { silent?: boolean }) {
    const silent = options?.silent ?? false;

    if (!silent) {
      setLoadingMovements(true);
      setErr(null);
    }

    try {
      const { data, meta } = await apiGet<PageOut<MovementOut>>("/api/movements", {
        review_status: "pending",
        q: movementQuery || undefined,
        from_date: movementDateFromFilter || undefined,
        to_date: movementDateToFilter || undefined,
        page: p,
        page_size: movementPageSize,
      });

      let items = data.items;

      if (movementSourceFilter.trim()) {
        const needle = movementSourceFilter.trim().toLowerCase();
        items = items.filter((row) =>
          sourceLabel(row, locationMap).toLowerCase().includes(needle)
        );
      }

      if (movementDestinationFilter.trim()) {
        const needle = movementDestinationFilter.trim().toLowerCase();
        items = items.filter((row) =>
          destinationLabel(row, locationMap).toLowerCase().includes(needle)
        );
      }

      const prevRows = movementRowsRef.current;
      const prevMeta = movementMetaRef.current;
      const prevPage = movementPageRef.current;

      const prevSnapshot = JSON.stringify(movementSnapshot(prevRows));
      const nextSnapshot = JSON.stringify(movementSnapshot(items));

      const metaChanged =
        prevMeta.page !== meta.page ||
        prevMeta.pageSize !== meta.pageSize ||
        prevMeta.total !== meta.total ||
        prevMeta.pages !== meta.pages;

      if (prevSnapshot !== nextSnapshot || metaChanged || prevPage !== p) {
        setMovementRows(items);
        setMovementMeta(meta);
        setMovementPage(p);
      }

      for (const item of items) {
        void loadCandidateLocations(item);
      }
    } catch (e: any) {
      if (!silent) {
        setErr(e?.message ?? String(e));
      } else {
        console.error("Silent movement refresh failed:", e);
      }
    } finally {
      if (!silent) {
        setLoadingMovements(false);
      }
    }
  }

  async function loadEvents() {
    setLoadingEvents(true);
    setErr(null);

    try {
      const { data } = await apiGet<RFIDEventOut[]>("/api/rfid/events/history", {
        review_status: "pending",
        has_movement: false,
        limit: 100,
      });

      setEventRows(data);
    } catch (e: any) {
      setErr(e?.message ?? String(e));
    } finally {
      setLoadingEvents(false);
    }
  }

  useEffect(() => {
    (async () => {
      await Promise.all([
        loadLocationMap(),
        loadMovementTypes(),
        loadUserMap(),
        loadEvents(),
      ]);

      await loadMovements(1);
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const intervalId = window.setInterval(() => {
      loadMovements(movementPageRef.current, { silent: true });
    }, 2000);

    return () => {
      window.clearInterval(intervalId);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    movementQuery,
    movementDateFromFilter,
    movementDateToFilter,
    movementSourceFilter,
    movementDestinationFilter,
    locationMap,
  ]);

  function currentDescriptionValue(row: MovementOut) {
    if (editingDescription[row.id] != null) {
      return editingDescription[row.id];
    }

    return row.notes ?? "";
  }

  function isMovementExpanded(movementId: number) {
    return expandedMovementIds.includes(movementId);
  }

  function toggleMovementExpanded(movementId: number) {
    setExpandedMovementIds((prev) =>
      prev.includes(movementId)
        ? prev.filter((id) => id !== movementId)
        : [...prev, movementId]
    );
  }

  async function saveMovementDescription(row: MovementOut) {
    if (savingDescriptionIds.includes(row.id)) return;

    setErr(null);
    setSavingDescriptionIds((prev) => [...prev, row.id]);

    try {
      const notes = currentDescriptionValue(row).trim();

      const response = await apiJson(
        "PATCH",
        `/api/movements/${row.id}/description`,
        {
          notes,
        }
      );

      const updated = unwrapApiData<MovementOut>(response);

      setMovementRows((prev) =>
        prev.map((m) => (m.id === updated.id ? { ...m, ...updated } : m))
      );

      setEditingDescription((prev) => {
        const next = { ...prev };
        delete next[row.id];
        return next;
      });
    } catch (e: any) {
      setErr(e?.message ?? String(e));
    } finally {
      setSavingDescriptionIds((prev) => prev.filter((id) => id !== row.id));
    }
  }

  function currentQtyValue(row: MovementOut, editingQtyMap: Record<number, string>) {
    if (editingQtyMap[row.id] != null) return editingQtyMap[row.id];
    if (row.quantity == null || row.quantity === "") return "1";
    return String(row.quantity);
  }

  async function saveMovementQuantity(row: MovementOut) {
    setErr(null);

    try {
      const raw = editingQty[row.id] ?? (row.quantity == null ? "1" : String(row.quantity));
      const qty = Number(raw);

      if (!Number.isFinite(qty) || qty <= 0) {
        setErr("Quantity must be greater than zero");
        return;
      }

      await apiJson("PATCH", `/api/movements/${row.id}/quantity`, {
        quantity: qty,
      });

      await loadMovements(movementPageRef.current);

      setEditingQty((prev) => {
        const next = { ...prev };
        delete next[row.id];
        return next;
      });
    } catch (e: any) {
      setErr(e?.message ?? String(e));
    }
  }

  async function confirmMovement(row: MovementOut) {
    if (confirmingMovementIds.includes(row.id)) return;

    setErr(null);
    setConfirmingMovementIds((prev) => [...prev, row.id]);

    try {
      const payload: MovementReviewIn = {
        reviewed_by_user_id: reviewerId,
        note: "Validated manually",
      };

      await apiPost(`/api/movements/${row.id}/confirm`, payload);
      await loadMovements(movementPageRef.current);
      await loadEvents();
    } catch (e: any) {
      setErr(e?.message ?? String(e));
    } finally {
      setConfirmingMovementIds((prev) => prev.filter((id) => id !== row.id));
    }
  }

  async function rejectMovement(row: MovementOut) {
    setErr(null);

    try {
      const payload: MovementReviewIn = {
        reviewed_by_user_id: reviewerId,
        note: movementRejectNote,
      };

      await apiPost(`/api/movements/${row.id}/reject`, payload);
      await loadMovements(movementPageRef.current);
      await loadEvents();
    } catch (e: any) {
      setErr(e?.message ?? String(e));
    }
  }

  async function confirmEvent(row: RFIDEventOut) {
    setErr(null);

    try {
      const payload: RFIDEventReviewIn = {
        reviewed_by_user_id: reviewerId,
        note: "Incident reviewed",
      };

      await apiPost(`/api/rfid/events/${row.id}/confirm`, payload);
      await loadEvents();
    } catch (e: any) {
      setErr(e?.message ?? String(e));
    }
  }

  async function rejectEvent(row: RFIDEventOut) {
    setErr(null);

    try {
      const payload: RFIDEventReviewIn = {
        reviewed_by_user_id: reviewerId,
        note: eventRejectNote,
      };

      await apiPost(`/api/rfid/events/${row.id}/reject`, payload);
      await loadEvents();
    } catch (e: any) {
      setErr(e?.message ?? String(e));
    }
  }

  const movementPages = useMemo(() => {
    const ps = movementMeta.pageSize || movementPageSize || 25;
    const t = movementMeta.total || 0;
    const computed = Math.max(1, Math.ceil(t / ps));
    return movementMeta.pages && movementMeta.pages > 0 ? movementMeta.pages : computed;
  }, [movementMeta.pages, movementMeta.pageSize, movementMeta.total, movementPageSize]);

  return (
    <AppShell
      title="RFID Review"
      subtitle="Manual review of pending movements and unusual RFID events"
    //actions={
    //  <div className="flex items-center gap-2">
    //    <div className="flex items-center gap-2 text-xs text-zinc-600">
    //      <span>Reviewer</span>
    //      <Input
    //        value={reviewerUserId}
    //       onChange={(e) => setReviewerUserId(e.target.value)}
    //        className="w-20"
    //      />
    //    </div>

    //    <Button variant="outline" onClick={() => loadMovements(1)} disabled={loadingMovements}>
    //      Reload movements
    //    </Button>
    //  </div >
    //}
    >
      <div className="space-y-6">
        {err && (
          <div className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            Error: {err}
          </div>
        )}

        <div className="rounded-xl border border-zinc-200 bg-white">
          <div className="border-b border-zinc-200 px-4 py-3">
            <div className="text-sm font-semibold text-zinc-900">Pending Movements</div>
            <div className="mt-1 text-xs text-zinc-500">
              Review each RFID movement, adjust the type, select the destination, then confirm
            </div>
          </div>
          {/*}
          <div className="border-b border-zinc-200 bg-zinc-50/50 px-4 py-4">
            <div className="grid gap-3 xl:grid-cols-[1.1fr_1fr_1fr_1fr_auto]">
              <div>
                <label className="mb-1 block text-xs font-semibold text-zinc-600">
                  Part or notes
                </label>
                <Input
                  value={movementItemKeyFilter}
                  onChange={(e) => setMovementItemKeyFilter(e.target.value)}
                  placeholder="Part ID, EPC, notes…"
                />
              </div>

              <div>
                <label className="mb-1 block text-xs font-semibold text-zinc-600">
                  From date
                </label>
                <Input
                  type="date"
                  value={movementDateFromFilter}
                  onChange={(e) => setMovementDateFromFilter(e.target.value)}
                />
              </div>

              <div>
                <label className="mb-1 block text-xs font-semibold text-zinc-600">
                  To date
                </label>
                <Input
                  type="date"
                  value={movementDateToFilter}
                  onChange={(e) => setMovementDateToFilter(e.target.value)}
                />
              </div>

              <div>
                <label className="mb-1 block text-xs font-semibold text-zinc-600">
                  Done by
                </label>
                <Input
                  value={movementUserFilter}
                  onChange={(e) => setMovementUserFilter(e.target.value)}
                  placeholder="Operator…"
                />
              </div>

              <div className="flex items-end">
                <Button
                  variant="outline"
                  onClick={() => loadMovements(1)}
                  disabled={loadingMovements}
                >
                  Search
                </Button>
              </div>
            </div>

            <div className="mt-3 grid gap-3 md:grid-cols-2">
              <Input
                value={movementSourceFilter}
                onChange={(e) => setMovementSourceFilter(e.target.value)}
                placeholder="Filter source…"
              />
              <Input
                value={movementDestinationFilter}
                onChange={(e) => setMovementDestinationFilter(e.target.value)}
                placeholder="Filter destination…"
              />
            </div>
          </div>
          */}
          <div className="grid items-start gap-3 p-4 xl:grid-cols-3">
            {movementRows.map((r) => {
              const rowMovementCode = safeMovementCode(
                movementCodeOf(r.movement_type_id, movementTypeMap)
              );

              const candidateState = candidateByMovement[r.id] ?? emptyCandidateState();
              const candidateLocations = candidateState.data?.locations ?? [];
              const destinationDisabled =
                candidateState.loading ||
                candidateState.settingDestinationId !== null ||
                movementTypeUpdatingId === r.id ||
                candidateLocations.length === 0;

              const logicalName = noteField(r.notes, "logical_name");
              const aisleCode = noteField(r.notes, "aisle_code");

              return (
                <div
                  key={r.id}
                  className="w-fit max-w-[475px] justify-self-start rounded-2xl border border-zinc-200 bg-white p-4 shadow-sm"
                >
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="rounded-full bg-blue-900 px-2.5 py-1 text-xs font-semibold text-white">
                        #{r.id}
                      </span>

                      <span className="text-base font-semibold text-zinc-950">
                        {r.item_key || "No Part ID"}
                      </span>
                    </div>

                    <div className="mt-1 text-sm text-zinc-500">
                      {fmtDate(r.created_at)}
                    </div>
                  </div>

                  <div className="mt-2 grid gap-3">
                    <div className="space-y-3">
                      <div className="grid gap-2 md:grid-cols-[180px_195px_48px] md:justify-start">
                        <div className="rounded-xl border border-zinc-200 bg-zinc-50 p-3">
                          <div className="text-[11px] font-semibold uppercase tracking-wide text-zinc-500">
                            Movement Type
                          </div>

                          <div className="mt-1 flex h-10 items-center">
                            <select
                              value={rowMovementCode}
                              disabled={movementTypeUpdatingId === r.id}
                              onChange={(e) => {
                                const nextCode = e.target.value as MovementCode;

                                if (nextCode !== rowMovementCode) {
                                  void setMovementType(r, nextCode);
                                }
                              }}
                              className={`${movementSelectClassName(rowMovementCode)} h-10`}
                            >
                              <option value="GR" style={movementOptionStyle("GR")}>
                                Good Receipt
                              </option>

                              <option value="GT" style={movementOptionStyle("GT")}>
                                Good Transfer
                              </option>

                              <option value="GI" style={movementOptionStyle("GI")}>
                                Good Issue
                              </option>
                            </select>
                          </div>
                        </div>

                        <div className="rounded-xl border border-zinc-200 bg-zinc-50 p-3">
                          <div className="text-[11px] font-semibold uppercase tracking-wide text-zinc-500">
                            Destination
                          </div>

                          <div className="mt-1 flex h-10 items-center">
                            <select
                              value={r.to_location_id != null ? String(r.to_location_id) : ""}
                              disabled={destinationDisabled}
                              onChange={(e) => {
                                void handleDestinationSelect(r, e.target.value);
                              }}
                              className="h-10 w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900 outline-none focus:border-zinc-500 disabled:bg-zinc-100 disabled:text-zinc-400"
                            >
                              <option value="">
                                {candidateState.loading
                                  ? "Loading destinations…"
                                  : candidateLocations.length === 0
                                    ? "No valid destinations"
                                    : "Select destination…"}
                              </option>

                              {candidateLocations.map((loc) => (
                                <option key={loc.id} value={loc.id}>
                                  {destinationOptionLabel(loc)}
                                </option>
                              ))}
                            </select>
                          </div>
                        </div>

                        <div
                          title="Actions"
                          className="flex w-12 flex-col items-center justify-center gap-2 rounded-xl border border-zinc-200 bg-zinc-50 p-1.5 xl:row-span-2"
                        >
                          <span className="sr-only">Actions</span>

                          <button
                            type="button"
                            onClick={() => toggleMovementExpanded(r.id)}
                            title={
                              isMovementExpanded(r.id)
                                ? "Hide movement details"
                                : "Show movement details"
                            }
                            className="flex h-9 w-9 items-center justify-center rounded-lg border border-blue-600 bg-blue-600 text-white hover:bg-blue-700"
                          >
                            {isMovementExpanded(r.id) ? (
                              <Minus className="h-4 w-4" />
                            ) : (
                              <Plus className="h-4 w-4" />
                            )}
                            <span className="sr-only">
                              {isMovementExpanded(r.id)
                                ? "Hide movement details"
                                : "Show movement details"}
                            </span>
                          </button>

                          {r.to_location_id != null && (
                            <button
                              type="button"
                              onClick={() => confirmMovement(r)}
                              disabled={confirmingMovementIds.includes(r.id)}
                              title="Confirm movement"
                              className="flex h-9 w-9 items-center justify-center rounded-lg border border-green-600 bg-green-600 text-white hover:bg-green-700 disabled:opacity-60"
                            >
                              <CheckCircle2 className="h-4 w-4" />
                              <span className="sr-only">Confirm movement</span>
                            </button>
                          )}

                          <button
                            type="button"
                            onClick={() => rejectMovement(r)}
                            title="Reject movement"
                            className="flex h-9 w-9 items-center justify-center rounded-lg border border-red-600 bg-red-600 text-white hover:bg-red-700"
                          >
                            <XCircle className="h-4 w-4" />
                            <span className="sr-only">Reject movement</span>
                          </button>
                        </div>

                        <div className="rounded-xl border border-zinc-200 bg-zinc-50 p-3">
                          <div className="text-[11px] font-semibold uppercase tracking-wide text-zinc-500">
                            Done by
                          </div>

                          <div className="mt-1 flex h-10 items-center text-sm font-medium text-zinc-900">
                            {doneByLabel(r, userMap) || ""}
                          </div>
                        </div>

                        <div className="rounded-xl border border-zinc-200 bg-zinc-50 p-3">
                          <div className="text-[11px] font-semibold uppercase tracking-wide text-zinc-500">
                            Quantity
                          </div>

                          <div className="mt-1 flex h-10 items-center gap-2">
                            <input
                              type="number"
                              min="1"
                              step="1"
                              value={currentQtyValue(r, editingQty)}
                              onChange={(e) =>
                                setEditingQty((prev) => ({
                                  ...prev,
                                  [r.id]: e.target.value,
                                }))
                              }
                              className="h-10 w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900 outline-none focus:border-zinc-500"
                            />

                            <button
                              type="button"
                              onClick={() => saveMovementQuantity(r)}
                              className="h-10 rounded-lg border border-zinc-300 bg-white px-4 text-sm font-medium text-zinc-900 hover:bg-zinc-50"
                            >
                              Save
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>


                  </div>

                  {isMovementExpanded(r.id) && (
                    <div className="mt-2 grid gap-2 md:grid-cols-[180px_195px_48px] md:justify-start">
                      <div className="rounded-xl border border-zinc-200 bg-zinc-50 p-3 md:col-span-3">
                        <div className="grid gap-2 md:grid-cols-[180px_195px_48px]">
                          <div className="md:col-span-2">
                            <label className="mb-2 block text-[11px] font-semibold uppercase tracking-wide text-zinc-500">
                              Description
                            </label>

                            <textarea
                              value={currentDescriptionValue(r)}
                              onChange={(e) =>
                                setEditingDescription((prev) => ({
                                  ...prev,
                                  [r.id]: e.target.value,
                                }))
                              }
                              rows={5}
                              className="mt-2 w-[calc(100%-10px)] resize-y rounded-lg border border-zinc-300 bg-white px-2 py-1 text-sm text-zinc-900 outline-none focus:border-zinc-500 disabled:bg-zinc-100 disabled:text-zinc-400"
                              placeholder="Movement description..."
                            />
                          </div>

                          <div className="flex w-12 -translate-x-4 justify-center pt-[29px]">
                            <button
                              type="button"
                              onClick={() => saveMovementDescription(r)}
                              disabled={savingDescriptionIds.includes(r.id)}
                              title="Save description"
                              className="flex h-9 w-9 items-center justify-center rounded-lg border border-zinc-900 bg-zinc-900 text-white hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-60"
                            >
                              <Save className="h-4 w-4" />

                              <span className="sr-only">
                                {savingDescriptionIds.includes(r.id)
                                  ? "Saving description"
                                  : "Save description"}
                              </span>
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}

              {!loadingMovements && movementRows.length === 0 && (
                <div className="col-span-full flex min-h-[120px] w-full items-center justify-center rounded-xl border border-zinc-200 bg-zinc-50 px-4 py-8 text-center text-sm text-zinc-600">
                  No pending movements
                </div>
              )}

              {loadingMovements && (
                <div className="col-span-full flex min-h-[120px] w-full items-center justify-center rounded-xl border border-zinc-200 bg-zinc-50 px-4 py-8 text-center text-sm text-zinc-600">
                  Loading movements…
                </div>
              )}
          </div>

          <div className="flex flex-col gap-2 border-t border-zinc-200 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="text-sm text-zinc-600">
              Total <span className="font-semibold text-zinc-900">{movementMeta.total}</span> ·
              Page <span className="font-semibold text-zinc-900">{movementMeta.page}</span> /{" "}
              <span className="font-semibold text-zinc-900">{movementPages}</span> · Size{" "}
              <span className="font-semibold text-zinc-900">{movementMeta.pageSize}</span>
            </div>

            <div className="flex items-center gap-2">
              <Button
                onClick={() => loadMovements(movementMeta.page - 1)}
                disabled={loadingMovements || movementMeta.page <= 1}
              >
                Prev
              </Button>
              <Button
                onClick={() => loadMovements(movementMeta.page + 1)}
                disabled={loadingMovements || movementMeta.page >= movementPages}
              >
                Next
              </Button>
            </div>
          </div>
        </div>

        {eventRows.length > 0 && (
          <div className="rounded-xl border border-zinc-200 bg-white">
            <div className="border-b border-zinc-200 px-4 py-3">
              <div className="text-sm font-semibold text-zinc-900">Pending RFID Events</div>
              <div className="mt-1 text-xs text-zinc-500">
                Unusual RFID events awaiting review
                {loadingEvents ? " · Loading…" : ""}
              </div>
            </div>

            <div className="overflow-auto">
              <table className="min-w-full border-separate border-spacing-0">
                <thead className="bg-zinc-50">
                  <tr>
                    {["ID", "Date", "Type", "Reason", "EPC", "Door", "Payload", "Actions"].map(
                      (h) => (
                        <th
                          key={h}
                          className="border-b border-zinc-200 px-3 py-2 text-left text-xs font-semibold text-zinc-700"
                        >
                          {h}
                        </th>
                      )
                    )}
                  </tr>
                </thead>

                <tbody>
                  {eventRows.map((r) => (
                    <tr key={r.id} className="hover:bg-zinc-50">
                      <td className="border-b border-zinc-100 px-3 py-2 text-sm font-medium">
                        {r.id}
                      </td>
                      <td className="border-b border-zinc-100 px-3 py-2 text-sm">
                        {fmtDate(r.created_at)}
                      </td>
                      <td className="border-b border-zinc-100 px-3 py-2 text-sm">
                        {r.event_type}
                      </td>
                      <td className="border-b border-zinc-100 px-3 py-2 text-sm">
                        {r.reason || ""}
                      </td>
                      <td className="border-b border-zinc-100 px-3 py-2 text-sm">
                        {r.epc || ""}
                      </td>
                      <td className="border-b border-zinc-100 px-3 py-2 text-sm">
                        {r.door_id || ""}
                      </td>
                      <td className="border-b border-zinc-100 px-3 py-2 text-xs">
                        <pre className="max-w-[360px] whitespace-pre-wrap break-words">
                          {prettyJson(r.payload)}
                        </pre>
                      </td>
                      <td className="border-b border-zinc-100 px-3 py-2 text-sm">
                        <div className="flex flex-wrap gap-2">
                          <Button variant="outline" size="sm" onClick={() => confirmEvent(r)}>
                            Confirm
                          </Button>
                          <Button variant="danger" size="sm" onClick={() => rejectEvent(r)}>
                            Reject
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}
