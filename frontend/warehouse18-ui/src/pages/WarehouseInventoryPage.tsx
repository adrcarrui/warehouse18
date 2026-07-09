import { useEffect, useMemo, useState } from "react";
import { Search, RefreshCw, PackageSearch } from "lucide-react";

import { apiGet } from "../api";
import type { PageOut } from "../api";
import { AppShell } from "../app/AppShell";
import { Button } from "../ui/Button";
import { Input } from "../ui/Input";

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

type InventoryPartOut = {
  source_type: "serialized" | "stock" | string;

  item_id: number;
  item_code: string;

  asset_id?: number | null;
  asset_code?: string | null;

  quantity: string | number;

  location_id: number;
  location_code: string;
  location_name: string;

  rack_code?: string | null;
  shelf_code?: string | null;
  aisle_id?: number | null;
};

type AisleWarehousePartsOut = {
  aisle_id: number;
  aisle_code: string;
  aisle_name: string;
  device_group_code?: string | null;
  matched_prefixes: string[];
  parts: InventoryPartOut[];
};

type DeviceGroupWarehousePartsOut = {
  device_group_id: number;
  device_group_code: string;
  matched_prefixes: string[];
  parts: InventoryPartOut[];
};

type InventoryResult =
  | {
      scope_type: "aisle";
      title: string;
      matched_prefixes: string[];
      parts: InventoryPartOut[];
    }
  | {
      scope_type: "device_group";
      title: string;
      matched_prefixes: string[];
      parts: InventoryPartOut[];
    };

const DEVICE_GROUP_CODES = [
  "CN235",
  "C295",
  "A400M",
  "A400",
  "MRTT",
  "ITC",
  "CHT",
  "DARPT",
];

const fieldInputClassName =
  "h-10 w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900 shadow-none outline-none focus:border-zinc-500 focus:ring-0 disabled:bg-zinc-100 disabled:text-zinc-400";

function safeStr(value: unknown): string {
  return value == null ? "" : String(value);
}

function normalizeSearchText(value: string): string {
  return value
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .trim();
}

function formatQuantity(value: string | number): string {
  const n = Number(value);

  if (!Number.isFinite(n)) {
    return String(value);
  }

  if (Number.isInteger(n)) {
    return String(n);
  }

  return n.toFixed(2);
}

function sourceTypeLabel(sourceType: string): string {
  if (sourceType === "serialized") return "Serialized";
  if (sourceType === "stock") return "Stock";
  return sourceType;
}

function sourceTypeClassName(sourceType: string): string {
  if (sourceType === "serialized") {
    return "bg-blue-50 text-blue-700 ring-blue-200";
  }

  if (sourceType === "stock") {
    return "bg-emerald-50 text-emerald-700 ring-emerald-200";
  }

  return "bg-zinc-50 text-zinc-700 ring-zinc-200";
}

function aisleLabel(aisleId: number): string {
  return `AISLE${aisleId}`;
}

function locationSearchText(loc: LocationOut): string {
  return normalizeSearchText(
    [
      loc.name,
      loc.code,
      loc.rack_code,
      loc.shelf_code,
      loc.aisle_id == null ? "" : aisleLabel(loc.aisle_id),
    ]
      .filter(Boolean)
      .join(" ")
  );
}

export default function WarehouseInventoryPage() {
  const [locationMap, setLocationMap] = useState<Record<number, LocationOut>>({});
  const [selectedAisleId, setSelectedAisleId] = useState("");
  const [selectedDeviceGroupCode, setSelectedDeviceGroupCode] = useState("");
  const [result, setResult] = useState<InventoryResult | null>(null);

  const [searchText, setSearchText] = useState("");
  const [loadingLocations, setLoadingLocations] = useState(false);
  const [loadingInventory, setLoadingInventory] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const aisleOptions = useMemo(() => {
    const byAisle = new Map<
      number,
      {
        aisle_id: number;
        label: string;
        location_count: number;
      }
    >();

    for (const loc of Object.values(locationMap)) {
      if (
        loc.aisle_id == null ||
        loc.is_active === false ||
        loc.is_warehouse_location !== true
      ) {
        continue;
      }

      const current = byAisle.get(loc.aisle_id);

      if (current) {
        current.location_count += 1;
      } else {
        byAisle.set(loc.aisle_id, {
          aisle_id: loc.aisle_id,
          label: aisleLabel(loc.aisle_id),
          location_count: 1,
        });
      }
    }

    return Array.from(byAisle.values()).sort((a, b) => a.aisle_id - b.aisle_id);
  }, [locationMap]);

  const filteredParts = useMemo(() => {
    const query = normalizeSearchText(searchText);

    const parts = result?.parts ?? [];

    if (!query) {
      return parts;
    }

    return parts.filter((part) =>
      normalizeSearchText(
        [
          part.item_code,
          part.asset_code,
          part.location_name,
          part.location_code,
          part.rack_code,
          part.shelf_code,
          part.aisle_id == null ? "" : aisleLabel(part.aisle_id),
          part.source_type,
        ]
          .filter(Boolean)
          .join(" ")
      ).includes(query)
    );
  }, [result, searchText]);

  const stats = useMemo(() => {
    const parts = result?.parts ?? [];

    const totalRows = parts.length;
    const serializedRows = parts.filter((p) => p.source_type === "serialized").length;
    const stockRows = parts.filter((p) => p.source_type === "stock").length;

    const totalQuantity = parts.reduce((acc, part) => {
      const n = Number(part.quantity);
      return acc + (Number.isFinite(n) ? n : 0);
    }, 0);

    const locationCount = new Set(parts.map((p) => p.location_id)).size;
    const itemCount = new Set(parts.map((p) => p.item_code)).size;

    return {
      totalRows,
      serializedRows,
      stockRows,
      totalQuantity,
      locationCount,
      itemCount,
    };
  }, [result]);

  async function loadLocationMap() {
    setLoadingLocations(true);
    setErr(null);

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
    } catch (e: any) {
      setErr(e?.message ?? String(e));
      setLocationMap({});
    } finally {
      setLoadingLocations(false);
    }
  }

  async function loadInventory() {
    setLoadingInventory(true);
    setErr(null);

    try {
      const aisleId = selectedAisleId.trim();
      const deviceGroupCode = selectedDeviceGroupCode.trim();

      if (!aisleId && !deviceGroupCode) {
        throw new Error("Select an aisle or a device group before searching");
      }

      if (aisleId) {
        const params: Record<string, string> = {};

        if (deviceGroupCode) {
          params.device_group_code = deviceGroupCode;
        }

        const { data } = await apiGet<AisleWarehousePartsOut>(
          `/api/inventory/aisles/${aisleId}/warehouse-parts`,
          params
        );

        setResult({
          scope_type: "aisle",
          title: deviceGroupCode
            ? `${data.aisle_code} · ${data.device_group_code}`
            : data.aisle_code,
          matched_prefixes: data.matched_prefixes ?? [],
          parts: data.parts ?? [],
        });

        return;
      }

      const { data } = await apiGet<DeviceGroupWarehousePartsOut>(
        `/api/inventory/device-groups/${deviceGroupCode}/warehouse-parts`
      );

      setResult({
        scope_type: "device_group",
        title: data.device_group_code,
        matched_prefixes: data.matched_prefixes ?? [],
        parts: data.parts ?? [],
      });
    } catch (e: any) {
      setErr(e?.message ?? String(e));
      setResult(null);
    } finally {
      setLoadingInventory(false);
    }
  }

  useEffect(() => {
    void loadLocationMap();
  }, []);

  return (
    <AppShell
      title="Warehouse Inventory"
      subtitle="Visualize parts currently stored in Warehouse18 by aisle or device family"
    >
      <div className="space-y-6">
        {err && (
          <div className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            Error: {err}
          </div>
        )}

        <div className="rounded-xl border border-zinc-200 bg-white">
          <div className="border-b border-zinc-200 px-4 py-3">
            <div className="text-sm font-semibold text-zinc-900">
              Inventory filters
            </div>
            <div className="mt-1 text-xs text-zinc-500">
              Select an aisle, a device family, or both. When both are selected, the
              result is limited to that family inside the aisle.
            </div>
          </div>

          <div className="grid gap-3 p-4 lg:grid-cols-[1fr_1fr_auto]">
            <div>
              <label className="mb-1 block text-xs font-semibold text-zinc-600">
                Aisle
              </label>

              <select
                value={selectedAisleId}
                onChange={(e) => setSelectedAisleId(e.target.value)}
                disabled={loadingLocations}
                className={fieldInputClassName}
              >
                <option value="">All aisles</option>

                {aisleOptions.map((aisle) => (
                  <option key={aisle.aisle_id} value={aisle.aisle_id}>
                    {aisle.label} · {aisle.location_count} locations
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="mb-1 block text-xs font-semibold text-zinc-600">
                Device family
              </label>

              <select
                value={selectedDeviceGroupCode}
                onChange={(e) => setSelectedDeviceGroupCode(e.target.value)}
                className={fieldInputClassName}
              >
                <option value="">All families</option>

                {DEVICE_GROUP_CODES.map((code) => (
                  <option key={code} value={code}>
                    {code}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex items-end">
              <Button
                onClick={() => void loadInventory()}
                disabled={loadingInventory || loadingLocations}
                className="h-10"
              >
                <RefreshCw className="mr-2 h-4 w-4" />
                {loadingInventory ? "Loading..." : "Search"}
              </Button>
            </div>
          </div>
        </div>

        <div className="grid gap-3 md:grid-cols-5">
          <div className="rounded-xl border border-zinc-200 bg-zinc-50 p-3">
            <div className="text-[11px] font-semibold uppercase tracking-wide text-zinc-500">
              Rows
            </div>
            <div className="mt-1 text-2xl font-semibold text-zinc-950">
              {stats.totalRows}
            </div>
          </div>

          <div className="rounded-xl border border-zinc-200 bg-zinc-50 p-3">
            <div className="text-[11px] font-semibold uppercase tracking-wide text-zinc-500">
              Items
            </div>
            <div className="mt-1 text-2xl font-semibold text-zinc-950">
              {stats.itemCount}
            </div>
          </div>

          <div className="rounded-xl border border-zinc-200 bg-zinc-50 p-3">
            <div className="text-[11px] font-semibold uppercase tracking-wide text-zinc-500">
              Locations
            </div>
            <div className="mt-1 text-2xl font-semibold text-zinc-950">
              {stats.locationCount}
            </div>
          </div>

          <div className="rounded-xl border border-zinc-200 bg-zinc-50 p-3">
            <div className="text-[11px] font-semibold uppercase tracking-wide text-zinc-500">
              Serialized
            </div>
            <div className="mt-1 text-2xl font-semibold text-blue-700">
              {stats.serializedRows}
            </div>
          </div>

          <div className="rounded-xl border border-zinc-200 bg-zinc-50 p-3">
            <div className="text-[11px] font-semibold uppercase tracking-wide text-zinc-500">
              Total qty
            </div>
            <div className="mt-1 text-2xl font-semibold text-zinc-950">
              {formatQuantity(stats.totalQuantity)}
            </div>
          </div>
        </div>

        <div className="rounded-xl border border-zinc-200 bg-white">
          <div className="flex flex-col gap-3 border-b border-zinc-200 px-4 py-3 md:flex-row md:items-center md:justify-between">
            <div>
              <div className="flex items-center gap-2 text-sm font-semibold text-zinc-900">
                <PackageSearch className="h-4 w-4" />
                Inventory result
                {result?.title ? (
                  <span className="rounded-full bg-zinc-100 px-2 py-0.5 text-xs font-semibold text-zinc-700">
                    {result.title}
                  </span>
                ) : null}
              </div>

              <div className="mt-1 text-xs text-zinc-500">
                {result
                  ? `${filteredParts.length} visible rows from ${result.parts.length} total rows`
                  : "No search performed yet"}
                {result?.matched_prefixes?.length ? (
                  <>
                    {" "}
                    · Prefixes:{" "}
                    <span className="font-medium">
                      {result.matched_prefixes.join(", ")}
                    </span>
                  </>
                ) : null}
              </div>
            </div>

            <div className="relative w-full md:w-80">
              <Search className="pointer-events-none absolute left-3 top-3 h-4 w-4 text-zinc-400" />
              <Input
                value={searchText}
                onChange={(e) => setSearchText(e.target.value)}
                placeholder="Filter item, asset, location..."
                className="h-10 w-full rounded-lg border border-zinc-300 bg-white px-9 py-2 text-sm text-zinc-900 shadow-none outline-none focus:border-zinc-500 focus:ring-0"
              />
            </div>
          </div>

          <div className="overflow-auto">
            <table className="min-w-full border-separate border-spacing-0">
              <thead className="bg-zinc-50">
                <tr>
                  {[
                    "Type",
                    "Item",
                    "Asset",
                    "Qty",
                    "Location",
                    "Aisle",
                  ].map((header) => (
                    <th
                      key={header}
                      className="border-b border-zinc-200 px-3 py-2 text-left text-xs font-semibold text-zinc-700"
                    >
                      {header}
                    </th>
                  ))}
                </tr>
              </thead>

              <tbody>
                {filteredParts.map((part, index) => (
                  <tr
                    key={`${part.source_type}-${part.item_id}-${part.asset_id ?? "stock"}-${part.location_id}-${index}`}
                    className="hover:bg-zinc-50"
                  >
                    <td className="border-b border-zinc-100 px-3 py-2 text-sm">
                      <span
                        className={`inline-flex rounded-full px-2 py-0.5 text-xs font-semibold ring-1 ${sourceTypeClassName(
                          part.source_type
                        )}`}
                      >
                        {sourceTypeLabel(part.source_type)}
                      </span>
                    </td>

                    <td className="border-b border-zinc-100 px-3 py-2 text-sm font-semibold text-zinc-950">
                      {part.item_code}
                    </td>

                    <td className="border-b border-zinc-100 px-3 py-2 text-sm text-zinc-700">
                      {part.asset_code || "—"}
                    </td>

                    <td className="border-b border-zinc-100 px-3 py-2 text-sm font-medium text-zinc-900">
                      {formatQuantity(part.quantity)}
                    </td>

                    <td className="border-b border-zinc-100 px-3 py-2 text-sm text-zinc-700">
                      {part.location_name}
                    </td>

                    <td className="border-b border-zinc-100 px-3 py-2 text-sm text-zinc-700">
                      {part.aisle_id == null ? "—" : aisleLabel(part.aisle_id)}
                    </td>
                  </tr>
                ))}

                {!loadingInventory && result && filteredParts.length === 0 && (
                  <tr>
                    <td
                      colSpan={8}
                      className="px-4 py-8 text-center text-sm text-zinc-500"
                    >
                      No parts match the current filter.
                    </td>
                  </tr>
                )}

                {!loadingInventory && !result && (
                  <tr>
                    <td
                      colSpan={8}
                      className="px-4 py-8 text-center text-sm text-zinc-500"
                    >
                      Select filters and press Search to load warehouse inventory.
                    </td>
                  </tr>
                )}

                {loadingInventory && (
                  <tr>
                    <td
                      colSpan={8}
                      className="px-4 py-8 text-center text-sm text-zinc-500"
                    >
                      Loading inventory...
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