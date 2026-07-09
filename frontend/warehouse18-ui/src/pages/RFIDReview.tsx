import { useEffect, useMemo, useRef, useState } from "react";
import type { CSSProperties } from "react";
import { CheckCircle2, XCircle, Minus, Plus, Save, ChevronUp, ChevronDown } from "lucide-react";
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
  is_preventive: boolean;
  rfid_status: string | null;
  detected_asset_code?: string | null;
  detected_tracking_mode?: "serialized" | "bulk" | "unknown" | null;
  detected_tid_hex?: string | null;
  item_is_serialized?: boolean | null;
  aisle_code?: string | null;
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
  auth_provider?: string;
  mysim_id?: number | null;
};

type MovementCode = "GR" | "GT" | "GI";

type CandidateState = {
  data: CandidateLocationsOut | null;
  loading: boolean;
  error: string | null;
  settingDestinationId: number | null;

  loadedMovementTypeId: number | null;
  loadedDetectedAisleId: number | null;
  loadedRfidStatus: string | null;
};

type DeviceInstallUninstallForm = {
  unistall_part: string;

  // Valor real que se envía al backend/mySim.
  // Debe ser Location.code, no Location.id.
  dest_uninstalled_part: string;

  // Texto visible del buscador.
  dest_uninstalled_part_search: string;

  uninstalled_by: string;
  why_is_it_uninstalled: string;
};

type DoneByForm = {
  mysim_id: string;
  search: string;
};

function userDisplayName(user: UserOut): string {
  return (
    safeStr(user.full_name).trim() ||
    safeStr(user.username).trim() ||
    `User ${user.id}`
  );
}

function userOptionLabel(user: UserOut): string {
  const displayName = userDisplayName(user);
  const username = safeStr(user.username).trim();

  const mysimText =
    user.mysim_id == null ? "no mySim ID" : `mySim ${user.mysim_id}`;

  return displayName
}

function userSearchText(user: UserOut): string {
  return normalizeSearchText(
    [
      user.full_name,
      user.username,
      user.email,
      user.mysim_id == null ? "" : String(user.mysim_id),
    ]
      .filter(Boolean)
      .join(" ")
  );
}

function userHasMysimId(user: UserOut): boolean {
  return user.mysim_id != null && Number.isFinite(Number(user.mysim_id));
}

function userMysimId(user: UserOut): string {
  return user.mysim_id == null ? "" : String(user.mysim_id);
}

function emptyDeviceInstallUninstallForm(): DeviceInstallUninstallForm {
  return {
    unistall_part: "",
    dest_uninstalled_part: "",
    dest_uninstalled_part_search: "",
    uninstalled_by: "",
    why_is_it_uninstalled: "",
  };
}

function isDeviceLocation(location?: LocationOut | null): boolean {
  if (!location) return false;

  const code = safeStr(location.code).trim().toLowerCase();
  const name = safeStr(location.name).trim().toLowerCase();

  return code === "1" || code === "device" || name === "device";
}

function isDeviceInstallUninstallComplete(form: DeviceInstallUninstallForm): boolean {
  const destUninstalledPart = Number(form.dest_uninstalled_part);

  return (
    form.unistall_part.trim().length > 0 &&
    Number.isFinite(destUninstalledPart) &&
    destUninstalledPart > 0 &&
    form.why_is_it_uninstalled.trim().length > 0
  );
}

function isWarehouseLocation(location?: LocationOut | null): boolean {
  if (!location) return false;

  return (
    location.is_active === true &&
    location.is_warehouse_location === true &&
    !isDeviceLocation(location)
  );
}

function deviceUninstallDestinationLabel(loc: LocationOut): string {
  const name = safeStr(loc.name).trim();
  const code = safeStr(loc.code).trim();
  const rack = safeStr(loc.rack_code).trim();
  const shelf = safeStr(loc.shelf_code).trim().toUpperCase();

  const rackShelf =
    rack || shelf ? ` · ${[rack, shelf].filter(Boolean).join("")}` : "";

  if (name && code) {
    return `${name}`; {/*· ${code}${rackShelf}`;*/ }
  }

  return name; {/* || code || `Location ${loc.id}`;*/ }
}

function locationHasNumericMysimCode(loc: LocationOut): boolean {
  return /^\d+$/.test(safeStr(loc.code).trim());
}

function safeStr(value: unknown) {
  return value == null ? "" : String(value);
}

type ConfirmKind = "serialized" | "bulk" | "normal";

function inferConfirmKind(row: MovementOut): ConfirmKind {
  const assetCode = getMovementAssetCode(row);
  const itemCode = getMovementItemCode(row);

  if (!assetCode || !itemCode) {
    return "normal";
  }

  if (row.detected_tracking_mode === "serialized") {
    return "serialized";
  }

  if (row.detected_tracking_mode === "bulk") {
    return "bulk";
  }

  return "normal";
}

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

function shouldUseSerializedAssetConfirm(row: MovementOut): boolean {
  return Boolean(row.detected_asset_code && row.item_key);
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

async function saveQuantityIfNeeded(row: MovementOut): Promise<void> {
  const raw = editingQty[row.id];

  // Si no hay edición pendiente, no hacemos nada.
  if (raw === undefined) {
    return;
  }

  const nextQty = normalizeQtyForSave(raw);
  const currentQty = normalizeQtyForSave(row.quantity ?? 1);

  if (nextQty === currentQty) {
    return;
  }

  await apiJson("PATCH", `/api/movements/${row.id}/quantity`, {
    quantity: nextQty,
  });
}

const fieldInputClassName =
  "h-10 w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm shadow-none outline-none focus:border-zinc-500 focus:ring-0 disabled:bg-zinc-100 disabled:text-zinc-400";

function movementSelectClassName(code: string) {
  const normalized = (code || "").toUpperCase();

  const base = `${fieldInputClassName} font-semibold`;

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

function destinationOptionLabel(loc: LocationOut, deviceGroupCode?: string | null) {
  const rackCode = safeStr(loc.rack_code).trim();
  const shelfCode = safeStr(loc.shelf_code).trim().toUpperCase();
  const groupCode = safeStr(deviceGroupCode).trim().toUpperCase();

  if (loc.is_warehouse_location && groupCode && (rackCode || shelfCode)) {
    return `${groupCode} ${rackCode}${shelfCode}`;
  }

  const base = loc.name || loc.code;

  if (rackCode || shelfCode) {
    return `${base}`; {/* · Rack ${rackCode || "-"} · Shelf ${shelfCode || "-"}`;*/ }
  }

  return base;
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
    loadedMovementTypeId: null,
    loadedDetectedAisleId: null,
    loadedRfidStatus: null,
  };
}
function normalizeSearchText(value: string): string {
  return value
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .trim();
}
export default function RFIDReviewPage() {
  const [doneByOpenRowId, setDoneByOpenRowId] = useState<number | null>(null);
  const [doneByByMovement, setDoneByByMovement] = useState<Record<number, DoneByForm>>({});
  const [reviewerUserId, setReviewerUserId] = useState("1");
  const [confirmingMovementIds, setConfirmingMovementIds] = useState<number[]>([]);
  const [movementTypeUpdatingId, setMovementTypeUpdatingId] = useState<number | null>(null);
  const [destinationSearchById, setDestinationSearchById] = useState<
    Record<number, string>
  >({});

  const [destinationOpenRowId, setDestinationOpenRowId] = useState<number | null>(
    null
  );
  const [deviceUninstallDestinationOpenRowId, setDeviceUninstallDestinationOpenRowId,] = useState<number | null>(
    null
  );
  const [deviceInstallByMovement, setDeviceInstallByMovement] = useState<
    Record<number, DeviceInstallUninstallForm>
  >({});

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

  const selectableUsers = useMemo(() => {
    return Object.values(userMap)
      .filter((user) => user.is_active !== false)
      .sort((a, b) =>
        userOptionLabel(a).localeCompare(userOptionLabel(b), undefined, {
          numeric: true,
          sensitivity: "base",
        })
      );
  }, [userMap]);

  const userByMysimId = useMemo(() => {
    const next: Record<string, UserOut> = {};

    for (const user of selectableUsers) {
      if (user.mysim_id != null) {
        next[String(user.mysim_id)] = user;
      }
    }

    return next;
  }, [selectableUsers]);
  const warehouseLocations = useMemo(() => {
    return Object.values(locationMap)
      .filter(isWarehouseLocation)
      .sort((a, b) =>
        deviceUninstallDestinationLabel(a).localeCompare(
          deviceUninstallDestinationLabel(b),
          undefined,
          { numeric: true, sensitivity: "base" }
        )
      );
  }, [locationMap]);

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

  function updateDeviceInstallFields(
    movementId: number,
    patch: Partial<DeviceInstallUninstallForm>
  ) {
    setDeviceInstallByMovement((prev) => ({
      ...prev,
      [movementId]: {
        ...(prev[movementId] ?? emptyDeviceInstallUninstallForm()),
        ...patch,
      },
    }));
  }

  function updateDeviceInstallField(
    movementId: number,
    field: keyof DeviceInstallUninstallForm,
    value: string
  ) {
    updateDeviceInstallFields(movementId, {
      [field]: value,
    });
  }

  function movementSnapshot(rows: MovementOut[]) {
    return rows.map((r) => ({
      id: r.id,
      movement_type_id: r.movement_type_id,
      item_id: r.item_id ?? null,
      from_location_id: r.from_location_id ?? null,
      to_location_id: r.to_location_id ?? null,
      quantity: r.quantity == null ? null : String(r.quantity),
      review_status: r.review_status,
      notes: r.notes ?? "",
      item_key: r.item_key ?? "",
      detected_asset_code: r.detected_asset_code ?? "",
      reference_type: r.reference_type ?? "",
      reference_id: r.reference_id ?? null,
      user_id: r.user_id ?? null,
      user_name: r.user_name ?? "",

      is_preventive: r.is_preventive ?? false,
      rfid_status: r.rfid_status ?? "",
      detected_aisle_id: r.detected_aisle_id ?? null,
      aisle_code: r.aisle_code ?? "",
      detected_tracking_mode: r.detected_tracking_mode ?? "",
      detected_tid_hex: r.detected_tid_hex ?? "",

      updated_like: [
        r.id,
        r.movement_type_id,
        r.item_id ?? null,
        r.from_location_id ?? null,
        r.to_location_id ?? null,
        r.quantity == null ? null : String(r.quantity),
        r.review_status,
        r.notes ?? "",
        r.item_key ?? "",
        r.detected_asset_code ?? "",
        r.reference_type ?? "",
        r.reference_id ?? null,
        r.user_id ?? null,
        r.user_name ?? "",

        r.is_preventive ?? false,
        r.rfid_status ?? "",
        r.detected_aisle_id ?? null,
        r.aisle_code ?? "",
        r.detected_tracking_mode ?? "",
        r.detected_tid_hex ?? "",
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
        loadedMovementTypeId: row.movement_type_id,
        loadedDetectedAisleId: row.detected_aisle_id ?? null,
        loadedRfidStatus: row.rfid_status ?? null,
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
          loadedMovementTypeId: row.movement_type_id,
          loadedDetectedAisleId: row.detected_aisle_id ?? null,
          loadedRfidStatus: row.rfid_status ?? null,
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
          loadedMovementTypeId: row.movement_type_id,
          loadedDetectedAisleId: row.detected_aisle_id ?? null,
          loadedRfidStatus: row.rfid_status ?? null,
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
        loadedMovementTypeId: row.movement_type_id,
        loadedDetectedAisleId: row.detected_aisle_id ?? null,
        loadedRfidStatus: row.rfid_status ?? null,
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
          loadedMovementTypeId: row.movement_type_id,
          loadedDetectedAisleId: row.detected_aisle_id ?? null,
          loadedRfidStatus: row.rfid_status ?? null,
        },
      }));
    } finally {
      setMovementTypeUpdatingId(null);
    }
  }

  async function setCandidateAsDestination(row: MovementOut, loc: LocationOut) {
    setErr(null);

    const destinationLabel = destinationOptionLabel(
      loc,
      candidateByMovementRef.current[row.id]?.data?.device_group_code
    );

    setCandidateByMovement((prev) => ({
      ...prev,
      [row.id]: {
        ...(prev[row.id] ?? emptyCandidateState()),
        settingDestinationId: loc.id,
        error: null,
      },
    }));

    setLocationMap((prev) => ({
      ...prev,
      [loc.id]: loc,
    }));

    setDestinationSearchById((prev) => ({
      ...prev,
      [row.id]: destinationLabel,
    }));

    // Optimistic update so the button can enable immediately.
    // The backend refresh below will keep it honest, sadly a thing we need now.
    setMovementRows((prev) =>
      prev.map((m) =>
        m.id === row.id
          ? {
            ...m,
            to_location_id: loc.id,
          }
          : m
      )
    );

    try {
      console.log("PATCH DESTINATION", {
        movementId: row.id,
        locationId: loc.id,
        locationCode: loc.code,
        locationName: loc.name,
      });

      const response = await apiJson(
        "PATCH",
        `/api/movements/${row.id}/destination`,
        {
          location_id: loc.id,
        }
      );

      const updated = unwrapApiData<MovementOut>(response);

      setMovementRows((prev) =>
        prev.map((m) =>
          m.id === row.id
            ? {
              ...m,
              ...updated,
              to_location_id: updated.to_location_id ?? loc.id,
            }
            : m
        )
      );

      setDestinationSearchById((prev) => ({
        ...prev,
        [row.id]: destinationLabel,
      }));

      // Force a silent refresh so polling does not later resurrect the stale row.
      await loadMovements(movementPageRef.current, { silent: true });
    } catch (e: any) {
      const message = e?.message ?? String(e);

      console.error("PATCH DESTINATION FAILED", {
        movementId: row.id,
        locationId: loc.id,
        locationCode: loc.code,
        locationName: loc.name,
        isWarehouseLocation: loc.is_warehouse_location,
        message,
      });
      setErr(message);

      setMovementRows((prev) =>
        prev.map((m) =>
          m.id === row.id
            ? {
              ...m,
              to_location_id: row.to_location_id ?? null,
            }
            : m
        )
      );

      setDestinationSearchById((prev) => {
        const next = { ...prev };
        delete next[row.id];
        return next;
      });

      setCandidateByMovement((prev) => ({
        ...prev,
        [row.id]: {
          ...(prev[row.id] ?? emptyCandidateState()),
          error: message,
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
        const currentCandidate = candidateByMovementRef.current[item.id];

        const itemMovementCode = safeMovementCode(
          movementCodeOf(item.movement_type_id, movementTypeMap)
        );

        const isGI = itemMovementCode === "GI";

        const isReadyForLocation =
          isGI ||
          (
            item.rfid_status === "ready_for_location" &&
            item.detected_aisle_id != null &&
            (itemMovementCode === "GR" || itemMovementCode === "GT")
          );

        if (!isReadyForLocation) {
          setCandidateByMovement((prev) => ({
            ...prev,
            [item.id]: {
              ...emptyCandidateState(),
              loadedMovementTypeId: item.movement_type_id,
              loadedDetectedAisleId: item.detected_aisle_id ?? null,
              loadedRfidStatus: item.rfid_status ?? null,
            },
          }));

          continue;
        }

        const candidateWasLoadedForDifferentAisle =
          currentCandidate?.loadedDetectedAisleId !==
          (item.detected_aisle_id ?? null);

        const candidateWasLoadedForDifferentMovementType =
          currentCandidate?.loadedMovementTypeId !== item.movement_type_id;

        const candidateWasLoadedForDifferentRfidStatus =
          currentCandidate?.loadedRfidStatus !== (item.rfid_status ?? null);

        const hasCandidateData = Boolean(currentCandidate?.data);

        const hasEmptyCandidateLocations =
          Boolean(currentCandidate?.data) &&
          (currentCandidate?.data?.locations.length ?? 0) === 0;

        const hasCandidateError = Boolean(currentCandidate?.error);

        const shouldForceCandidateReload =
          !hasCandidateData ||
          hasEmptyCandidateLocations ||
          hasCandidateError ||
          candidateWasLoadedForDifferentAisle ||
          candidateWasLoadedForDifferentMovementType ||
          candidateWasLoadedForDifferentRfidStatus;

        void loadCandidateLocations(item, shouldForceCandidateReload);
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

  function currentQtyValue(
    r: MovementOut,
    editingQty: Record<number, string>
  ): string {
    const edited = editingQty[r.id];

    if (edited !== undefined) {
      return edited;
    }

    const qty = Number(r.quantity ?? 1);

    if (!Number.isFinite(qty) || qty <= 0) {
      return "1";
    }

    return String(Math.trunc(qty));
  }

  function normalizeQtyForSave(value: string | number | null | undefined): number {
    const qty = Number.parseInt(String(value ?? ""), 10);

    if (!Number.isFinite(qty) || qty <= 0) {
      return 1;
    }

    return qty;
  }

  async function saveMovementQuantity(row: MovementOut) {
    setErr(null);

    try {
      const raw = editingQty[row.id] ?? (row.quantity == null ? "1" : String(row.quantity));
      const qty = normalizeQtyForSave(raw);

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

  function getMovementAssetCode(row: MovementOut): string | null {
    return row.detected_asset_code?.trim() || null;
  }

  function getMovementItemCode(row: MovementOut): string | null {
    return row.item_key?.trim() || null;
  }

  async function saveQuantityIfNeeded(row: MovementOut): Promise<void> {
    const rawValue = editingQty[row.id];

    // Si el usuario no ha tocado el input, no hacemos nada.
    if (rawValue === undefined) {
      return;
    }

    const textValue = String(rawValue).trim();

    if (!textValue) {
      throw new Error("Quantity is required");
    }

    const nextQuantity = Number(textValue);

    if (!Number.isFinite(nextQuantity) || nextQuantity <= 0) {
      throw new Error("Quantity must be greater than zero");
    }

    if (!Number.isInteger(nextQuantity)) {
      throw new Error("Quantity must be an integer");
    }

    const currentQuantity = Number(row.quantity ?? 1);

    if (nextQuantity === currentQuantity) {
      return;
    }

    const updatedMovement = await apiJson<MovementOut>(
      "PATCH",
      `/api/movements/${row.id}/quantity`,
      {
        quantity: nextQuantity,
      }
    );

    setMovementRows((prev) =>
      prev.map((item) => (item.id === row.id ? updatedMovement : item))
    );

    setEditingQty((prev) => {
      const next = { ...prev };
      delete next[row.id];
      return next;
    });
  }

  function shouldUseSerializedAssetConfirm(row: MovementOut): boolean {
    return Boolean(getMovementAssetCode(row) && getMovementItemCode(row));
  }

  async function confirmMovement(row: MovementOut) {
    if (confirmingMovementIds.includes(row.id)) return;

    setErr(null);
    setConfirmingMovementIds((prev) => [...prev, row.id]);

    try {
      const assetCode = getMovementAssetCode(row);
      const itemCode = getMovementItemCode(row);
      const trackingMode = row.detected_tracking_mode ?? "unknown";

      const selectedDestination =
        row.to_location_id != null ? locationMap[row.to_location_id] ?? null : null;

      const selectedDestinationIsDevice = isDeviceLocation(selectedDestination);

      const deviceInstallForm =
        deviceInstallByMovement[row.id] ?? emptyDeviceInstallUninstallForm();

      const currentDoneByForm = doneByByMovement[row.id];

      const doneByPayload = Number(
        currentDoneByForm?.mysim_id ||
        (row.mysim_user_id == null ? "" : String(row.mysim_user_id))
      );

      if (!Number.isFinite(doneByPayload) || doneByPayload <= 0) {
        throw new Error("Done by requires a user with mySim ID");
      }

      let deviceInstallPayload: {
        unistall_part: string;
        dest_uninstalled_part: number;
        uninstalled_by: number;
        why_is_it_uninstalled: string;
      } | null = null;

      if (selectedDestinationIsDevice) {
        if (trackingMode !== "serialized") {
          throw new Error("Device install/uninstall is only supported for serialized assets");
        }

        if (!isDeviceInstallUninstallComplete(deviceInstallForm)) {
          throw new Error(
            "Device destination requires part to uninstall, destination for uninstalled part, uninstalled by and reason"
          );
        }

        deviceInstallPayload = {
          unistall_part: deviceInstallForm.unistall_part.trim(),
          dest_uninstalled_part: Number(deviceInstallForm.dest_uninstalled_part),
          uninstalled_by: doneByPayload,
          why_is_it_uninstalled: deviceInstallForm.why_is_it_uninstalled.trim(),
        };
      }

      console.log("confirmMovement decision", {
        id: row.id,
        item_key: row.item_key,
        detected_asset_code: row.detected_asset_code,
        detected_tracking_mode: row.detected_tracking_mode,
        detected_tid_hex: row.detected_tid_hex,
        destination: selectedDestination,
        selectedDestinationIsDevice,
        deviceInstallPayload,
        assetCode,
        itemCode,
        trackingMode,
      });

      if (assetCode && itemCode && trackingMode === "serialized") {
        await apiPost(`/api/movements/${row.id}/confirm-serialized-asset`, {
          asset_code: assetCode,
          item_code: itemCode,
          reviewed_by_user_id: reviewerId,
          review_note: "Validated manually",
          create_enrichment: true,
          enqueue_sync: true,
          done_by: doneByPayload,
          ...(deviceInstallPayload ?? {}),
        });
      } else if (assetCode && itemCode && trackingMode === "bulk") {
        await saveQuantityIfNeeded(row);

        await apiPost(`/api/movements/${row.id}/confirm-bulk`, {
          container_code: assetCode,
          item_code: itemCode,
          reviewed_by_user_id: reviewerId,
          review_note: "Validated manually",
          enqueue_sync: true,
        });
      } else {
        const payload: MovementReviewIn = {
          reviewed_by_user_id: reviewerId,
          note: "Validated manually",
        };

        await apiPost(`/api/movements/${row.id}/confirm`, payload);
      }

      setDeviceInstallByMovement((prev) => {
        const next = { ...prev };
        delete next[row.id];
        return next;
      });

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

              const canUseCandidateLocations =
                rowMovementCode === "GI" ||
                (
                  r.rfid_status === "ready_for_location" &&
                  (rowMovementCode === "GT" || rowMovementCode === "GR")
                );

              const candidateLocations = canUseCandidateLocations
                ? candidateState.data?.locations ?? []
                : [];

              const selectedDestinationId = r.to_location_id ?? null;

              const selectedDestination =
                selectedDestinationId !== null
                  ? (
                    candidateLocations.find((loc) => loc.id === selectedDestinationId) ??
                    locationMap[selectedDestinationId] ??
                    null
                  )
                  : null;
              const selectedDestinationIsDevice = isDeviceLocation(selectedDestination);

              const deviceInstallForm =
                deviceInstallByMovement[r.id] ?? emptyDeviceInstallUninstallForm();

              const currentDoneByMysimId =
                doneByByMovement[r.id]?.mysim_id ||
                (r.mysim_user_id == null ? "" : String(r.mysim_user_id));

              const selectedDoneByUser =
                currentDoneByMysimId && userByMysimId[currentDoneByMysimId]
                  ? userByMysimId[currentDoneByMysimId]
                  : null;

              const doneByForm: DoneByForm = doneByByMovement[r.id] ?? {
                mysim_id: currentDoneByMysimId,
                search: selectedDoneByUser
                  ? userOptionLabel(selectedDoneByUser)
                  : doneByLabel(r, userMap),
              };

              const doneBySearchFilter = normalizeSearchText(doneByForm.search);

              const filteredDoneByUsers =
                doneBySearchFilter.length === 0
                  ? selectableUsers.slice(0, 50)
                  : selectableUsers
                    .filter((user) => userSearchText(user).includes(doneBySearchFilter))
                    .slice(0, 50);

              const doneByPayload = Number(doneByForm.mysim_id);

              const doneByComplete =
                Number.isFinite(doneByPayload) && doneByPayload > 0;

              const deviceInstallComplete =
                !selectedDestinationIsDevice ||
                isDeviceInstallUninstallComplete(deviceInstallForm);

              const deviceUninstallDestinationSearch =
                deviceInstallForm.dest_uninstalled_part_search ||
                deviceInstallForm.dest_uninstalled_part;

              const selectedDeviceUninstallDestination =
                warehouseLocations.find(
                  (loc) =>
                    safeStr(loc.code).trim() ===
                    safeStr(deviceInstallForm.dest_uninstalled_part).trim()
                ) ?? null;

              const deviceUninstallDestinationFilter = normalizeSearchText(
                deviceUninstallDestinationSearch
              );

              const filteredDeviceUninstallDestinations =
                deviceUninstallDestinationFilter.length === 0
                  ? warehouseLocations.slice(0, 50)
                  : warehouseLocations
                    .filter((loc) =>
                      normalizeSearchText(deviceUninstallDestinationLabel(loc)).includes(
                        deviceUninstallDestinationFilter
                      )
                    )
                    .slice(0, 50);

              const selectedDestinationIsValid =
                selectedDestinationId !== null && selectedDestination !== null;

              const selectedDestinationLabel = selectedDestination
                ? destinationOptionLabel(
                  selectedDestination,
                  candidateState.data?.device_group_code
                )
                : "";

              const destinationSearchText =
                destinationSearchById[r.id] ?? selectedDestinationLabel;

              const destinationFilter = normalizeSearchText(destinationSearchText);

              const filteredDestinationLocations =
                destinationFilter.length === 0
                  ? candidateLocations
                  : candidateLocations.filter((loc) =>
                    normalizeSearchText(
                      destinationOptionLabel(loc, candidateState.data?.device_group_code)
                    ).includes(destinationFilter)
                  );

              const destinationDisabled =
                candidateState.loading ||
                candidateState.settingDestinationId !== null ||
                movementTypeUpdatingId === r.id ||
                candidateLocations.length === 0;

              const hasRequiredLocation = selectedDestinationId !== null;

              const canConfirmMovement =
                hasRequiredLocation &&
                selectedDestinationIsValid &&
                doneByComplete &&
                deviceInstallComplete &&
                !candidateState.loading &&
                candidateState.settingDestinationId === null &&
                movementTypeUpdatingId !== r.id;

              const showAisle = rowMovementCode === "GT" || rowMovementCode === "GR";
              const aisleCode =
                r.aisle_code ||
                (r.detected_aisle_id != null ? `AISLE${r.detected_aisle_id}` : "") ||
                "";

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
                      <div className="grid gap-2 md:grid-cols-[195px_195px_48px] md:justify-start">
                        <div className="rounded-xl border border-zinc-200 bg-zinc-50 p-3">
                          <div className="text-[11px] font-semibold uppercase tracking-wide text-zinc-500">
                            Movement Type
                          </div>

                          <div className="mt-4 flex h-10 items-center">
                            <select
                              value={rowMovementCode}
                              disabled={movementTypeUpdatingId === r.id}
                              onChange={(e) => {
                                const nextCode = e.target.value as MovementCode;

                                if (nextCode !== rowMovementCode) {
                                  void setMovementType(r, nextCode);
                                }
                              }}
                              className={`${movementSelectClassName(rowMovementCode)} h-10 w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm font-semibold outline-none focus:border-zinc-500 disabled:bg-zinc-100 disabled:text-zinc-400`}
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
                          {showAisle && (
                            <div className="mb-2 flex items-center justify-between gap-2">
                              <span className="text-[11px] font-semibold uppercase tracking-wide text-zinc-500">
                                Aisle
                              </span>

                              <span className="rounded-full bg-white px-2 py-0.5 text-xs font-semibold text-zinc-800 ring-1 ring-zinc-200">
                                {aisleCode || "—"}
                              </span>
                            </div>
                          )}

                          <div className={showAisle ? "border-t border-zinc-200 pt-2" : ""}>
                            <div className="text-[11px] font-semibold uppercase tracking-wide text-zinc-500">
                              Destination
                            </div>

                            <div className="relative mt-4">
                              {r.rfid_status === "wrong_aisle" && (
                                <div className="mt-2 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-xs font-semibold text-red-700">
                                  Wrong aisle for this item
                                </div>
                              )}
                              <input
                                type="text"
                                value={destinationSearchText}
                                disabled={destinationDisabled}
                                placeholder={
                                  candidateState.loading
                                    ? "Loading destinations…"
                                    : candidateLocations.length === 0
                                      ? "No valid destinations"
                                      : "Search destination…"
                                }
                                onFocus={() => {
                                  setDestinationOpenRowId(r.id);
                                }}
                                onChange={(e) => {
                                  setDestinationSearchById((prev) => ({
                                    ...prev,
                                    [r.id]: e.target.value,
                                  }));

                                  setDestinationOpenRowId(r.id);
                                }}
                                onKeyDown={(e) => {
                                  if (e.key === "Escape") {
                                    setDestinationOpenRowId(null);
                                  }

                                  if (
                                    e.key === "Enter" &&
                                    !destinationDisabled &&
                                    filteredDestinationLocations.length > 0
                                  ) {
                                    e.preventDefault();

                                    const firstLocation = filteredDestinationLocations[0];

                                    setDestinationOpenRowId(null);

                                    void setCandidateAsDestination(r, firstLocation);
                                  }
                                }}
                                onBlur={() => {
                                  window.setTimeout(() => {
                                    setDestinationOpenRowId((current) =>
                                      current === r.id ? null : current
                                    );
                                  }, 150);
                                }}
                                className={`${fieldInputClassName} font-medium`}
                              />

                              {destinationOpenRowId === r.id && !destinationDisabled && (
                                <div className="absolute left-0 right-0 z-50 mt-1 max-h-56 overflow-auto rounded-lg border border-zinc-200 bg-white shadow-lg">
                                  {candidateState.loading ? (
                                    <div className="px-3 py-2 text-sm text-zinc-500">
                                      Loading destinations…
                                    </div>
                                  ) : filteredDestinationLocations.length === 0 ? (
                                    <div className="px-3 py-2 text-sm text-zinc-500">
                                      No matching destinations
                                    </div>
                                  ) : (
                                    filteredDestinationLocations.map((loc) => {
                                      const label = destinationOptionLabel(
                                        loc,
                                        candidateState.data?.device_group_code
                                      );

                                      return (
                                        <button
                                          key={loc.id}
                                          type="button"
                                          onMouseDown={(e) => {
                                            e.preventDefault();

                                            setDestinationOpenRowId(null);

                                            void setCandidateAsDestination(r, loc);
                                          }}
                                          className="flex w-full items-center px-3 py-2 text-left text-sm text-zinc-900 hover:bg-zinc-50"
                                        >
                                          <span className="font-medium text-zinc-900">
                                            {label}
                                          </span>
                                        </button>
                                      );
                                    })
                                  )}
                                </div>
                              )}

                              {selectedDestinationId !== null && !selectedDestinationIsValid && (
                                <p className="mt-1 text-xs font-medium text-red-600">
                                  Current destination is no longer valid for this movement.
                                </p>
                              )}
                            </div>
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

                          {hasRequiredLocation && (
                            <button
                              type="button"
                              onClick={() => {
                                if (canConfirmMovement) {
                                  void confirmMovement(r);
                                }
                              }}
                              disabled={!canConfirmMovement || confirmingMovementIds.includes(r.id)}
                              title={
                                canConfirmMovement
                                  ? "Confirm movement"
                                  : !doneByComplete
                                    ? "Select a Done by user with mySim ID before confirming"
                                    : selectedDestinationIsDevice && !deviceInstallComplete
                                      ? "Complete the Device install/uninstall data before confirming"
                                      : "Select a valid destination before confirming"
                              }
                              className="flex h-9 w-9 items-center justify-center rounded-lg border border-green-600 bg-green-600 text-white hover:bg-green-700 disabled:cursor-not-allowed disabled:opacity-40"
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

                          <div className="relative mt-4">
                            <Input
                              value={
                                doneByOpenRowId === r.id
                                  ? doneByForm.search
                                  : selectedDoneByUser
                                    ? userDisplayName(selectedDoneByUser)
                                    : doneByForm.search
                              }
                              onFocus={() => {
                                setDoneByOpenRowId(r.id);
                              }}
                              onChange={(e) => {
                                setDoneByOpenRowId(r.id);

                                setDoneByByMovement((prev) => ({
                                  ...prev,
                                  [r.id]: {
                                    mysim_id: "",
                                    search: e.target.value,
                                  },
                                }));
                              }}
                              onBlur={() => {
                                window.setTimeout(() => {
                                  setDoneByOpenRowId((current) =>
                                    current === r.id ? null : current
                                  );
                                }, 150);
                              }}
                              placeholder="Search user..."
                              className={`${fieldInputClassName} ${selectedDoneByUser ? "font-medium" : "font-normal"
                                }`}
                            />

                            {doneByForm.mysim_id && (
                              <div className="mt-1 text-[11px] text-zinc-500">

                              </div>
                            )}

                            {doneByOpenRowId === r.id && (
                              <div className="absolute z-50 mt-1 max-h-56 w-full overflow-auto rounded-lg border border-zinc-200 bg-white shadow-lg">
                                {filteredDoneByUsers.length === 0 ? (
                                  <div className="px-3 py-2 text-sm text-zinc-500">
                                    No users found.
                                  </div>
                                ) : (
                                  filteredDoneByUsers.map((user) => {
                                    const disabled = !userHasMysimId(user);

                                    return (
                                      <button
                                        key={user.id}
                                        type="button"
                                        disabled={disabled}
                                        onMouseDown={(e) => {
                                          e.preventDefault();
                                        }}
                                        onClick={() => {
                                          if (disabled) {
                                            setErr(`User ${userOptionLabel(user)} has no mySim ID`);
                                            return;
                                          }

                                          setDoneByByMovement((prev) => ({
                                            ...prev,
                                            [r.id]: {
                                              mysim_id: userMysimId(user),
                                              search: userOptionLabel(user),
                                            },
                                          }));

                                          setDoneByOpenRowId(null);
                                        }}
                                        className={`flex w-full flex-col px-3 py-2 text-left text-sm ${disabled
                                          ? "cursor-not-allowed bg-zinc-50 text-zinc-400"
                                          : "hover:bg-zinc-50"
                                          }`}
                                      >
                                        <span className="font-medium text-zinc-900">
                                          {userDisplayName(user)}
                                        </span>{/*

                                        <span className="text-xs text-zinc-500">
                                          {[
                                            safeStr(user.username).trim()
                                              ? `@${safeStr(user.username).trim()}`
                                              : "",
                                            user.mysim_id == null
                                              ? "no mySim ID"
                                              : `mySim ${user.mysim_id}`,
                                          ]
                                            .filter(Boolean)
                                            .join(" · ")}
                                        </span>*/}
                                      </button>
                                    );
                                  })
                                )}
                              </div>
                            )}
                          </div>
                        </div>
                        <div className="rounded-xl border border-zinc-200 bg-zinc-50 p-3">
                          <div className="text-[11px] font-semibold uppercase tracking-wide text-zinc-500">
                            Quantity
                          </div>

                          <div className="mt-4 flex h-10 items-center gap-2">
                            <div className="flex h-10 flex-1 overflow-hidden rounded-lg border border-zinc-300 bg-white shadow-none">
                              <input
                                type="text"
                                inputMode="numeric"
                                pattern="[0-9]*"
                                value={currentQtyValue(r, editingQty)}
                                onChange={(e) => {
                                  const cleanValue = e.target.value.replace(/[^\d]/g, "");

                                  setEditingQty((prev) => ({
                                    ...prev,
                                    [r.id]: cleanValue,
                                  }));
                                }}
                                onBlur={() => {
                                  setEditingQty((prev) => {
                                    const rawValue = prev[r.id] ?? currentQtyValue(r, editingQty);
                                    const qty = Number.parseInt(rawValue, 10);

                                    return {
                                      ...prev,
                                      [r.id]: Number.isFinite(qty) && qty > 0 ? String(qty) : "1",
                                    };
                                  });
                                }}
                                className="h-full min-w-0 flex-1 border-0 bg-white px-3 text-sm font-semibold text-zinc-900 outline-none focus:ring-0"
                              />

                              <div className="flex w-8 flex-col border-l border-zinc-300">
                                <button
                                  type="button"
                                  onClick={() => {
                                    const current = Number.parseInt(
                                      editingQty[r.id] ?? currentQtyValue(r, editingQty),
                                      10
                                    );

                                    setEditingQty((prev) => ({
                                      ...prev,
                                      [r.id]: String(
                                        Number.isFinite(current) && current > 0 ? current + 1 : 2
                                      ),
                                    }));
                                  }}
                                  className="flex h-5 items-center justify-center text-zinc-500 hover:bg-zinc-100 hover:text-zinc-800"
                                  title="Increase quantity"
                                >
                                  <ChevronUp className="h-3.5 w-3.5" />
                                </button>

                                <button
                                  type="button"
                                  onClick={() => {
                                    const current = Number.parseInt(
                                      editingQty[r.id] ?? currentQtyValue(r, editingQty),
                                      10
                                    );

                                    setEditingQty((prev) => ({
                                      ...prev,
                                      [r.id]: String(
                                        Math.max(1, Number.isFinite(current) ? current - 1 : 1)
                                      ),
                                    }));
                                  }}
                                  className="flex h-5 items-center justify-center border-t border-zinc-300 text-zinc-500 hover:bg-zinc-100 hover:text-zinc-800"
                                  title="Decrease quantity"
                                >
                                  <ChevronDown className="h-3.5 w-3.5" />
                                </button>
                              </div>
                            </div>

                            <button
                              type="button"
                              onClick={() => saveMovementQuantity(r)}
                              title="Save quantity"
                              className="flex h-10 w-10 items-center justify-center rounded-lg border border-zinc-300 bg-white text-zinc-900 shadow-none outline-none hover:bg-zinc-50 focus:border-zinc-500 focus:ring-0"
                            >
                              <Save className="h-4 w-4" />
                              <span className="sr-only">Save quantity</span>
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>


                  </div>
                  {selectedDestinationIsDevice && (
                    <div className="mt-3 rounded-xl border border-amber-200 bg-amber-50 p-3">
                      <div className="text-[11px] font-semibold uppercase tracking-wide text-amber-800">
                        Device install / uninstall
                      </div>

                      <div className="mt-2 grid gap-2 md:grid-cols-2">
                        <div>
                          <label className="mb-1 block text-[11px] font-semibold uppercase tracking-wide text-amber-800">
                            Part to uninstall
                          </label>
                          <Input
                            value={deviceInstallForm.unistall_part}
                            onChange={(e) =>
                              updateDeviceInstallField(
                                r.id,
                                "unistall_part",
                                e.target.value
                              )
                            }
                            placeholder="400-0774"
                            className={`${fieldInputClassName} text-zinc-900 font-medium`}
                          />
                        </div>

                        <div className="relative">
                          <label className="mb-1 block text-[11px] font-semibold uppercase tracking-wide text-amber-800">
                            Destination uninstalled part
                          </label>

                          <Input
                            value={
                              deviceUninstallDestinationOpenRowId === r.id
                                ? deviceUninstallDestinationSearch
                                : selectedDeviceUninstallDestination
                                  ? deviceUninstallDestinationLabel(selectedDeviceUninstallDestination)
                                  : deviceUninstallDestinationSearch
                            }
                            onFocus={() => {
                              setDeviceUninstallDestinationOpenRowId(r.id);
                            }}
                            onChange={(e) => {
                              setDeviceUninstallDestinationOpenRowId(r.id);

                              updateDeviceInstallFields(r.id, {
                                dest_uninstalled_part_search: e.target.value,
                                dest_uninstalled_part: "",
                              });
                            }}
                            onKeyDown={(e) => {
                              if (e.key === "Escape") {
                                setDeviceUninstallDestinationOpenRowId(null);
                              }

                              if (
                                e.key === "Enter" &&
                                filteredDeviceUninstallDestinations.length > 0
                              ) {
                                e.preventDefault();

                                const firstLocation = filteredDeviceUninstallDestinations[0];
                                const code = safeStr(firstLocation.code).trim();

                                if (!locationHasNumericMysimCode(firstLocation)) {
                                  setErr(
                                    `Location ${deviceUninstallDestinationLabel(
                                      firstLocation
                                    )} has no numeric mySim code`
                                  );
                                  return;
                                }

                                updateDeviceInstallFields(r.id, {
                                  dest_uninstalled_part: code,
                                  dest_uninstalled_part_search:
                                    deviceUninstallDestinationLabel(firstLocation),
                                });

                                setDeviceUninstallDestinationOpenRowId(null);
                              }
                            }}
                            onBlur={() => {
                              window.setTimeout(() => {
                                setDeviceUninstallDestinationOpenRowId((current) =>
                                  current === r.id ? null : current
                                );
                              }, 150);
                            }}
                            placeholder="Search warehouse location, e.g. CN235 9D"
                            className={`${fieldInputClassName} text-zinc-900 font-medium`}
                          />

                          {deviceInstallForm.dest_uninstalled_part && (
                            <div className="mt-1 text-[11px] text-amber-800">
                              {/*mySim location ID:{" "}
                              <span className="font-semibold">
                                {deviceInstallForm.dest_uninstalled_part}
                              </span>*/}
                            </div>
                          )}

                          {deviceUninstallDestinationOpenRowId === r.id && (
                            <div className="absolute z-50 mt-1 max-h-56 w-full overflow-auto rounded-lg border border-zinc-200 bg-white shadow-lg">
                              {filteredDeviceUninstallDestinations.length === 0 ? (
                                <div className="px-3 py-2 text-sm text-zinc-500">
                                  No warehouse locations found.
                                </div>
                              ) : (
                                filteredDeviceUninstallDestinations.map((loc) => {
                                  const code = safeStr(loc.code).trim();
                                  const disabled = !locationHasNumericMysimCode(loc);

                                  return (
                                    <button
                                      key={loc.id}
                                      type="button"
                                      disabled={disabled}
                                      onMouseDown={(e) => {
                                        e.preventDefault();
                                      }}
                                      onClick={() => {
                                        if (disabled) {
                                          setErr(
                                            `Location ${deviceUninstallDestinationLabel(
                                              loc
                                            )} has no numeric mySim code`
                                          );
                                          return;
                                        }

                                        updateDeviceInstallFields(r.id, {
                                          dest_uninstalled_part: code,
                                          dest_uninstalled_part_search:
                                            deviceUninstallDestinationLabel(loc),
                                        });

                                        setDeviceUninstallDestinationOpenRowId(null);
                                      }}
                                      className={`flex w-full flex-col px-3 py-2 text-left text-sm ${disabled
                                        ? "cursor-not-allowed bg-zinc-50 text-zinc-400"
                                        : "hover:bg-amber-50"
                                        }`}
                                    >
                                      <span className="font-medium text-zinc-900">
                                        {deviceUninstallDestinationLabel(loc)}
                                      </span>

                                      {/*<span className="text-xs text-zinc-500">
                                        local id: {loc.id} · mySim code: {code || "missing"}
                                      </span>*/}
                                    </button>
                                  );
                                })
                              )}
                            </div>
                          )}
                        </div>

                        <div>
                          <label className="mb-1 block text-[11px] font-semibold uppercase tracking-wide text-amber-800">
                            Uninstalled by
                          </label>

                          <div className="flex min-h-10 items-center rounded-lg border border-zinc-300 bg-zinc-100 px-3 py-2 text-sm font-medium text-zinc-700">
                            {selectedDoneByUser
                              ? userDisplayName(selectedDoneByUser)
                              : doneByForm.mysim_id
                                ? `mySim user ID: ${doneByForm.mysim_id}`
                                : "Select Done by first"}
                          </div>

                          {doneByForm.mysim_id && (
                            <div className="mt-1 text-[11px] text-amber-800">
                            </div>
                          )}
                        </div>

                        <div>
                          <label className="mb-1 block text-[11px] font-semibold uppercase tracking-wide text-amber-800">
                            Reason
                          </label>
                          <textarea
                            value={deviceInstallForm.why_is_it_uninstalled}
                            onChange={(e) =>
                              updateDeviceInstallField(
                                r.id,
                                "why_is_it_uninstalled",
                                e.target.value
                              )
                            }
                            placeholder="Remove for maintenance"
                            rows={2}
                            className="w-full resize-y rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900 outline-none focus:border-zinc-500"
                          />
                        </div>
                      </div>

                      {!deviceInstallComplete && (
                        <p className="mt-2 text-xs font-medium text-amber-800">
                          Complete these fields before confirming the Device movement.
                        </p>
                      )}
                    </div>
                  )}
                  {isMovementExpanded(r.id) && (
                    <div className="mt-2 grid gap-2 md:grid-cols-[195px_195px_48px] md:justify-start">
                      <div className="rounded-xl border border-zinc-200 bg-zinc-50 p-3 md:col-span-3">
                        <div className="grid gap-2 md:grid-cols-[195px_195px_48px]">
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
