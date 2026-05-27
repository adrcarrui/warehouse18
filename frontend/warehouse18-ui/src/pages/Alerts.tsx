import { useEffect, useMemo, useState } from "react";
import {
  BellRing,
  CheckCircle2,
  Eye,
  RefreshCcw,
  ShieldAlert,
} from "lucide-react";

import { AppShell } from "../app/AppShell";
import { Button } from "../ui/Button";

type AlertSeverity = "info" | "warning" | "critical";
type AlertStatus = "open" | "acknowledged" | "resolved" | "dismissed";

type AlertItem = {
  id: number;
  code: string;
  title: string;
  message: string;
  severity: AlertSeverity;
  status: AlertStatus;
  source: string;
  entityType: string | null;
  entityId: string | null;
  movementId: number | null;
  itemId: number | null;
  epc: string | null;
  createdAt: string;
  updatedAt: string | null;
  acknowledgedAt: string | null;
  resolvedAt: string | null;
  metadata: Record<string, unknown> | null;
};

function severityClass(severity: AlertSeverity) {
  if (severity === "critical") return "border-red-200 bg-red-50 text-red-700";
  if (severity === "warning")
    return "border-amber-200 bg-amber-50 text-amber-700";

  return "border-blue-200 bg-blue-50 text-blue-700";
}

function statusClass(status: AlertStatus) {
  if (status === "open") return "border-red-200 bg-red-50 text-red-700";
  if (status === "acknowledged")
    return "border-amber-200 bg-amber-50 text-amber-700";
  if (status === "resolved")
    return "border-green-200 bg-green-50 text-green-700";

  return "border-zinc-200 bg-zinc-50 text-zinc-700";
}

function formatDate(value: string | null) {
  if (!value) return "—";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString();
}

function formatCode(code: string) {
  return code.replaceAll("_", " ");
}

function formatEntity(alert: AlertItem) {
  if (alert.entityType && alert.entityId) {
    return `${alert.entityType}: ${alert.entityId}`;
  }

  if (alert.movementId) {
    return `movement: #${alert.movementId}`;
  }

  if (alert.itemId) {
    return `item: #${alert.itemId}`;
  }

  if (alert.epc) {
    return `epc: ${alert.epc}`;
  }

  return "—";
}

function mapAlert(row: any): AlertItem {
  return {
    id: row.id,
    code: row.code,
    title: row.title,
    message: row.message,
    severity: row.severity,
    status: row.status,
    source: row.source,
    entityType: row.entity_type,
    entityId: row.entity_id,
    movementId: row.movement_id,
    itemId: row.item_id,
    epc: row.epc,
    createdAt: row.created_at,
    updatedAt: row.updated_at,
    acknowledgedAt: row.acknowledged_at,
    resolvedAt: row.resolved_at,
    metadata: row.metadata,
  };
}

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [statusFilter, setStatusFilter] = useState<"all" | AlertStatus>("all");
  const [severityFilter, setSeverityFilter] = useState<
    "all" | AlertSeverity
  >("all");
  const [sourceFilter, setSourceFilter] = useState<"all" | string>("all");

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadAlerts(options?: { silent?: boolean }) {
    try {
      if (options?.silent) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }

      setError(null);

      const params = new URLSearchParams();

      if (statusFilter !== "all") {
        params.set("status", statusFilter);
      }

      if (severityFilter !== "all") {
        params.set("severity", severityFilter);
      }

      if (sourceFilter !== "all") {
        params.set("source", sourceFilter);
      }

      params.set("limit", "200");

      const response = await fetch(`/api/alerts?${params.toString()}`);

      if (!response.ok) {
        throw new Error(`Failed to load alerts: ${response.status}`);
      }

      const data = await response.json();

      setAlerts(data.map(mapAlert));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load alerts");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  useEffect(() => {
    void loadAlerts();

    const intervalId = window.setInterval(() => {
      void loadAlerts({ silent: true });
    }, 10000);

    return () => {
      window.clearInterval(intervalId);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [statusFilter, severityFilter, sourceFilter]);

  const openCount = alerts.filter((alert) => alert.status === "open").length;

  const acknowledgedCount = alerts.filter(
    (alert) => alert.status === "acknowledged"
  ).length;

  const criticalCount = alerts.filter(
    (alert) => alert.severity === "critical"
  ).length;

  const filteredAlerts = useMemo(() => {
    return alerts.filter((alert) => {
      if (statusFilter !== "all" && alert.status !== statusFilter) return false;

      if (severityFilter !== "all" && alert.severity !== severityFilter) {
        return false;
      }

      if (sourceFilter !== "all" && alert.source !== sourceFilter) {
        return false;
      }

      return true;
    });
  }, [alerts, statusFilter, severityFilter, sourceFilter]);

  const availableSources = useMemo(() => {
    const sources = new Set(alerts.map((alert) => alert.source).filter(Boolean));
    return Array.from(sources).sort();
  }, [alerts]);

  async function acknowledgeAlert(alertId: number) {
    try {
      const response = await fetch(`/api/alerts/${alertId}/acknowledge`, {
        method: "PATCH",
      });

      if (!response.ok) {
        throw new Error(`Failed to acknowledge alert: ${response.status}`);
      }

      const updated = mapAlert(await response.json());

      setAlerts((prev) =>
        prev.map((alert) => (alert.id === updated.id ? updated : alert))
      );
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to acknowledge alert"
      );
    }
  }

  async function resolveAlert(alertId: number) {
    try {
      const response = await fetch(`/api/alerts/${alertId}/resolve`, {
        method: "PATCH",
      });

      if (!response.ok) {
        throw new Error(`Failed to resolve alert: ${response.status}`);
      }

      const updated = mapAlert(await response.json());

      setAlerts((prev) =>
        prev.map((alert) => (alert.id === updated.id ? updated : alert))
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to resolve alert");
    }
  }

  return (
    <AppShell title="Alerts" subtitle="Alerts and notices">
      <div className="space-y-4">
        <div className="grid gap-4 md:grid-cols-3">
          <div className="rounded-xl border border-zinc-200 bg-white p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm font-semibold text-zinc-700">
                  Open alerts
                </div>
                <div className="mt-2 text-3xl font-bold text-zinc-900">
                  {openCount}
                </div>
              </div>

              <div className="flex h-11 w-11 items-center justify-center rounded-xl border border-red-200 bg-red-50 text-red-700">
                <ShieldAlert className="h-5 w-5" />
              </div>
            </div>
          </div>

          <div className="rounded-xl border border-zinc-200 bg-white p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm font-semibold text-zinc-700">
                  Acknowledged
                </div>
                <div className="mt-2 text-3xl font-bold text-zinc-900">
                  {acknowledgedCount}
                </div>
              </div>

              <div className="flex h-11 w-11 items-center justify-center rounded-xl border border-amber-200 bg-amber-50 text-amber-700">
                <BellRing className="h-5 w-5" />
              </div>
            </div>
          </div>

          <div className="rounded-xl border border-zinc-200 bg-white p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm font-semibold text-zinc-700">
                  Critical
                </div>
                <div className="mt-2 text-3xl font-bold text-zinc-900">
                  {criticalCount}
                </div>
              </div>

              <div className="flex h-11 w-11 items-center justify-center rounded-xl border border-green-200 bg-green-50 text-green-700">
                <CheckCircle2 className="h-5 w-5" />
              </div>
            </div>
          </div>
        </div>

        <div className="rounded-xl border border-zinc-200 bg-white">
          <div className="flex flex-col gap-3 border-b border-zinc-200 px-4 py-3 xl:flex-row xl:items-center xl:justify-between">
            <div>
              <div className="text-sm font-semibold text-zinc-900">
                Alert log
              </div>
              <div className="text-sm text-zinc-500">
                Incidents detected by RFID, manual review, synchronization or
                system checks.
              </div>
            </div>

            <div className="flex flex-col gap-2 sm:flex-row sm:flex-wrap">
              <select
                value={statusFilter}
                onChange={(event) =>
                  setStatusFilter(event.target.value as "all" | AlertStatus)
                }
                className="h-10 rounded-lg border border-zinc-300 bg-white px-3 text-sm text-zinc-900"
              >
                <option value="all">All statuses</option>
                <option value="open">Open</option>
                <option value="acknowledged">Acknowledged</option>
                <option value="resolved">Resolved</option>
                <option value="dismissed">Dismissed</option>
              </select>

              <select
                value={severityFilter}
                onChange={(event) =>
                  setSeverityFilter(
                    event.target.value as "all" | AlertSeverity
                  )
                }
                className="h-10 rounded-lg border border-zinc-300 bg-white px-3 text-sm text-zinc-900"
              >
                <option value="all">All severities</option>
                <option value="critical">Critical</option>
                <option value="warning">Warning</option>
                <option value="info">Info</option>
              </select>

              <select
                value={sourceFilter}
                onChange={(event) => setSourceFilter(event.target.value)}
                className="h-10 rounded-lg border border-zinc-300 bg-white px-3 text-sm text-zinc-900"
              >
                <option value="all">All sources</option>
                {availableSources.map((source) => (
                  <option key={source} value={source}>
                    {source}
                  </option>
                ))}
              </select>

              <Button
                type="button"
                variant="outline"
                onClick={() => void loadAlerts({ silent: true })}
                disabled={refreshing}
              >
                <RefreshCcw
                  className={`mr-1 h-4 w-4 ${refreshing ? "animate-spin" : ""}`}
                />
                Refresh
              </Button>
            </div>
          </div>

          <div className="relative max-h-[750px] overflow-auto bg-white">
            <table className="min-w-[1300px] border-separate border-spacing-0 [table-layout:fixed]">
              <thead>
                <tr>
                  {[
                    "ID",
                    "Alert",
                    "Source",
                    "Severity",
                    "Status",
                    "Entity",
                    "Created",
                    "Resolved",
                    "Actions",
                  ].map((header) => (
                    <th
                      key={header}
                      className="sticky top-0 z-30 whitespace-nowrap border-b border-zinc-200 bg-zinc-50 px-3 py-2 text-left text-sm font-semibold text-zinc-700"
                    >
                      {header}
                    </th>
                  ))}
                </tr>
              </thead>

              <tbody>
                {loading && (
                  <tr>
                    <td
                      colSpan={9}
                      className="px-3 py-8 text-center text-sm text-zinc-500"
                    >
                      Loading alerts...
                    </td>
                  </tr>
                )}

                {error && !loading && (
                  <tr>
                    <td
                      colSpan={9}
                      className="px-3 py-8 text-center text-sm text-red-600"
                    >
                      {error}
                    </td>
                  </tr>
                )}

                {!loading &&
                  !error &&
                  filteredAlerts.map((alert) => (
                    <tr key={alert.id} className="hover:bg-zinc-50">
                      <td className="border-b border-zinc-100 px-3 py-2 text-center text-sm text-zinc-900">
                        <span className="inline-flex w-fit items-center rounded-full bg-blue-900 px-2 py-1 text-xs font-semibold text-white">
                          #{alert.id}
                        </span>
                      </td>

                      <td className="border-b border-zinc-100 px-3 py-2">
                        <div className="font-medium text-zinc-900">
                          {alert.title}
                        </div>
                        <div className="mt-0.5 text-xs font-medium uppercase tracking-wide text-zinc-400">
                          {formatCode(alert.code)}
                        </div>
                        <div className="mt-1 line-clamp-2 text-sm text-zinc-500">
                          {alert.message}
                        </div>
                      </td>

                      <td className="border-b border-zinc-100 px-3 py-2 text-center text-sm text-zinc-900">
                        {alert.source}
                      </td>

                      <td className="border-b border-zinc-100 px-3 py-2 text-center">
                        <span
                          className={`inline-flex rounded-full border px-2 py-1 text-xs font-semibold ${severityClass(
                            alert.severity
                          )}`}
                        >
                          {alert.severity}
                        </span>
                      </td>

                      <td className="border-b border-zinc-100 px-3 py-2 text-center">
                        <span
                          className={`inline-flex rounded-full border px-2 py-1 text-xs font-semibold ${statusClass(
                            alert.status
                          )}`}
                        >
                          {alert.status}
                        </span>
                      </td>

                      <td className="border-b border-zinc-100 px-3 py-2 text-center text-sm text-zinc-900">
                        {formatEntity(alert)}
                      </td>

                      <td className="border-b border-zinc-100 px-3 py-2 text-center text-sm text-zinc-600">
                        {formatDate(alert.createdAt)}
                      </td>

                      <td className="border-b border-zinc-100 px-3 py-2 text-center text-sm text-zinc-600">
                        {formatDate(alert.resolvedAt)}
                      </td>

                      <td className="border-b border-zinc-100 px-3 py-2">
                        <div className="flex justify-center gap-2">
                          <Button type="button" variant="outline">
                            <Eye className="mr-1 h-4 w-4" />
                            View
                          </Button>

                          <Button
                            type="button"
                            variant="outline"
                            disabled={alert.status !== "open"}
                            onClick={() => void acknowledgeAlert(alert.id)}
                          >
                            Acknowledge
                          </Button>

                          <Button
                            type="button"
                            disabled={
                              alert.status === "resolved" ||
                              alert.status === "dismissed"
                            }
                            onClick={() => void resolveAlert(alert.id)}
                          >
                            Resolve
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}

                {!loading && !error && filteredAlerts.length === 0 && (
                  <tr>
                    <td
                      colSpan={9}
                      className="px-3 py-8 text-center text-sm text-zinc-500"
                    >
                      No alerts match the selected filters.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </AppShell>
  );
}