import { useEffect, useMemo, useRef, useState } from "react";
import { apiGet, apiPost } from "../api";
import { AppShell } from "../app/AppShell";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import { Input } from "../ui/Input";

type LocationOut = {
  id: number;
  code: string;
  name: string;
  type: string;
  parent_id?: number | null;
};

type ItemOut = {
  id: number;
  item_code: string;
  name?: string | null;
  description?: string | null;
  category?: string | null;
  uom?: string | null;
  is_serialized: boolean;
  is_active: boolean;
};

type InventoryAsset = {
  type: "asset";
  asset_id: number;
  asset_code: string;
  status?: string | null;
  item?: ItemOut | null;
};

type InventoryContainer = {
  type: "container";
  container_id: number;
  container_code: string;
  quantity?: number | null;
  status?: string | null;
  item?: ItemOut | null;
};

type InventoryStockItem = {
  type: "stock";
  stock_id: number;
  quantity?: number | null;
  item?: ItemOut | null;
};

type InventoryResponse = {
  location: LocationOut;
  summary: {
    assets_expected: number;
    containers_expected: number;
    stock_lines: number;
  };
  assets: InventoryAsset[];
  containers: InventoryContainer[];
  stock_items: InventoryStockItem[];
};

type ValidationSeverity = "success" | "warning" | "error" | "neutral" | string;

type ValidateScanResponse = {
  status: string;
  validation: string;
  severity: ValidationSeverity;
  message: string;
  epc: string;
  object_type?: "asset" | "container" | "item" | string;
  asset_id?: number;
  asset_code?: string;
  asset_status?: string;
  container_id?: number;
  container_code?: string;
  container_status?: string;
  quantity?: number | null;
  item?: ItemOut | null;
  selected_location?: LocationOut | null;
  current_location?: LocationOut | null;
  resolved_key?: string;
  family?: string;
  serial?: number;
  candidates?: string[];
  location?: LocationOut | null;
};

type ScanRecord = ValidateScanResponse & {
  id: string;
  scanned_at: string;
  duplicate_count: number;
};

const DEFAULT_LOCATION_ID = "2457";
const MAX_SCANS = 250;

function nowLabel() {
  return new Date().toLocaleTimeString("es-ES", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

function normalizeEpc(value: string) {
  return value.trim().replace(/\s+/g, "").toUpperCase();
}

function badgeVariant(validation?: string, severity?: ValidationSeverity) {
  if (validation === "duplicate") return "neutral" as const;
  if (severity === "success") return "success" as const;
  if (severity === "warning") return "warning" as const;
  if (severity === "error") return "danger" as const;
  return "neutral" as const;
}

function rowTint(validation?: string, severity?: ValidationSeverity) {
  if (validation === "duplicate") return "bg-blue-50";
  if (severity === "success") return "bg-green-50";
  if (severity === "warning") return "bg-amber-50";
  if (severity === "error") return "bg-red-50";
  return "bg-white";
}

function getScanKey(scan: ValidateScanResponse) {
  if (scan.object_type === "container" && scan.container_id != null) {
    return `container:${scan.container_id}`;
  }

  if (scan.object_type === "asset" && scan.asset_id != null) {
    return `asset:${scan.asset_id}`;
  }

  if (scan.object_type === "item" && scan.item?.id != null) {
    return `item:${scan.item.id}`;
  }

  return null;
}

function isOkValidation(validation: string) {
  return validation === "expected" || validation === "expected_stock_item";
}

function formatQty(value: number | null | undefined, uom?: string | null) {
  if (value == null) return "-";

  const formatted = Number(value).toLocaleString("es-ES", {
    maximumFractionDigits: 3,
  });

  return uom ? `${formatted} ${uom}` : formatted;
}

export default function HandheldInventoryPage() {
  const [locationId, setLocationId] = useState(DEFAULT_LOCATION_ID);
  const [inventory, setInventory] = useState<InventoryResponse | null>(null);

  const [loadingInventory, setLoadingInventory] = useState(false);
  const [validating, setValidating] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const [scanValue, setScanValue] = useState("");
  const [scannerActive, setScannerActive] = useState(false);
  const [scans, setScans] = useState<ScanRecord[]>([]);
  const [lastScan, setLastScan] = useState<ScanRecord | null>(null);

  const scanInputRef = useRef<HTMLInputElement | null>(null);

  function focusScanner() {
    window.setTimeout(() => {
      scanInputRef.current?.focus();
    }, 30);
  }

  useEffect(() => {
    if (scannerActive) {
      focusScanner();
    }
  }, [scannerActive, inventory?.location.id]);

  async function loadInventory() {
    const id = Number(locationId);

    if (!Number.isFinite(id) || id <= 0) {
      setErr("Location ID must be a valid number.");
      return;
    }

    setLoadingInventory(true);
    setErr(null);
    setScannerActive(false);

    try {
      const { data } = await apiGet<InventoryResponse>(
        `/api/locations/${id}/handheld-inventory`
      );

      setInventory(data);
      setScans([]);
      setLastScan(null);
      setScanValue("");
      setScannerActive(true);
    } catch (e: any) {
      setInventory(null);
      setErr(e?.message ?? String(e));
    } finally {
      setLoadingInventory(false);
    }
  }

  async function validateEpc(raw: string) {
    const epc = normalizeEpc(raw);
    setScanValue("");

    if (!epc) {
      focusScanner();
      return;
    }

    if (!inventory?.location?.id) {
      setErr("Load a location before scanning.");
      focusScanner();
      return;
    }

    const existing = scans.find((x) => x.epc === epc);

    if (existing) {
      const duplicate: ScanRecord = {
        ...existing,
        id: existing.id,
        scanned_at: nowLabel(),
        duplicate_count: existing.duplicate_count + 1,
        validation: "duplicate",
        severity: "neutral",
        message: "EPC already scanned in this session",
      };

      setScans((prev) =>
        prev.map((x) =>
          x.epc === epc
            ? {
                ...x,
                duplicate_count: x.duplicate_count + 1,
                scanned_at: duplicate.scanned_at,
              }
            : x
        )
      );

      setLastScan(duplicate);
      focusScanner();
      return;
    }

    setValidating(true);
    setErr(null);

    try {
      const result = await apiPost<ValidateScanResponse>(
        `/api/locations/${inventory.location.id}/handheld-inventory/validate-scan`,
        {
          epc,
          reader_id: "zebra-mc3300r-01",
        }
      );

      const record: ScanRecord = {
        ...result,
        epc,
        id: `${Date.now()}-${epc}`,
        scanned_at: nowLabel(),
        duplicate_count: 0,
      };

      setScans((prev) => [record, ...prev].slice(0, MAX_SCANS));
      setLastScan(record);
    } catch (e: any) {
      const record: ScanRecord = {
        id: `${Date.now()}-${epc}`,
        scanned_at: nowLabel(),
        duplicate_count: 0,
        status: "error",
        validation: "request_error",
        severity: "error",
        message: e?.message ?? String(e),
        epc,
      };

      setScans((prev) => [record, ...prev].slice(0, MAX_SCANS));
      setLastScan(record);
    } finally {
      setValidating(false);
      focusScanner();
    }
  }

  function onScanKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key !== "Enter") return;

    e.preventDefault();
    validateEpc(scanValue);
  }

  function clearSession() {
    setScans([]);
    setLastScan(null);
    setScanValue("");
    focusScanner();
  }

  const scannedKeys = useMemo(() => {
    const keys = new Set<string>();

    for (const scan of scans) {
      if (!isOkValidation(scan.validation)) continue;

      const key = getScanKey(scan);

      if (key) {
        keys.add(key);
      }
    }

    return keys;
  }, [scans]);

  const coveredItemIds = useMemo(() => {
    const ids = new Set<number>();

    for (const scan of scans) {
      if (!isOkValidation(scan.validation)) continue;

      if (scan.item?.id != null) {
        ids.add(scan.item.id);
      }
    }

    return ids;
  }, [scans]);

  const okCount = scans.filter((x) => isOkValidation(x.validation)).length;
  const wrongLocationCount = scans.filter((x) => x.validation === "wrong_location").length;
  const errorCount = scans.filter((x) => x.severity === "error").length;
  const duplicateTotal = scans.reduce((acc, x) => acc + x.duplicate_count, 0);

  const assetRows = inventory?.assets ?? [];
  const containerRows = inventory?.containers ?? [];
  const stockRows = inventory?.stock_items ?? [];

  return (
    <AppShell
      title="Handheld Inventory"
      subtitle="Validate shelf content with Zebra MC3300R / DataWedge"
      actions={
        <div className="flex flex-wrap items-center justify-end gap-2">
          <Button
            variant="outline"
            onClick={() => setScannerActive(false)}
            disabled={!scannerActive}
          >
            Pause scan
          </Button>

          <Button
            variant="primary"
            onClick={() => {
              setScannerActive(true);
              focusScanner();
            }}
            disabled={!inventory}
          >
            Activate scan
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

        <div className="grid gap-4 xl:grid-cols-[420px_1fr]">
          <div className="rounded-xl border border-zinc-200 bg-white p-4 shadow-sm">
            <div className="text-sm font-semibold text-zinc-900">Location</div>

            <div className="mt-1 text-xs text-zinc-500">
              Introduce el ID de la estantería. De momento por ID, porque buscar por
              nombre será el siguiente pequeño circo.
            </div>

            <div className="mt-4 flex gap-2">
              <Input
                value={locationId}
                onFocus={() => setScannerActive(false)}
                onChange={(e) => setLocationId(e.target.value)}
                placeholder="Location ID"
              />

              <Button onClick={loadInventory} disabled={loadingInventory}>
                {loadingInventory ? "Loading…" : "Load"}
              </Button>
            </div>

            {inventory && (
              <div className="mt-4 rounded-xl border border-zinc-200 bg-zinc-50 p-3 text-sm text-zinc-800">
                <div className="font-semibold text-zinc-900">
                  {inventory.location.name}
                </div>

                <div className="mt-1 text-xs text-zinc-500">
                  ID {inventory.location.id} · Code {inventory.location.code} · Type{" "}
                  {inventory.location.type}
                </div>

                <div className="mt-3 grid grid-cols-3 gap-2 text-center">
                  <div className="rounded-lg bg-white p-2">
                    <div className="text-lg font-bold">
                      {inventory.summary.assets_expected}
                    </div>
                    <div className="text-[11px] text-zinc-500">Assets</div>
                  </div>

                  <div className="rounded-lg bg-white p-2">
                    <div className="text-lg font-bold">
                      {inventory.summary.containers_expected}
                    </div>
                    <div className="text-[11px] text-zinc-500">Containers</div>
                  </div>

                  <div className="rounded-lg bg-white p-2">
                    <div className="text-lg font-bold">
                      {inventory.summary.stock_lines}
                    </div>
                    <div className="text-[11px] text-zinc-500">Stock lines</div>
                  </div>
                </div>
              </div>
            )}
          </div>

          <div className="rounded-xl border border-zinc-200 bg-white p-4 shadow-sm">
            <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
              <div>
                <div className="text-sm font-semibold text-zinc-900">
                  Scanner session
                </div>

                <div className="mt-1 text-xs text-zinc-500">
                  DataWedge debe enviar el EPC como teclado y terminar con ENTER. El
                  input está oculto pero enfocado, una trampa elegante para Android.
                </div>
              </div>

              <div className="flex flex-wrap gap-2">
                <Badge variant={scannerActive ? "success" : "warning"}>
                  {scannerActive ? "Scanner active" : "Scanner paused"}
                </Badge>

                {validating && <Badge variant="neutral">Validating…</Badge>}
              </div>
            </div>

            <input
              ref={scanInputRef}
              value={scanValue}
              onChange={(e) => setScanValue(e.target.value)}
              onKeyDown={onScanKeyDown}
              onBlur={() => {
                if (scannerActive) focusScanner();
              }}
              autoComplete="off"
              className="absolute h-px w-px opacity-0"
              aria-label="RFID scan capture"
              disabled={!scannerActive || !inventory}
            />

            <div className="mt-4 grid gap-2 sm:grid-cols-5">
              <div className="rounded-xl border border-zinc-200 bg-zinc-50 p-3">
                <div className="text-xl font-bold text-zinc-900">{scans.length}</div>
                <div className="text-xs text-zinc-500">Unique scans</div>
              </div>

              <div className="rounded-xl border border-green-200 bg-green-50 p-3">
                <div className="text-xl font-bold text-green-700">{okCount}</div>
                <div className="text-xs text-green-700">OK</div>
              </div>

              <div className="rounded-xl border border-amber-200 bg-amber-50 p-3">
                <div className="text-xl font-bold text-amber-700">
                  {wrongLocationCount}
                </div>
                <div className="text-xs text-amber-700">Wrong location</div>
              </div>

              <div className="rounded-xl border border-red-200 bg-red-50 p-3">
                <div className="text-xl font-bold text-red-700">{errorCount}</div>
                <div className="text-xs text-red-700">Errors</div>
              </div>

              <div className="rounded-xl border border-blue-200 bg-blue-50 p-3">
                <div className="text-xl font-bold text-blue-700">
                  {duplicateTotal}
                </div>
                <div className="text-xs text-blue-700">Duplicates</div>
              </div>
            </div>

            {lastScan && (
              <div
                className={`mt-4 rounded-xl border border-zinc-200 p-4 ${rowTint(
                  lastScan.validation,
                  lastScan.severity
                )}`}
              >
                <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                  <div className="min-w-0">
                    <div className="truncate font-mono text-sm font-semibold text-zinc-900">
                      {lastScan.epc}
                    </div>

                    <div className="mt-1 text-sm text-zinc-700">
                      {lastScan.message}
                    </div>
                  </div>

                  <Badge
                    variant={badgeVariant(lastScan.validation, lastScan.severity)}
                  >
                    {lastScan.validation}
                  </Badge>
                </div>
              </div>
            )}

            <div className="mt-4 flex justify-end">
              <Button
                variant="outline"
                onClick={clearSession}
                disabled={scans.length === 0}
              >
                Clear session
              </Button>
            </div>
          </div>
        </div>

        <div className="grid gap-4 xl:grid-cols-2">
          <div className="rounded-xl border border-zinc-200 bg-white shadow-sm">
            <div className="border-b border-zinc-200 px-4 py-3">
              <div className="text-sm font-semibold text-zinc-900">
                Expected content
              </div>

              <div className="mt-1 text-xs text-zinc-500">
                Assets, containers and stock lines registered in this location.
              </div>
            </div>

            <div className="max-h-[520px] overflow-auto">
              <table className="min-w-full border-separate border-spacing-0">
                <thead>
                  <tr>
                    {["Type", "Code", "Item", "Qty", "Status"].map((h) => (
                      <th
                        key={h}
                        className="sticky top-0 border-b border-zinc-200 bg-zinc-50 px-3 py-2 text-left text-xs font-semibold text-zinc-700"
                      >
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>

                <tbody>
                  {assetRows.map((a) => {
                    const covered = scannedKeys.has(`asset:${a.asset_id}`);

                    return (
                      <tr
                        key={`asset-${a.asset_id}`}
                        className={covered ? "bg-green-50" : "hover:bg-zinc-50"}
                      >
                        <td className="border-b border-zinc-100 px-3 py-2 text-sm">
                          Asset
                        </td>
                        <td className="border-b border-zinc-100 px-3 py-2 font-mono text-xs">
                          {a.asset_code}
                        </td>
                        <td className="border-b border-zinc-100 px-3 py-2 text-sm">
                          {a.item?.item_code ?? "-"}
                        </td>
                        <td className="border-b border-zinc-100 px-3 py-2 text-sm">
                          1
                        </td>
                        <td className="border-b border-zinc-100 px-3 py-2 text-sm">
                          <Badge variant={covered ? "success" : "neutral"}>
                            {covered ? "scanned" : a.status ?? "pending"}
                          </Badge>
                        </td>
                      </tr>
                    );
                  })}

                  {containerRows.map((c) => {
                    const covered = scannedKeys.has(`container:${c.container_id}`);

                    return (
                      <tr
                        key={`container-${c.container_id}`}
                        className={covered ? "bg-green-50" : "hover:bg-zinc-50"}
                      >
                        <td className="border-b border-zinc-100 px-3 py-2 text-sm">
                          Container
                        </td>
                        <td className="border-b border-zinc-100 px-3 py-2 font-mono text-xs">
                          {c.container_code}
                        </td>
                        <td className="border-b border-zinc-100 px-3 py-2 text-sm">
                          {c.item?.item_code ?? "-"}
                        </td>
                        <td className="border-b border-zinc-100 px-3 py-2 text-sm">
                          {formatQty(c.quantity, c.item?.uom)}
                        </td>
                        <td className="border-b border-zinc-100 px-3 py-2 text-sm">
                          <Badge variant={covered ? "success" : "neutral"}>
                            {covered ? "scanned" : c.status ?? "pending"}
                          </Badge>
                        </td>
                      </tr>
                    );
                  })}

                  {stockRows.map((s) => {
                    const covered =
                      s.item?.id != null ? coveredItemIds.has(s.item.id) : false;

                    return (
                      <tr
                        key={`stock-${s.stock_id}`}
                        className={covered ? "bg-green-50" : "hover:bg-zinc-50"}
                      >
                        <td className="border-b border-zinc-100 px-3 py-2 text-sm">
                          Stock
                        </td>
                        <td className="border-b border-zinc-100 px-3 py-2 font-mono text-xs">
                          #{s.stock_id}
                        </td>
                        <td className="border-b border-zinc-100 px-3 py-2 text-sm">
                          {s.item?.item_code ?? "-"}
                        </td>
                        <td className="border-b border-zinc-100 px-3 py-2 text-sm">
                          {formatQty(s.quantity, s.item?.uom)}
                        </td>
                        <td className="border-b border-zinc-100 px-3 py-2 text-sm">
                          <Badge variant={covered ? "success" : "neutral"}>
                            {covered ? "checked" : "pending"}
                          </Badge>
                        </td>
                      </tr>
                    );
                  })}

                  {inventory &&
                    assetRows.length === 0 &&
                    containerRows.length === 0 &&
                    stockRows.length === 0 && (
                      <tr>
                        <td
                          colSpan={5}
                          className="px-3 py-8 text-sm text-zinc-500"
                        >
                          No expected content for this location.
                        </td>
                      </tr>
                    )}

                  {!inventory && (
                    <tr>
                      <td colSpan={5} className="px-3 py-8 text-sm text-zinc-500">
                        Load a location to start.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          <div className="rounded-xl border border-zinc-200 bg-white shadow-sm">
            <div className="border-b border-zinc-200 px-4 py-3">
              <div className="text-sm font-semibold text-zinc-900">Scan log</div>
              <div className="mt-1 text-xs text-zinc-500">Latest reads first.</div>
            </div>

            <div className="max-h-[520px] overflow-auto">
              <table className="min-w-full border-separate border-spacing-0">
                <thead>
                  <tr>
                    {["Time", "EPC", "Validation", "Object", "Message"].map((h) => (
                      <th
                        key={h}
                        className="sticky top-0 border-b border-zinc-200 bg-zinc-50 px-3 py-2 text-left text-xs font-semibold text-zinc-700"
                      >
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>

                <tbody>
                  {scans.map((s) => (
                    <tr
                      key={s.id}
                      className={`${rowTint(
                        s.validation,
                        s.severity
                      )} hover:brightness-[0.98]`}
                    >
                      <td className="border-b border-zinc-100 px-3 py-2 text-xs text-zinc-600">
                        {s.scanned_at}
                      </td>
                      <td
                        className="max-w-[220px] truncate border-b border-zinc-100 px-3 py-2 font-mono text-xs"
                        title={s.epc}
                      >
                        {s.epc}
                      </td>
                      <td className="border-b border-zinc-100 px-3 py-2 text-sm">
                        <div className="flex items-center gap-2">
                          <Badge variant={badgeVariant(s.validation, s.severity)}>
                            {s.validation}
                          </Badge>

                          {s.duplicate_count > 0 && (
                            <span className="text-xs text-blue-700">
                              +{s.duplicate_count}
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="border-b border-zinc-100 px-3 py-2 text-xs text-zinc-700">
                        {s.object_type ?? "-"}
                        {s.item?.item_code ? (
                          <div className="text-zinc-500">{s.item.item_code}</div>
                        ) : null}
                      </td>
                      <td className="border-b border-zinc-100 px-3 py-2 text-sm text-zinc-700">
                        {s.message}
                      </td>
                    </tr>
                  ))}

                  {scans.length === 0 && (
                    <tr>
                      <td colSpan={5} className="px-3 py-8 text-sm text-zinc-500">
                        No scans yet. Load a location and press the Zebra trigger.
                        Humanity has come this far.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}