import { useEffect, useMemo, useRef, useState } from "react";
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

type MovementLocationsUpdateIn = {
  from_location_id?: number | null;
  to_location_id?: number | null;
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
};

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

function locationLabel(locationId?: number | null, locationMap?: Record<number, LocationOut>) {
  if (locationId == null) return "";
  const loc = locationMap?.[locationId];
  return loc?.name || `${locationId}`;
}

function doneByLabel(row: MovementOut) {
  if (row.user_name && row.user_name.trim() !== "") return row.user_name;
  if (row.mysim_user_id != null) return String(row.mysim_user_id);
  if (row.user_id != null) return String(row.user_id);
  return "";
}

function quantityLabel(row: MovementOut) {
  if (row.quantity == null || row.quantity === "") return "1";
  return String(row.quantity);
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

function movementTypeClassName(
  movementTypeId: number,
  movementTypeMap: Record<number, MovementTypeOut>
) {
  const mt = movementTypeMap[movementTypeId];
  const code = (mt?.code || "").toUpperCase();

  if (code === "GI") return "text-red-600 font-semibold";
  if (code === "GR") return "text-green-600 font-semibold";
  if (code === "GT") return "text-blue-600 font-semibold";

  return "text-black";
}

type LocationAutocompleteProps = {
  label: string;
  valueText: string;
  onTextChange: (v: string) => void;
  onSelect: (loc: LocationOut) => void;
  suggestions: LocationOut[];
};

function LocationAutocomplete({
  label,
  valueText,
  onTextChange,
  onSelect,
  suggestions,
}: LocationAutocompleteProps) {
  return (
    <div className="relative">
      <div className="mb-1 text-xs font-semibold text-zinc-700">{label}</div>
      <Input
        value={valueText}
        onChange={(e) => onTextChange(e.target.value)}
        placeholder="Type a location name…"
      />
      {valueText.trim() !== "" && suggestions.length > 0 && (
        <div className="absolute z-50 mt-1 max-h-52 w-full overflow-auto rounded-xl border border-zinc-200 bg-white shadow-lg">
          {suggestions.map((loc) => (
            <button
              key={loc.id}
              type="button"
              onClick={() => onSelect(loc)}
              className="block w-full border-b border-zinc-100 px-3 py-2 text-left text-sm hover:bg-zinc-50"
            >
              <div className="font-medium text-black">{loc.name}</div>
              <div className="text-xs text-zinc-500">
                #{loc.id} • {loc.code} • {loc.type}
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

export default function RFIDReviewPage() {
  const [reviewerUserId, setReviewerUserId] = useState("1");
  const [confirmingMovementIds, setConfirmingMovementIds] = useState<number[]>([]);
  const [movementRejectNote, setMovementRejectNote] = useState(
    "Invalid reading or discarded movement"
  );
  const [eventRejectNote, setEventRejectNote] = useState(
    "Incident reviewed and discarded"
  );

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

  const [eventDoorFilter, setEventDoorFilter] = useState("");
  const [eventEpcFilter, setEventEpcFilter] = useState("");
  const [eventTypeFilter, setEventTypeFilter] = useState("");
  const [eventRows, setEventRows] = useState<RFIDEventOut[]>([]);

  const [loadingMovements, setLoadingMovements] = useState(false);
  const [loadingEvents, setLoadingEvents] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const [locationEditorOpen, setLocationEditorOpen] = useState(false);
  const [editingMovement, setEditingMovement] = useState<MovementOut | null>(null);

  const [locFromText, setLocFromText] = useState("");
  const [locToText, setLocToText] = useState("");
  const [locFromId, setLocFromId] = useState<number | null>(null);
  const [locToId, setLocToId] = useState<number | null>(null);
  const [fromSuggestions, setFromSuggestions] = useState<LocationOut[]>([]);
  const [toSuggestions, setToSuggestions] = useState<LocationOut[]>([]);
  const [locationMap, setLocationMap] = useState<Record<number, LocationOut>>({});
  const [movementTypeMap, setMovementTypeMap] = useState<Record<number, MovementTypeOut>>({});

  const fromDebounceRef = useRef<number | null>(null);
  const toDebounceRef = useRef<number | null>(null);

  const reviewerId = useMemo(() => toNumberOrZero(reviewerUserId), [reviewerUserId]);

  const movementQuery = useMemo(() => {
    return [movementItemKeyFilter.trim(), movementUserFilter.trim()].filter(Boolean).join(" ");
  }, [movementItemKeyFilter, movementUserFilter]);

  const [editingQty, setEditingQty] = useState<Record<number, string>>({});

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
      for (const row of data) next[row.id] = row;
      setMovementTypeMap(next);
    } catch {
      setMovementTypeMap({});
    }
  }

  async function searchLocations(term: string): Promise<LocationOut[]> {
    const q = term.trim();
    if (!q) return [];
    const { data } = await apiGet<PageOut<LocationOut>>("/api/locations", {
      q,
      include_inactive: false,
      page: 1,
      page_size: 8,
    });
    return data.items;
  }

  async function loadMovements(p: number) {
    setLoadingMovements(true);
    setErr(null);

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

      setMovementRows(items);
      setMovementMeta(meta);
      setMovementPage(p);
    } catch (e: any) {
      setErr(e?.message ?? String(e));
    } finally {
      setLoadingMovements(false);
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
        door_id: eventDoorFilter.trim() || undefined,
        epc: eventEpcFilter.trim() || undefined,
      });

      let items = data;

      if (eventTypeFilter.trim()) {
        const needle = eventTypeFilter.trim().toLowerCase();
        items = items.filter((x) => (x.event_type || "").toLowerCase().includes(needle));
      }

      setEventRows(items);
    } catch (e: any) {
      setErr(e?.message ?? String(e));
    } finally {
      setLoadingEvents(false);
    }
  }

  useEffect(() => {
    (async () => {
      await loadLocationMap();
      await loadMovementTypes();
      await loadMovements(1);
      await loadEvents();
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (Object.keys(locationMap).length > 0) {
      loadMovements(1);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [locationMap]);

  useEffect(() => {
    if (!locationEditorOpen) return;
    if (fromDebounceRef.current) window.clearTimeout(fromDebounceRef.current);

    fromDebounceRef.current = window.setTimeout(async () => {
      try {
        const items = await searchLocations(locFromText);
        setFromSuggestions(items);
      } catch {
        setFromSuggestions([]);
      }
    }, 250);

    return () => {
      if (fromDebounceRef.current) window.clearTimeout(fromDebounceRef.current);
    };
  }, [locFromText, locationEditorOpen]);

  useEffect(() => {
    if (!locationEditorOpen) return;
    if (toDebounceRef.current) window.clearTimeout(toDebounceRef.current);

    toDebounceRef.current = window.setTimeout(async () => {
      try {
        const items = await searchLocations(locToText);
        setToSuggestions(items);
      } catch {
        setToSuggestions([]);
      }
    }, 250);

    return () => {
      if (toDebounceRef.current) window.clearTimeout(toDebounceRef.current);
    };
  }, [locToText, locationEditorOpen]);

  function currentQtyValue(row: MovementOut, editingQty: Record<number, string>) {
    if (editingQty[row.id] != null) return editingQty[row.id];
    if (row.quantity == null || row.quantity === "") return "1";
    return String(row.quantity);
  }

  function openLocationEditor(row: MovementOut) {
    setEditingMovement(row);
    setLocFromId(row.from_location_id ?? null);
    setLocToId(row.to_location_id ?? null);
    setLocFromText(
      row.from_location_id
        ? locationMap[row.from_location_id]?.name || String(row.from_location_id)
        : ""
    );
    setLocToText(
      row.to_location_id
        ? locationMap[row.to_location_id]?.name || String(row.to_location_id)
        : ""
    );
    setFromSuggestions([]);
    setToSuggestions([]);
    setLocationEditorOpen(true);
  }

  function closeLocationEditor() {
    setLocationEditorOpen(false);
    setEditingMovement(null);
    setLocFromText("");
    setLocToText("");
    setLocFromId(null);
    setLocToId(null);
    setFromSuggestions([]);
    setToSuggestions([]);
  }

  async function saveMovementLocations() {
    if (!editingMovement) return;
    setErr(null);

    try {
      const payload: MovementLocationsUpdateIn = {
        from_location_id: locFromId,
        to_location_id: locToId,
      };

      await apiJson("PATCH", `/api/movements/${editingMovement.id}/locations`, payload);
      closeLocationEditor();
      await loadLocationMap();
      await loadMovements(movementPage);
      await loadEvents();
    } catch (e: any) {
      setErr(e?.message ?? String(e));
    }
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

      await loadMovements(movementPage);

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
      await loadMovements(movementPage);
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
        note: movementRejectNote.trim() || "Rejected manually",
      };
      await apiPost(`/api/movements/${row.id}/reject`, payload);
      await loadMovements(movementPage);
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
        note: eventRejectNote.trim() || "Rejected manually",
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

  const FILTER_ROW_TOP = "32px";

  return (
    <AppShell
      title="RFID Review"
      subtitle="Manual review of pending movements and unusual RFID events"
      actions={
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => loadMovements(1)} disabled={loadingMovements}>
            Reload movements
          </Button>
          {/*
          <Button variant="outline" onClick={() => loadEvents()} disabled={loadingEvents}>
            Reload events
          </Button>
          */}
        </div>
      }
    >
      <div className="space-y-6">
        {err && (
          <div className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            Error: {err}
          </div>
        )}
        {/*
        <div className="rounded-xl border border-zinc-200 bg-white p-4">
          <div className="grid gap-3 md:grid-cols-3">
            <div>
              <div className="mb-1 text-xs font-semibold text-zinc-700">Reviewer User ID</div>
              <Input
                value={reviewerUserId}
                onChange={(e) => setReviewerUserId(e.target.value)}
                placeholder="Reviewer user id"
              />
            </div>

            <div>
              <div className="mb-1 text-xs font-semibold text-zinc-700">Movement Reject Note</div>
              <Input
                value={movementRejectNote}
                onChange={(e) => setMovementRejectNote(e.target.value)}
                placeholder="Invalid reading or discarded movement"
              />
            </div>

            <div>
              <div className="mb-1 text-xs font-semibold text-zinc-700">Event Reject Note</div>
              <Input
                value={eventRejectNote}
                onChange={(e) => setEventRejectNote(e.target.value)}
                placeholder="Incident reviewed and discarded"
              />
            </div>
          </div>
        </div>
          */}
        <div className="rounded-xl border border-zinc-200 bg-white">
          <div className="border-b border-zinc-200 px-4 py-3">
            <div className="text-sm font-semibold text-zinc-900">Pending Movements</div>
            <div className="mt-1 text-xs text-zinc-500">
              Queue of RFID movements awaiting manual confirmation
            </div>
          </div>

          <div className="relative max-h-[750px] overflow-auto bg-white">
            <table className="min-w-full border-separate border-spacing-0 [table-layout:fixed]">
              <thead>
                <tr>
                  {[
                    "ID",
                    "Date",
                    "Part ID",
                    "Movement Type",
                    "Description",
                    "Source",
                    "Destination",
                    "Done By",
                    "Quantity",
                    "Actions",
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
                  />
                  <th
                    className="sticky z-20 border-b border-zinc-200 bg-white px-3 py-2"
                    style={{ top: FILTER_ROW_TOP }}
                  >
                    <div className="grid gap-2">
                      <Input
                        type="date"
                        value={movementDateFromFilter}
                        onChange={(e) => setMovementDateFromFilter(e.target.value)}
                      />
                      <Input
                        type="date"
                        value={movementDateToFilter}
                        onChange={(e) => setMovementDateToFilter(e.target.value)}
                      />
                    </div>
                  </th>
                  <th
                    className="sticky z-20 border-b border-zinc-200 bg-white px-3 py-2"
                    style={{ top: FILTER_ROW_TOP }}
                  >
                    <Input
                      value={movementItemKeyFilter}
                      onChange={(e) => setMovementItemKeyFilter(e.target.value)}
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
                  />
                  <th
                    className="sticky z-20 border-b border-zinc-200 bg-white px-3 py-2"
                    style={{ top: FILTER_ROW_TOP }}
                  >
                    <Input
                      value={movementSourceFilter}
                      onChange={(e) => setMovementSourceFilter(e.target.value)}
                      placeholder="Source…"
                    />
                  </th>
                  <th
                    className="sticky z-20 border-b border-zinc-200 bg-white px-3 py-2"
                    style={{ top: FILTER_ROW_TOP }}
                  >
                    <Input
                      value={movementDestinationFilter}
                      onChange={(e) => setMovementDestinationFilter(e.target.value)}
                      placeholder="Destination…"
                    />
                  </th>
                  <th
                    className="sticky z-20 border-b border-zinc-200 bg-white px-3 py-2"
                    style={{ top: FILTER_ROW_TOP }}
                  >
                    <Input
                      value={movementUserFilter}
                      onChange={(e) => setMovementUserFilter(e.target.value)}
                      placeholder="Done by…"
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
                    <div className="flex justify-end">
                      <Button
                        variant="outline"
                        onClick={() => loadMovements(1)}
                        disabled={loadingMovements}
                      >
                        Search
                      </Button>
                    </div>
                  </th>
                </tr>
              </thead>

              <tbody>
                {movementRows.map((r) => (
                  <tr key={r.id} className="hover:bg-zinc-50">
                    <td className="border-b border-zinc-100 px-3 py-2 text-sm font-medium text-black">
                      {r.id}
                    </td>

                    <td className="border-b border-zinc-100 px-3 py-2 text-sm text-black whitespace-nowrap">
                      {fmtDate(r.created_at)}
                    </td>

                    <td className="border-b border-zinc-100 px-3 py-2 text-sm text-black">
                      {r.item_key || ""}
                    </td>

                    <td
                      className={`border-b border-zinc-100 px-3 py-2 text-sm ${movementTypeClassName(
                        r.movement_type_id,
                        movementTypeMap
                      )}`}
                    >
                      {movementTypeLabel(r.movement_type_id, movementTypeMap)}
                    </td>

                    <td className="border-b border-zinc-100 px-3 py-2 text-xs text-black">
                      <div className="max-w-[360px] whitespace-pre-wrap break-words">
                        {r.notes || ""}
                      </div>
                    </td>

                    <td className="border-b border-zinc-100 px-3 py-2 text-sm text-black">
                      {locationLabel(r.from_location_id, locationMap)}
                    </td>

                    <td className="border-b border-zinc-100 px-3 py-2 text-sm text-black">
                      {locationLabel(r.to_location_id, locationMap)}
                    </td>

                    <td className="border-b border-zinc-100 px-3 py-2 text-sm text-black">
                      {doneByLabel(r)}
                    </td>

                    <td className="border-b border-zinc-100 px-3 py-2 text-sm text-black">
                      <div className="flex items-center gap-2">
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
                          className="w-20 rounded border border-zinc-300 px-2 py-1 text-sm"
                        />
                        <Button variant="outline" size="sm" onClick={() => saveMovementQuantity(r)}>
                          Save
                        </Button>
                      </div>
                    </td>

                    <td className="border-b border-zinc-100 px-3 py-2 text-sm text-black">
                      <div className="flex flex-wrap gap-2">
                        <Button variant="outline" size="sm" onClick={() => openLocationEditor(r)}>
                          Edit locations
                        </Button>
                        <Button
                          variant="primary"
                          size="sm"
                          onClick={() => confirmMovement(r)}
                          disabled={confirmingMovementIds.includes(r.id)}
                        >
                          {confirmingMovementIds.includes(r.id) ? "Confirming..." : "Confirm"}
                        </Button>
                        <Button variant="danger" size="sm" onClick={() => rejectMovement(r)}>
                          Reject
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}

                {!loadingMovements && movementRows.length === 0 && (
                  <tr>
                    <td colSpan={10} className="px-3 py-6 text-sm text-zinc-600">
                      No pending movements
                    </td>
                  </tr>
                )}

                {loadingMovements && (
                  <tr>
                    <td colSpan={10} className="px-3 py-6 text-sm text-zinc-600">
                      Loading…
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          <div className="flex flex-col gap-2 border-t border-zinc-200 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="text-sm text-zinc-600">
              Total <span className="font-semibold text-zinc-900">{movementMeta.total}</span> • Page{" "}
              <span className="font-semibold text-zinc-900">{movementMeta.page}</span> /{" "}
              <span className="font-semibold text-zinc-900">{movementPages}</span> • Size{" "}
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
        {/*
        <div className="rounded-xl border border-zinc-200 bg-white">
          <div className="border-b border-zinc-200 px-4 py-3">
            <div className="text-sm font-semibold text-zinc-900">Pending RFID Events</div>
            <div className="mt-1 text-xs text-zinc-500">
              Unusual RFID cases without associated movement
            </div>
          </div>

          <div className="relative max-h-[750px] overflow-auto bg-white">
            <table className="min-w-full border-separate border-spacing-0 [table-layout:fixed]">
              <thead>
                <tr>
                  {[
                    "ID",
                    "Seen At",
                    "Event Type",
                    "Reason",
                    "EPC",
                    "Reader",
                    "Antenna",
                    "Door",
                    "Zone",
                    "Role",
                    "Payload",
                    "Actions",
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
                  />
                  <th
                    className="sticky z-20 border-b border-zinc-200 bg-white px-3 py-2"
                    style={{ top: FILTER_ROW_TOP }}
                  />
                  <th
                    className="sticky z-20 border-b border-zinc-200 bg-white px-3 py-2"
                    style={{ top: FILTER_ROW_TOP }}
                  >
                    <Input
                      value={eventTypeFilter}
                      onChange={(e) => setEventTypeFilter(e.target.value)}
                      placeholder="Event type…"
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
                      value={eventEpcFilter}
                      onChange={(e) => setEventEpcFilter(e.target.value)}
                      placeholder="EPC…"
                    />
                  </th>
                  <th
                    className="sticky z-20 border-b border-zinc-200 bg-white px-3 py-2"
                    style={{ top: FILTER_ROW_TOP }}
                  />
                  <th
                    className="sticky z-20 border-b border-zinc-200 bg-white px-3 py-2"
                    style={{ top: FILTER_ROW_TOP }}
                  />
                  <th
                    className="sticky z-20 border-b border-zinc-200 bg-white px-3 py-2"
                    style={{ top: FILTER_ROW_TOP }}
                  >
                    <Input
                      value={eventDoorFilter}
                      onChange={(e) => setEventDoorFilter(e.target.value)}
                      placeholder="Door…"
                    />
                  </th>
                  <th
                    className="sticky z-20 border-b border-zinc-200 bg-white px-3 py-2"
                    style={{ top: FILTER_ROW_TOP }}
                  />
                  <th
                    className="sticky z-20 border-b border-zinc-200 bg-white px-3 py-2"
                    style={{ top: FILTER_ROW_TOP }}
                  />
                  <th
                    className="sticky z-20 border-b border-zinc-200 bg-white px-3 py-2"
                    style={{ top: FILTER_ROW_TOP }}
                  />
                  <th
                    className="sticky z-20 border-b border-zinc-200 bg-white px-3 py-2"
                    style={{ top: FILTER_ROW_TOP }}
                  >
                    <div className="flex justify-end">
                      <Button variant="outline" onClick={() => loadEvents()} disabled={loadingEvents}>
                        Search
                      </Button>
                    </div>
                  </th>
                </tr>
              </thead>

              <tbody>
                {eventRows.map((r) => (
                  <tr key={r.id} className="hover:bg-zinc-50">
                    <td className="border-b border-zinc-100 px-3 py-2 text-sm font-medium text-black">
                      {r.id}
                    </td>
                    <td className="border-b border-zinc-100 px-3 py-2 text-sm text-black">
                      {fmtDate(r.seen_at || r.created_at)}
                    </td>
                    <td className="border-b border-zinc-100 px-3 py-2 text-sm text-black">
                      {r.event_type}
                    </td>
                    <td className="border-b border-zinc-100 px-3 py-2 text-sm text-black">
                      {r.reason || ""}
                    </td>
                    <td className="border-b border-zinc-100 px-3 py-2 text-sm text-black">
                      {r.epc || ""}
                    </td>
                    <td className="border-b border-zinc-100 px-3 py-2 text-sm text-black">
                      {r.reader_id || ""}
                    </td>
                    <td className="border-b border-zinc-100 px-3 py-2 text-sm text-black">
                      {r.antenna ?? ""}
                    </td>
                    <td className="border-b border-zinc-100 px-3 py-2 text-sm text-black">
                      {r.door_id || ""}
                    </td>
                    <td className="border-b border-zinc-100 px-3 py-2 text-sm text-black">
                      {r.zone_id || ""}
                    </td>
                    <td className="border-b border-zinc-100 px-3 py-2 text-sm text-black">
                      {r.zone_role || ""}
                    </td>
                    <td className="border-b border-zinc-100 px-3 py-2 text-xs text-black">
                      <details>
                        <summary className="cursor-pointer text-zinc-700">View</summary>
                        <pre className="mt-2 max-w-[360px] whitespace-pre-wrap break-words text-xs text-zinc-700">
                          {prettyJson(r.payload || {})}
                        </pre>
                      </details>
                    </td>
                    <td className="border-b border-zinc-100 px-3 py-2 text-sm text-black">
                      <div className="flex flex-wrap gap-2">
                        <Button variant="primary" size="sm" onClick={() => confirmEvent(r)}>
                          Confirm
                        </Button>
                        <Button variant="danger" size="sm" onClick={() => rejectEvent(r)}>
                          Reject
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}

                {!loadingEvents && eventRows.length === 0 && (
                  <tr>
                    <td colSpan={12} className="px-3 py-6 text-sm text-zinc-600">
                      No pending RFID events
                    </td>
                  </tr>
                )}

                {loadingEvents && (
                  <tr>
                    <td colSpan={12} className="px-3 py-6 text-sm text-zinc-600">
                      Loading…
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
          */}
        {locationEditorOpen && editingMovement && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
            <div className="w-full max-w-2xl rounded-2xl border border-zinc-200 bg-white p-5 shadow-xl">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="text-sm font-semibold text-zinc-900">
                    Edit movement locations #{editingMovement.id}
                  </div>
                  <div className="mt-1 text-xs text-zinc-500">
                    Update source and destination locations before confirmation
                  </div>
                </div>

                <Button variant="ghost" onClick={closeLocationEditor}>
                  Close
                </Button>
              </div>

              <div className="mt-4 grid gap-4 md:grid-cols-2">
                <LocationAutocomplete
                  label="From location"
                  valueText={locFromText}
                  onTextChange={(v) => {
                    setLocFromText(v);
                    setLocFromId(null);
                  }}
                  onSelect={(loc) => {
                    setLocFromId(loc.id);
                    setLocFromText(loc.name);
                    setFromSuggestions([]);
                  }}
                  suggestions={fromSuggestions}
                />

                <LocationAutocomplete
                  label="To location"
                  valueText={locToText}
                  onTextChange={(v) => {
                    setLocToText(v);
                    setLocToId(null);
                  }}
                  onSelect={(loc) => {
                    setLocToId(loc.id);
                    setLocToText(loc.name);
                    setToSuggestions([]);
                  }}
                  suggestions={toSuggestions}
                />
              </div>

              <div className="mt-4 grid gap-3 md:grid-cols-2">
                <div className="rounded-xl border border-zinc-200 bg-zinc-50 p-3 text-sm">
                  <div className="font-medium text-zinc-800">Selected From</div>
                  <div className="mt-1 text-zinc-600">
                    {locFromId != null ? `#${locFromId} · ${locFromText}` : "Not selected"}
                  </div>
                </div>

                <div className="rounded-xl border border-zinc-200 bg-zinc-50 p-3 text-sm">
                  <div className="font-medium text-zinc-800">Selected To</div>
                  <div className="mt-1 text-zinc-600">
                    {locToId != null ? `#${locToId} · ${locToText}` : "Not selected"}
                  </div>
                </div>
              </div>

              {err && (
                <div className="mt-3 rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                  Error: {err}
                </div>
              )}

              <div className="mt-5 flex items-center justify-end gap-2">
                <Button variant="outline" onClick={closeLocationEditor}>
                  Cancel
                </Button>
                <Button variant="primary" onClick={saveMovementLocations}>
                  Save locations
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}