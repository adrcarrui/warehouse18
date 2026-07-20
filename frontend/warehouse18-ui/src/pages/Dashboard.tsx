import { useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import {
  BellRing,
  CalendarDays,
  Check,
  ClipboardCheck,
  Database,
  LoaderCircle,
  MapPin,
  RefreshCw,
  Search,
  X,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import {
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import type { PieLabelRenderProps } from "recharts";

import { AppShell } from "../app/AppShell";
import { apiGet } from "../api";
import type { PageOut } from "../api";
import mySimStatusIcon from "../assets/mysim-status-icon.png";
import { Button } from "../ui/Button";
import { Card } from "../ui/Card";

type PeriodPreset =
  | "today"
  | "7days"
  | "30days"
  | "month"
  | "custom";

type MovementOut = {
  id: number;
  movement_type_id: number;
  item_id?: number | null;
  item_key?: string | null;
  from_location_id?: number | null;
  to_location_id?: number | null;
  created_at: string;
  review_status?: string | null;
  mysim_sync_status?: string | null;
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
  is_active?: boolean;
};

type IntegrationCheck = {
  ok: boolean;
  latency_ms?: number | null;
};

type IntegrationsHealthResponse = {
  status: string;
  backend: IntegrationCheck;
  database: IntegrationCheck;
  mysim: IntegrationCheck & {
    rows?: number | null;
  };
};

type ChartSlice = {
  label: string;
  value: number;
  color: string;
};

const PAGE_SIZE = 200;

// Sustituye este valor cuando tengas un endpoint para contar alertas activas.
const ACTIVE_ALERTS = 1;

const SYNCED_STATUSES = new Set([
  "synced",
  "success",
  "succeeded",
  "completed",
  "ok",
]);

const FAILED_STATUSES = new Set(["failed", "error"]);

const MOVEMENT_TYPE_COLORS: Record<string, string> = {
  GI: "#ef4444",
  GR: "#10b981",
  FR: "#10b981",
  GT: "#2563eb",
};

const FALLBACK_TYPE_COLORS = [
  "#8b5cf6",
  "#ec4899",
  "#06b6d4",
  "#f59e0b",
];

const RADIAN = Math.PI / 180;

function startOfDay(date: Date) {
  const value = new Date(date);
  value.setHours(0, 0, 0, 0);
  return value;
}

function endOfDay(date: Date) {
  const value = new Date(date);
  value.setHours(23, 59, 59, 999);
  return value;
}

function toDateInput(date: Date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function presetRange(preset: Exclude<PeriodPreset, "custom">) {
  const today = new Date();
  const to = endOfDay(today);
  let from = startOfDay(today);

  if (preset === "7days" || preset === "30days") {
    from.setDate(
      from.getDate() - (preset === "7days" ? 6 : 29),
    );
  } else if (preset === "month") {
    from = new Date(today.getFullYear(), today.getMonth(), 1);
  }

  return {
    from: toDateInput(from),
    to: toDateInput(to),
  };
}

function rangeToIso(from: string, to: string) {
  return {
    fromDate: startOfDay(
      new Date(`${from}T00:00:00`),
    ).toISOString(),
    toDate: endOfDay(
      new Date(`${to}T00:00:00`),
    ).toISOString(),
  };
}

function syncGroup(
  status?: string | null,
  mySimMovementId?: string | null,
) {
  if (mySimMovementId) return "synced" as const;

  const normalized = status?.trim().toLowerCase() ?? "";

  if (SYNCED_STATUSES.has(normalized)) {
    return "synced" as const;
  }

  if (FAILED_STATUSES.has(normalized)) {
    return "failed" as const;
  }

  return "pending" as const;
}

function formatDateTime(value: string) {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) return value;

  return date.toLocaleString("en-GB", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function renderSectorLabel(
  props: PieLabelRenderProps,
  mode: "name-value" | "value-only",
) {
  const cx = Number(props.cx);
  const cy = Number(props.cy);
  const innerRadius = Number(props.innerRadius);
  const outerRadius = Number(props.outerRadius);
  const midAngle = Number(props.midAngle);
  const value = Number(props.value) || 0;

  if (value <= 0) return null;

  const radius =
    innerRadius + (outerRadius - innerRadius) * 0.56;
  const x = cx + radius * Math.cos(-midAngle * RADIAN);
  const y = cy + radius * Math.sin(-midAngle * RADIAN);

  if (mode === "value-only") {
    return (
      <text
        x={x}
        y={y}
        fill="#ffffff"
        textAnchor="middle"
        dominantBaseline="central"
        pointerEvents="none"
        fontSize="18"
        fontWeight="800"
      >
        {value}
      </text>
    );
  }

  return (
    <text
      x={x}
      y={y}
      fill="#ffffff"
      textAnchor="middle"
      dominantBaseline="central"
      pointerEvents="none"
    >
      <tspan x={x} dy="-0.45em" fontSize="13" fontWeight="700">
        {String(props.name ?? "")}
      </tspan>
      <tspan x={x} dy="1.2em" fontSize="18" fontWeight="800">
        {value}
      </tspan>
    </text>
  );
}

function renderCenterValue(
  props: PieLabelRenderProps,
  value: string,
) {
  const cx = Number(props.cx);
  const cy = Number(props.cy);

  if (!Number.isFinite(cx) || !Number.isFinite(cy)) {
    return null;
  }

  return (
    <text
      x={cx}
      y={cy}
      fill="#ffffff"
      textAnchor="middle"
      dominantBaseline="central"
      pointerEvents="none"
      fontSize="32"
      fontWeight="800"
    >
      {value}
    </text>
  );
}

function DonutChart(props: {
  title: string;
  slices: ChartSlice[];
  centerValue: string;
  sectorLabelMode: "name-value" | "value-only";
  showLegend?: boolean;
}) {
  const data = props.slices.map((slice) => ({
    name: slice.label,
    value: slice.value,
    color: slice.color,
  }));

  const total = data.reduce(
    (sum, item) => sum + item.value,
    0,
  );

  const showLegend = props.showLegend ?? false;
  const chartCenterY = "50%";

  return (
    <Card className="min-h-[320px] border-slate-200 bg-white p-4 shadow-sm">
      <div className="text-sm font-semibold text-slate-900">
        {props.title}
      </div>

      {total === 0 ? (
        <div className="flex h-[260px] items-center justify-center text-sm text-slate-400">
          No data for this period
        </div>
      ) : (
        <>
          <div className="mt-2 h-[230px] min-w-0">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
              <Pie
                data={[{ name: "center", value: 1 }]}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy={chartCenterY}
                innerRadius={0}
                outerRadius={57}
                fill="#020617"
                stroke="none"
                legendType="none"
                isAnimationActive={false}
              />

              <Pie
                data={data}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy={chartCenterY}
                innerRadius={58}
                outerRadius={98}
                paddingAngle={1}
                labelLine={false}
                isAnimationActive={false}
                label={(labelProps) =>
                  renderSectorLabel(
                    labelProps,
                    props.sectorLabelMode,
                  )
                }
              >
                {data.map((entry) => (
                  <Cell
                    key={entry.name}
                    fill={entry.color}
                    stroke="#ffffff"
                    strokeWidth={1}
                  />
                ))}

              </Pie>

              <Pie
                data={[{ name: "center-value", value: 1 }]}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy={chartCenterY}
                innerRadius={0}
                outerRadius={1}
                fill="transparent"
                stroke="none"
                legendType="none"
                isAnimationActive={false}
                labelLine={false}
                label={(labelProps) =>
                  renderCenterValue(
                    labelProps,
                    props.centerValue,
                  )
                }
              />

              <Tooltip
                formatter={(value, name) => [
                  Number(value),
                  String(name),
                ]}
                contentStyle={{
                  backgroundColor: "#020617",
                  border: "1px solid #334155",
                  borderRadius: "10px",
                  color: "#ffffff",
                }}
                itemStyle={{ color: "#ffffff" }}
              />

              </PieChart>
            </ResponsiveContainer>
          </div>

          {showLegend ? (
            <div className="mt-2 flex min-h-5 flex-wrap items-center justify-center gap-x-2.5 gap-y-1">
              {data.map((entry) => (
                <div
                  key={entry.name}
                  className="inline-flex items-center gap-1 whitespace-nowrap text-[11px] font-medium text-slate-700"
                >
                  <span
                    className="h-2 w-2 shrink-0 rounded-full"
                    style={{ backgroundColor: entry.color }}
                  />
                  <span>{entry.name}</span>
                </div>
              ))}
            </div>
          ) : null}
        </>
      )}
    </Card>
  );
}

function QuickActionButton(props: {
  to: string;
  label: string;
  icon: LucideIcon;
  count?: number;
  color: "red" | "amber" | "blue";
}) {
  const Icon = props.icon;
  const count = Math.max(0, props.count ?? 0);

  const colors = {
    red: "border-red-300 bg-red-50 text-red-500 hover:bg-red-100",
    amber:
      "border-amber-300 bg-amber-50 text-amber-500 hover:bg-amber-100",
    blue: "border-blue-300 bg-blue-50 text-blue-400 hover:bg-blue-100",
  };

  return (
    <Link
      to={props.to}
      aria-label={
        count > 0
          ? `${props.label}. ${count} pending`
          : props.label
      }
      title={
        count > 0
          ? `${props.label}: ${count}`
          : props.label
      }
      className={`relative flex h-20 w-20 items-center justify-center rounded-3xl border shadow-md transition duration-200 hover:-translate-y-0.5 hover:shadow-lg ${colors[props.color]}`}
    >
      <Icon className="h-9 w-9" strokeWidth={2.1} />
      <span className="sr-only">{props.label}</span>

      {count > 0 ? (
        <span className="absolute -right-2 -top-2 flex h-8 min-w-8 items-center justify-center rounded-full border-[3px] border-slate-950 bg-slate-950 px-1.5 text-xs font-bold text-white shadow-md">
          {count > 99 ? "99+" : count}
        </span>
      ) : null}
    </Link>
  );
}

function ConnectionStatusIndicator(props: {
  kind: "database" | "mysim";
  label: string;
  ok: boolean | null;
  checking: boolean;
  latencyMs?: number | null;
  detail?: string | null;
}) {
  const statusClasses = props.checking
    ? "border-slate-300 bg-slate-50 text-slate-500"
    : props.ok
      ? "border-emerald-300 bg-emerald-50 text-emerald-700"
      : "border-red-300 bg-red-50 text-red-600";

  const title = props.checking
    ? `${props.label}: checking connection`
    : props.ok
      ? `${props.label}: connected${
          props.latencyMs != null
            ? ` · ${props.latencyMs} ms`
            : ""
        }${props.detail ? ` · ${props.detail}` : ""}`
      : `${props.label}: unavailable${
          props.detail ? ` · ${props.detail}` : ""
        }`;

  return (
    <div
      role="status"
      aria-label={title}
      title={title}
      className={`relative flex h-20 w-20 cursor-default flex-col items-center justify-center rounded-3xl border shadow-sm ${statusClasses}`}
    >
      {props.kind === "database" ? (
        <Database className="h-8 w-8" strokeWidth={2} />
      ) : (
        <img
          src={mySimStatusIcon}
          alt=""
          aria-hidden="true"
          className="h-[72px] w-[72px] rounded-2xl object-contain"
        />
      )}

      <span
        className={`absolute -right-1.5 -top-1.5 flex h-6 w-6 items-center justify-center rounded-full border-2 border-white text-white shadow-sm ${
          props.checking
            ? "bg-slate-400"
            : props.ok
              ? "bg-emerald-500"
              : "bg-red-500"
        }`}
      >
        {props.checking ? (
          <LoaderCircle className="h-3.5 w-3.5 animate-spin" />
        ) : props.ok ? (
          <Check className="h-3.5 w-3.5" strokeWidth={3} />
        ) : (
          <X className="h-3.5 w-3.5" strokeWidth={3} />
        )}
      </span>
    </div>
  );
}

function DashboardActions(props: {
  alerts: number;
  pendingReview: number;
  health: IntegrationsHealthResponse | null;
  healthChecking: boolean;
  healthError: string | null;
}) {
  return (
    <div className="col-span-2 flex min-h-[108px] items-center justify-center gap-4 rounded-xl border border-slate-200 bg-white px-4 py-3 shadow-sm">
      <div className="flex items-center gap-4">
        <QuickActionButton
          to="/alerts"
          label="Alerts"
          icon={BellRing}
          count={props.alerts}
          color="red"
        />

        <QuickActionButton
          to="/rfid-review"
          label="RFID Review"
          icon={ClipboardCheck}
          count={props.pendingReview}
          color="amber"
        />

        <QuickActionButton
          to="/item-location"
          label="Item Location"
          icon={MapPin}
          color="blue"
        />
      </div>

      <div className="h-14 w-px shrink-0 bg-slate-200" />

      <div className="flex items-center gap-3">
        <ConnectionStatusIndicator
          kind="database"
          label="Database"
          ok={props.health?.database.ok ?? null}
          checking={props.healthChecking}
          latencyMs={props.health?.database.latency_ms}
          detail={props.healthError}
        />

        <ConnectionStatusIndicator
          kind="mysim"
          label="mySim"
          ok={props.health?.mysim.ok ?? null}
          checking={props.healthChecking}
          latencyMs={props.health?.mysim.latency_ms}
          detail={
            props.healthError ??
            (props.health?.mysim.rows != null
              ? `${props.health.mysim.rows} row${
                  props.health.mysim.rows === 1 ? "" : "s"
                }`
              : null)
          }
        />
      </div>
    </div>
  );
}

function SyncStatusBadge(props: {
  group: "synced" | "failed" | "pending";
}) {
  const styles = {
    synced: "bg-emerald-100 text-emerald-700",
    failed: "bg-red-100 text-red-700",
    pending: "bg-amber-100 text-amber-700",
  };

  const labels = {
    synced: "Synced",
    failed: "Failed",
    pending: "Pending",
  };

  return (
    <span
      className={`inline-flex rounded-full px-2 py-1 text-[10px] font-semibold ${styles[props.group]}`}
    >
      {labels[props.group]}
    </span>
  );
}

function RecentMovementsTable(props: {
  movements: MovementOut[];
  searchMovements: MovementOut[];
  searchMovementsLoading: boolean;
  searchMovementsError: string | null;
  movementTypes: Record<number, MovementTypeOut>;
  locationMap: Record<number, LocationOut>;
  loading: boolean;
}) {
  const [movementSearch, setMovementSearch] = useState("");
  const hasMovementSearch = movementSearch.trim().length > 0;
  const movementSource = hasMovementSearch
    ? props.searchMovements
    : props.movements;
  const tableLoading =
    props.loading ||
    (hasMovementSearch && props.searchMovementsLoading);
  const tableError = hasMovementSearch
    ? props.searchMovementsError
    : null;

  const matchingMovements = useMemo(() => {
    const query = movementSearch.trim().toLowerCase();

    return movementSource
      .map((movement) => {
        const movementType =
          props.movementTypes[movement.movement_type_id];
        const typeCode =
          movementType?.code ?? String(movement.movement_type_id);
        const typeName = movementType?.name ?? "";
        const item = String(
          movement.item_key ?? movement.item_id ?? "—",
        );

        const sourceLocation =
          movement.from_location_id == null
            ? "—"
            : props.locationMap[movement.from_location_id]?.name ||
              props.locationMap[movement.from_location_id]?.code ||
              "…";

        const destinationLocation =
          movement.to_location_id == null
            ? "—"
            : props.locationMap[movement.to_location_id]?.name ||
              props.locationMap[movement.to_location_id]?.code ||
              "…";

        const group = syncGroup(
          movement.mysim_sync_status,
          movement.mysim_movement_id,
        );

        return {
          movement,
          typeCode,
          typeName,
          item,
          sourceLocation,
          destinationLocation,
          group,
        };
      })
      .filter((row) => {
        if (!query) return true;

        return [
          row.typeCode,
          row.typeName,
          row.item,
          row.sourceLocation,
          row.destinationLocation,
          row.group,
        ]
          .join(" ")
          .toLowerCase()
          .includes(query);
      });
  }, [
    movementSearch,
    movementSource,
    props.locationMap,
    props.movementTypes,
  ]);

  const visibleMovements = hasMovementSearch
    ? matchingMovements
    : matchingMovements.slice(0, 8);

  return (
    <Card className="min-h-[484px] min-w-0 border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex items-center gap-3">
        <div>
          <div className="text-sm font-semibold text-slate-900">
            Latest movements
          </div>
          <div className="mt-0.5 text-xs text-slate-500">
            {hasMovementSearch && props.searchMovementsLoading
              ? "Loading complete movement history…"
              : tableError
                ? "Could not load movement history"
                : hasMovementSearch
              ? `${matchingMovements.length} matching movement${
                  matchingMovements.length === 1 ? "" : "s"
                }`
                  : "Up to eight recent records"}
          </div>
        </div>

        <div className="relative ml-auto w-full max-w-[240px]">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            value={movementSearch}
            onChange={(event) =>
              setMovementSearch(event.target.value)
            }
            placeholder="Type, item, location or status"
            aria-label="Search latest movements"
            className="h-9 w-full rounded-xl border border-slate-200 bg-slate-50 pl-9 pr-8 text-xs text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-blue-400 focus:bg-white focus:ring-2 focus:ring-blue-100"
          />

          {movementSearch ? (
            <button
              type="button"
              onClick={() => setMovementSearch("")}
              aria-label="Clear movement search"
              className="absolute right-2 top-1/2 flex h-5 w-5 -translate-y-1/2 items-center justify-center rounded-full text-slate-400 transition hover:bg-slate-200 hover:text-slate-700"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          ) : null}
        </div>

        <Link
          to="/movements"
          className="inline-flex h-9 items-center justify-center rounded-xl border border-slate-200 bg-slate-50 px-3 text-sm font-medium text-slate-800 transition hover:bg-slate-100"
        >
          View all
        </Link>
      </div>

      <div className="mt-3 max-h-[410px] overflow-auto rounded-xl border border-slate-200">
        <table className="w-full min-w-[680px] table-fixed text-xs">
          <colgroup>
            <col className="w-[145px]" />
            <col className="w-[55px]" />
            <col className="w-[135px]" />
            <col className="w-[120px]" />
            <col className="w-[120px]" />
            <col className="w-[90px]" />
          </colgroup>

          <thead className="sticky top-0 z-10 bg-blue-950">
            <tr className="text-left text-white">
              <th className="px-3 py-2.5 font-semibold">Date</th>
              <th className="px-2 py-2.5 text-center font-semibold">
                Type
              </th>
              <th className="px-2 py-2.5 font-semibold">Item</th>
              <th className="px-2 py-2.5 font-semibold">From</th>
              <th className="px-2 py-2.5 font-semibold">To</th>
              <th className="px-2 py-2.5 text-center font-semibold">
                mySim
              </th>
            </tr>
          </thead>

          <tbody className="divide-y divide-slate-200 bg-white">
            {visibleMovements.map((row) => {
              const { movement } = row;

              return (
                <tr
                  key={movement.id}
                  className="transition hover:bg-blue-50/60"
                >
                  <td
                    className="truncate whitespace-nowrap px-3 py-2.5 text-slate-600"
                    title={formatDateTime(movement.created_at)}
                  >
                    {formatDateTime(movement.created_at)}
                  </td>

                  <td className="truncate px-2 py-2.5 text-center font-semibold text-slate-900">
                    {row.typeCode}
                  </td>

                  <td
                    className="truncate px-2 py-2.5 text-slate-600"
                    title={row.item}
                  >
                    {row.item}
                  </td>

                  <td
                    className="truncate whitespace-nowrap px-2 py-2.5 text-slate-600"
                    title={row.sourceLocation}
                  >
                    {row.sourceLocation}
                  </td>

                  <td
                    className="truncate whitespace-nowrap px-2 py-2.5 text-slate-600"
                    title={row.destinationLocation}
                  >
                    {row.destinationLocation}
                  </td>

                  <td className="px-2 py-2.5 text-center">
                    <SyncStatusBadge group={row.group} />
                  </td>
                </tr>
              );
            })}

            {tableError ? (
              <tr>
                <td
                  colSpan={6}
                  className="px-3 py-12 text-center text-red-600"
                >
                  Could not load movement history: {tableError}
                </td>
              </tr>
            ) : null}

            {!tableLoading &&
            !tableError &&
            visibleMovements.length === 0 ? (
              <tr>
                <td
                  colSpan={6}
                  className="px-3 py-12 text-center text-slate-400"
                >
                  {hasMovementSearch
                    ? "No movements match this search."
                    : "No movements found in this period."}
                </td>
              </tr>
            ) : null}

            {tableLoading ? (
              <tr>
                <td
                  colSpan={6}
                  className="px-3 py-12 text-center text-slate-400"
                >
                  {hasMovementSearch
                    ? "Loading complete movement history…"
                    : "Loading metrics…"}
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>
    </Card>
  );
}

export default function DashboardPage() {
  const initialRange = presetRange("30days");

  const [preset, setPreset] =
    useState<PeriodPreset>("30days");
  const [from, setFrom] = useState(initialRange.from);
  const [to, setTo] = useState(initialRange.to);
  const [movements, setMovements] = useState<MovementOut[]>([]);
  const [movementHistory, setMovementHistory] = useState<
    MovementOut[]
  >([]);
  const [movementHistoryLoading, setMovementHistoryLoading] =
    useState(true);
  const [movementHistoryError, setMovementHistoryError] =
    useState<string | null>(null);
  const [movementTypes, setMovementTypes] = useState<
    Record<number, MovementTypeOut>
  >({});
  const [locationMap, setLocationMap] = useState<
    Record<number, LocationOut>
  >({});
  const [pendingReviewCount, setPendingReviewCount] =
    useState(0);
  const [integrationsHealth, setIntegrationsHealth] =
    useState<IntegrationsHealthResponse | null>(null);
  const [healthChecking, setHealthChecking] = useState(true);
  const [healthError, setHealthError] = useState<
    string | null
  >(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const requestId = useRef(0);
  const requestedLocationIds = useRef<Set<number>>(new Set());
  const invalidRange = !from || !to || from > to;

  async function loadMetrics(
    range?: { from: string; to: string },
  ) {
    const selectedFrom = range?.from ?? from;
    const selectedTo = range?.to ?? to;

    if (
      !selectedFrom ||
      !selectedTo ||
      selectedFrom > selectedTo
    ) {
      return;
    }

    const currentRequest = ++requestId.current;
    setLoading(true);
    setError(null);

    try {
      const { fromDate, toDate } = rangeToIso(
        selectedFrom,
        selectedTo,
      );

      const firstPagePromise = apiGet<PageOut<MovementOut>>(
        "/api/movements",
        {
          from_date: fromDate,
          to_date: toDate,
          page: 1,
          page_size: PAGE_SIZE,
        },
      );

      const typesPromise = apiGet<MovementTypeOut[]>(
        "/api/movement-types",
      );

      const [{ data: firstPage }, { data: types }] =
        await Promise.all([firstPagePromise, typesPromise]);

      const allRows = [...firstPage.items];

      for (
        let page = 2;
        page <= firstPage.pages;
        page += 1
      ) {
        const { data } = await apiGet<PageOut<MovementOut>>(
          "/api/movements",
          {
            from_date: fromDate,
            to_date: toDate,
            page,
            page_size: PAGE_SIZE,
          },
        );

        allRows.push(...data.items);
      }

      if (currentRequest !== requestId.current) return;

      const typeMap: Record<number, MovementTypeOut> = {};

      for (const type of types) {
        typeMap[type.id] = type;
      }

      setMovementTypes(typeMap);
      setMovements(allRows);
    } catch (caught: unknown) {
      if (currentRequest !== requestId.current) return;

      setError(
        caught instanceof Error
          ? caught.message
          : String(caught),
      );
      setMovements([]);
    } finally {
      if (currentRequest === requestId.current) {
        setLoading(false);
      }
    }
  }

  async function loadMovementHistory() {
    setMovementHistoryLoading(true);
    setMovementHistoryError(null);

    try {
      const { data: firstPage } = await apiGet<
        PageOut<MovementOut>
      >("/api/movements", {
        page: 1,
        page_size: PAGE_SIZE,
      });

      const allRows = [...firstPage.items];

      for (
        let page = 2;
        page <= firstPage.pages;
        page += 1
      ) {
        const { data } = await apiGet<PageOut<MovementOut>>(
          "/api/movements",
          {
            page,
            page_size: PAGE_SIZE,
          },
        );

        allRows.push(...data.items);
      }

      setMovementHistory(allRows);
    } catch (caught: unknown) {
      setMovementHistory([]);
      setMovementHistoryError(
        caught instanceof Error
          ? caught.message
          : String(caught),
      );
    } finally {
      setMovementHistoryLoading(false);
    }
  }

  async function loadPendingReviewCount() {
    try {
      const { data, meta } = await apiGet<
        PageOut<MovementOut>
      >("/api/movements", {
        review_status: "pending",
        page: 1,
        page_size: 1,
      });

      const total = meta.total ?? data.total ?? data.items.length;

      setPendingReviewCount(
        Math.max(0, Number(total) || 0),
      );
    } catch (caught: unknown) {
      console.error(
        "Could not load pending RFID Review count:",
        caught,
      );
    }
  }

  async function loadLocationMap() {
    try {
      const pageSize = 200;
      let currentPage = 1;
      let totalPages = 1;
      const next: Record<number, LocationOut> = {};

      while (currentPage <= totalPages) {
        const { data, meta } = await apiGet<
          PageOut<LocationOut>
        >("/api/locations", {
          include_inactive: true,
          page: currentPage,
          page_size: pageSize,
        });

        for (const location of data.items) {
          next[location.id] = location;
        }

        totalPages =
          meta.pages && meta.pages > 0
            ? meta.pages
            : Math.max(
                1,
                Math.ceil(
                  (meta.total || 0) /
                    (meta.pageSize || pageSize),
                ),
              );

        currentPage += 1;
      }

      setLocationMap(next);
    } catch (caught: unknown) {
      console.error("Could not load location names:", caught);
      setLocationMap({});
    }
  }

  useEffect(() => {
    void loadMetrics();
    void loadLocationMap();
    void loadMovementHistory();
    // El período se aplica mediante el botón Apply.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    void loadPendingReviewCount();

    const intervalId = window.setInterval(() => {
      void loadPendingReviewCount();
    }, 2000);

    return () => window.clearInterval(intervalId);
  }, []);

  useEffect(() => {
    const referencedLocationIds = new Set<number>();

    for (const movement of [
      ...movements,
      ...movementHistory,
    ]) {
      if (movement.from_location_id != null) {
        referencedLocationIds.add(movement.from_location_id);
      }

      if (movement.to_location_id != null) {
        referencedLocationIds.add(movement.to_location_id);
      }
    }

    const missingLocationIds = [...referencedLocationIds].filter(
      (locationId) =>
        !locationMap[locationId] &&
        !requestedLocationIds.current.has(locationId),
    );

    if (missingLocationIds.length === 0) return;

    for (const locationId of missingLocationIds) {
      requestedLocationIds.current.add(locationId);
    }

    async function loadMissingLocationNames() {
      const loadedLocations: Record<number, LocationOut> = {};
      const batchSize = 20;

      for (
        let index = 0;
        index < missingLocationIds.length;
        index += batchSize
      ) {
        const batch = missingLocationIds.slice(
          index,
          index + batchSize,
        );

        const results = await Promise.allSettled(
          batch.map((locationId) =>
            apiGet<LocationOut>(`/api/locations/${locationId}`),
          ),
        );

        results.forEach((result, resultIndex) => {
          const locationId = batch[resultIndex];

          if (result.status === "fulfilled") {
            loadedLocations[locationId] = result.value.data;
          } else {
            requestedLocationIds.current.delete(locationId);
            console.error(
              `Could not load location ${locationId}:`,
              result.reason,
            );
          }
        });
      }

      if (Object.keys(loadedLocations).length > 0) {
        setLocationMap((current) => ({
          ...current,
          ...loadedLocations,
        }));
      }
    }

    void loadMissingLocationNames();
  }, [locationMap, movementHistory, movements]);

  useEffect(() => {
    let active = true;

    async function loadIntegrationsHealth() {
      try {
        const { data } =
          await apiGet<IntegrationsHealthResponse>(
            "/api/integrations/health",
          );

        if (!active) return;

        setIntegrationsHealth(data);
        setHealthError(null);
      } catch (caught: unknown) {
        if (!active) return;

        setIntegrationsHealth(null);
        setHealthError(
          caught instanceof Error
            ? caught.message
            : String(caught),
        );
      } finally {
        if (active) {
          setHealthChecking(false);
        }
      }
    }

    void loadIntegrationsHealth();

    const intervalId = window.setInterval(() => {
      void loadIntegrationsHealth();
    }, 20_000);

    return () => {
      active = false;
      window.clearInterval(intervalId);
    };
  }, []);

  function selectPreset(
    nextPreset: Exclude<PeriodPreset, "custom">,
  ) {
    const nextRange = presetRange(nextPreset);
    setPreset(nextPreset);
    setFrom(nextRange.from);
    setTo(nextRange.to);
    void loadMetrics(nextRange);
  }

  const metrics = useMemo(() => {
    let synced = 0;
    let failed = 0;
    let pending = 0;
    const byType = new Map<string, number>();

    for (const movement of movements) {
      const group = syncGroup(
        movement.mysim_sync_status,
        movement.mysim_movement_id,
      );

      if (group === "synced") synced += 1;
      else if (group === "failed") failed += 1;
      else pending += 1;

      const code =
        movementTypes[movement.movement_type_id]?.code ??
        `Type ${movement.movement_type_id}`;

      byType.set(code, (byType.get(code) ?? 0) + 1);
    }

    return {
      total: movements.length,
      synced,
      failed,
      pending,
      syncRate:
        movements.length > 0
          ? Math.round((synced / movements.length) * 100)
          : 0,
      byType: [...byType.entries()].sort(
        (a, b) => b[1] - a[1],
      ),
    };
  }, [movementTypes, movements]);

  const movementCountByCode = new Map(
    metrics.byType.map(([code, value]) => [
      code.toUpperCase(),
      value,
    ]),
  );

  const mainTypeSlices: ChartSlice[] = [
    {
      label: "Good Issue",
      value: movementCountByCode.get("GI") ?? 0,
      color: "#ef4444",
    },
    {
      label: "Good Transfer",
      value: movementCountByCode.get("GT") ?? 0,
      color: "#2563eb",
    },
    {
      label: "Good Receipt",
      value:
        (movementCountByCode.get("GR") ?? 0) +
        (movementCountByCode.get("FR") ?? 0),
      color: "#10b981",
    },
  ];

  const knownMovementCodes = new Set(["GI", "GT", "GR", "FR"]);

  const extraTypeSlices: ChartSlice[] = metrics.byType
    .filter(
      ([code]) =>
        !knownMovementCodes.has(code.toUpperCase()),
    )
    .map(([label, value], index) => ({
      label,
      value,
      color:
        MOVEMENT_TYPE_COLORS[label.toUpperCase()] ??
        FALLBACK_TYPE_COLORS[
          index % FALLBACK_TYPE_COLORS.length
        ],
    }));

  const typeSlices: ChartSlice[] = [
    ...mainTypeSlices,
    ...extraTypeSlices,
  ];

  const syncSlices: ChartSlice[] = [
    {
      label: "Failed",
      value: metrics.failed,
      color: "#ef4444",
    },
    {
      label: "Pending",
      value: metrics.pending,
      color: "#f59e0b",
    },
    {
      label: "Synced",
      value: metrics.synced,
      color: "#10b981",
    },
  ];

  const sortedMovements = useMemo(
    () =>
      [...movements]
        .sort(
          (a, b) =>
            new Date(b.created_at).getTime() -
            new Date(a.created_at).getTime(),
        ),
    [movements],
  );

  const sortedMovementHistory = useMemo(
    () =>
      [...movementHistory].sort(
        (a, b) =>
          new Date(b.created_at).getTime() -
          new Date(a.created_at).getTime(),
      ),
    [movementHistory],
  );

  return (
    <AppShell
      title="Dashboard"
      subtitle="Warehouse activity and mySim synchronization"
    >
      <div className="space-y-4">
        <Card className="border-slate-200 bg-white p-4 shadow-sm">
          <div className="flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
            <div className="flex flex-col gap-3 xl:flex-row xl:items-center">
              <div className="flex items-center gap-2 text-base font-semibold text-slate-900">
                <CalendarDays className="h-10 w-10 text-blue-700" />
              </div>

              <div className="flex flex-wrap gap-2">
                {(
                  [
                    ["today", "Today"],
                    ["7days", "Last 7 days"],
                    ["30days", "Last 30 days"],
                    ["month", "This month"],
                  ] as const
                ).map(([value, label]) => (
                  <button
                    key={value}
                    type="button"
                    onClick={() => selectPreset(value)}
                    className={`rounded-lg border px-3 py-2 text-xs font-semibold transition ${
                      preset === value
                        ? "border-blue-600 bg-blue-600 text-white shadow-sm"
                        : "border-slate-200 bg-slate-50 text-slate-700 hover:border-blue-300 hover:bg-blue-50"
                    }`}
                  >
                    {label}
                  </button>
                ))}
              </div>
            </div>

            <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
              <label className="flex items-center gap-2 text-xs font-semibold text-slate-500">
                <span className="whitespace-nowrap">From</span>
                <input
                  type="date"
                  value={from}
                  max={to || undefined}
                  onChange={(event) => {
                    setFrom(event.target.value);
                    setPreset("custom");
                  }}
                  className="block h-10 rounded-lg border border-slate-200 bg-slate-50 px-3 text-sm font-medium text-slate-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                />
              </label>

              <label className="flex items-center gap-2 text-xs font-semibold text-slate-500">
                <span className="whitespace-nowrap">To</span>
                <input
                  type="date"
                  value={to}
                  min={from || undefined}
                  onChange={(event) => {
                    setTo(event.target.value);
                    setPreset("custom");
                  }}
                  className="block h-10 rounded-lg border border-slate-200 bg-slate-50 px-3 text-sm font-medium text-slate-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                />
              </label>

              <Button
                type="button"
                onClick={() => void loadMetrics()}
                disabled={loading || invalidRange}
                className="bg-blue-950 hover:bg-blue-900"
              >
                <RefreshCw
                  className={`h-4 w-4 ${
                    loading ? "animate-spin" : ""
                  }`}
                />
                Apply
              </Button>
            </div>
          </div>

          {invalidRange ? (
            <div className="mt-3 text-xs font-medium text-red-600">
              The start date must be before the end date.
            </div>
          ) : null}
        </Card>

        {error ? (
          <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
            Could not load metrics: {error}
          </div>
        ) : null}

        <div className="overflow-x-auto pb-2">
          <div className="grid min-w-[1280px] grid-cols-[minmax(540px,0.8fr)_minmax(720px,1.2fr)] items-stretch gap-4">
            <div className="grid grid-cols-2 gap-4">
              <DonutChart
                title="Movements by type"
                slices={typeSlices}
                centerValue={String(metrics.total)}
                sectorLabelMode="value-only"
                showLegend
              />

              <DonutChart
                title="mySim synchronization"
                slices={syncSlices}
                centerValue={`${metrics.syncRate}%`}
                sectorLabelMode="value-only"
                showLegend
              />

              <DashboardActions
                alerts={ACTIVE_ALERTS}
                pendingReview={pendingReviewCount}
                health={integrationsHealth}
                healthChecking={healthChecking}
                healthError={healthError}
              />
            </div>

            <RecentMovementsTable
              movements={sortedMovements}
              searchMovements={sortedMovementHistory}
              searchMovementsLoading={movementHistoryLoading}
              searchMovementsError={movementHistoryError}
              movementTypes={movementTypes}
              locationMap={locationMap}
              loading={loading}
            />
          </div>
        </div>
      </div>
    </AppShell>
  );
}
