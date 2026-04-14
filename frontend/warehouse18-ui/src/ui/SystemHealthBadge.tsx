import { useEffect, useMemo, useState } from "react";
import { Badge } from "./Badge";

type HealthSection = {
  ok: boolean;
  latency_ms?: number;
  error?: string;
  rows?: number;
};

type IntegrationsHealthResponse = {
  status: "ok" | "degraded" | "down";
  backend: { ok: boolean };
  database: HealthSection;
  mysim: HealthSection;
};

function statusVariant(
  status: string
): "neutral" | "success" | "warning" | "danger" {
  switch (status) {
    case "ok":
      return "success";
    case "degraded":
      return "warning";
    case "down":
      return "danger";
    default:
      return "neutral";
  }
}

function statusLabel(status: string) {
  switch (status) {
    case "ok":
      return "System OK";
    case "degraded":
      return "System degraded";
    case "down":
      return "System down";
    default:
      return "System unknown";
  }
}

function sectionLabel(ok?: boolean) {
  if (ok === true) return "OK";
  if (ok === false) return "ERR";
  return "--";
}

export function SystemHealthBadge(props: { collapsed?: boolean }) {
  const { collapsed = false } = props;

  const [data, setData] = useState<IntegrationsHealthResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState<string | null>(null);

  async function loadHealth() {
    try {
      const res = await fetch("/api/integrations/health", {
        headers: { Accept: "application/json" },
      });

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }

      const json = (await res.json()) as IntegrationsHealthResponse;
      setData(json);
      setFetchError(null);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Unknown frontend error";
      setFetchError(message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadHealth();

    const id = window.setInterval(() => {
      loadHealth();
    }, 30*60*1000); // every 30 minutes

    return () => window.clearInterval(id);
  }, []);

  const globalStatus = useMemo(() => {
    if (fetchError) return "down";
    return data?.status ?? "unknown";
  }, [data, fetchError]);

  const variant = statusVariant(globalStatus);
  const label = statusLabel(globalStatus);

  if (collapsed) {
    return (
      <div
        className="flex items-center justify-center"
        title={
          fetchError
            ? `Health error: ${fetchError}`
            : `DB: ${sectionLabel(data?.database?.ok)} | mySim: ${sectionLabel(
                data?.mysim?.ok
              )}`
        }
      >
        <Badge variant={variant}>{label}</Badge>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/30 p-3">
      <div className="flex items-center justify-between gap-2">
        <div className="text-xs font-semibold text-slate-200">
          Connection status
        </div>
        <Badge variant={variant}>{loading ? "Checking..." : label}</Badge>
      </div>

      <div className="mt-3 space-y-1 text-[11px] text-slate-400">
        <div className="flex items-center justify-between gap-2">
          <span>Backend</span>
          <span className="text-slate-200">OK</span>
        </div>

        <div className="flex items-center justify-between gap-2">
          <span>DB</span>
          <span className="text-slate-200">
            {sectionLabel(data?.database?.ok)}
          </span>
        </div>

        <div className="flex items-center justify-between gap-2">
          <span>mySim</span>
          <span className="text-slate-200">
            {sectionLabel(data?.mysim?.ok)}
          </span>
        </div>

        {typeof data?.mysim?.latency_ms === "number" ? (
          <div className="flex items-center justify-between gap-2">
            <span>mySim latency</span>
            <span className="text-slate-200">{data.mysim.latency_ms} ms</span>
          </div>
        ) : null}

        {fetchError ? (
          <div className="pt-1 text-red-400 break-words">
            Error: {fetchError}
          </div>
        ) : null}

        {!fetchError && data?.mysim?.error ? (
          <div className="pt-1 text-amber-400 break-words">
            mySim: {data.mysim.error}
          </div>
        ) : null}

        {!fetchError && data?.database?.error ? (
          <div className="pt-1 text-amber-400 break-words">
            DB: {data.database.error}
          </div>
        ) : null}
      </div>
    </div>
  );
}