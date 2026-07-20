import { useEffect, useMemo, useState } from "react";
import {
  ArrowDown,
  ArrowUp,
  ArrowUpDown,
  Download,
  Search,
  RefreshCw,
  PackageSearch,
} from "lucide-react";

import { apiGet } from "../api";
import type { PageOut } from "../api";
import { AppShell } from "../app/AppShell";
import { Button } from "../ui/Button";
import { Input } from "../ui/Input";
import { jsPDF } from "jspdf";
import { autoTable } from "jspdf-autotable";

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

type SortField = "location" | "aisle";
type SortDirection = "asc" | "desc";

type SortState = {
  field: SortField;
  direction: SortDirection;
} | null;

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

const inventoryCollator = new Intl.Collator(undefined, {
  numeric: true,
  sensitivity: "base",
});

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

function sanitizeFileName(value: string): string {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-zA-Z0-9_-]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .toLowerCase();
}

function formatPdfDate(value: Date): string {
  const year = value.getFullYear();
  const month = String(value.getMonth() + 1).padStart(2, "0");
  const day = String(value.getDate()).padStart(2, "0");
  const hours = String(value.getHours()).padStart(2, "0");
  const minutes = String(value.getMinutes()).padStart(2, "0");

  return `${year}-${month}-${day}_${hours}-${minutes}`;
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
  const [sortState, setSortState] = useState<SortState>(null);
  const [exportingPdf, setExportingPdf] = useState(false);

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
          part.location_name,
          part.location_code,
          part.rack_code,
          part.shelf_code,
          part.aisle_id == null ? "" : aisleLabel(part.aisle_id),
        ]
          .filter(Boolean)
          .join(" ")
      ).includes(query)
    );
  }, [result, searchText]);

  const visibleParts = useMemo(() => {
    if (!sortState) {
      return filteredParts;
    }

    return filteredParts
      .map((part, originalIndex) => ({ part, originalIndex }))
      .sort((left, right) => {
        const leftPart = left.part;
        const rightPart = right.part;
        let comparison = 0;

        if (sortState.field === "location") {
          const leftLocation = leftPart.location_name || leftPart.location_code || "";
          const rightLocation = rightPart.location_name || rightPart.location_code || "";
          comparison = inventoryCollator.compare(leftLocation, rightLocation);
        } else {
          const leftAisle = leftPart.aisle_id;
          const rightAisle = rightPart.aisle_id;

          if (leftAisle == null && rightAisle == null) {
            comparison = 0;
          } else if (leftAisle == null) {
            return 1;
          } else if (rightAisle == null) {
            return -1;
          } else {
            comparison = leftAisle - rightAisle;
          }
        }

        if (comparison === 0) {
          return left.originalIndex - right.originalIndex;
        }

        return sortState.direction === "asc" ? comparison : -comparison;
      })
      .map(({ part }) => part);
  }, [filteredParts, sortState]);

  function cycleSort(field: SortField) {
    setSortState((current) => {
      if (!current || current.field !== field) {
        return { field, direction: "asc" };
      }

      if (current.direction === "asc") {
        return { field, direction: "desc" };
      }

      return null;
    });
  }

  function sortIcon(field: SortField) {
    if (sortState?.field !== field) {
      return <ArrowUpDown className="h-3.5 w-3.5 text-blue-200" />;
    }

    return sortState.direction === "asc" ? (
      <ArrowUp className="h-3.5 w-3.5" />
    ) : (
      <ArrowDown className="h-3.5 w-3.5" />
    );
  }


  function downloadInventoryPdf() {
    if (!result || visibleParts.length === 0) {
      return;
    }

    setExportingPdf(true);

    try {
      const document = new jsPDF({
        orientation: "portrait",
        unit: "mm",
        format: "a4",
      });

      const generatedAt = new Date();
      const resultTitle = result.title || "Warehouse inventory";

      document.setFontSize(18);
      document.text("Warehouse Inventory", 14, 18);

      document.setFontSize(9);
      document.text(
        `Generated: ${generatedAt.toLocaleString("en-GB")}`,
        14,
        27
      );

      if (searchText.trim()) {
        document.text(`Filter: ${searchText.trim()}`, 14, 33);
      }

      const tableStartY = searchText.trim() ? 40 : 34;

      autoTable(document, {
        startY: tableStartY,
        head: [["Item", "Qty", "Location", "Aisle"]],
        body: visibleParts.map((part) => [
          part.item_code,
          formatQuantity(part.quantity),
          part.location_name || part.location_code || "—",
          part.aisle_id == null ? "—" : aisleLabel(part.aisle_id),
        ]),
        theme: "grid",
        styles: {
          fontSize: 8.5,
          cellPadding: 2.4,
          lineColor: [226, 232, 240],
          lineWidth: 0.2,
          textColor: [71, 85, 105],
          valign: "middle",
        },
        headStyles: {
          fillColor: [23, 37, 84],
          textColor: [255, 255, 255],
          fontStyle: "bold",
        },
        alternateRowStyles: {
          fillColor: [248, 250, 252],
        },
        columnStyles: {
          0: { cellWidth: 42, textColor: [15, 23, 42], fontStyle: "bold" },
          1: { cellWidth: 22, halign: "center" },
          2: { cellWidth: "auto" },
          3: { cellWidth: 28, halign: "center" },
        },
        margin: {
          left: 14,
          right: 14,
          bottom: 14,
        },
        didDrawPage: (data) => {
          document.setFontSize(8);
          document.setTextColor(100);
          document.text(
            `Page ${data.pageNumber}`,
            document.internal.pageSize.getWidth() - 14,
            document.internal.pageSize.getHeight() - 7,
            { align: "right" }
          );
        },
      });

      const safeTitle = sanitizeFileName(resultTitle) || "warehouse-inventory";

      document.save(
        `warehouse-inventory-${safeTitle}-${formatPdfDate(generatedAt)}.pdf`
      );
    } finally {
      setExportingPdf(false);
    }
  }

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
    setSortState(null);

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

        <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
          <div className="flex flex-col gap-3 border-b border-slate-200 px-4 py-3 lg:flex-row lg:items-center lg:justify-between">
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2 text-sm font-semibold text-slate-900">
                <PackageSearch className="h-4 w-4" />
                Inventory result
                {result?.title ? (
                  <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-semibold text-slate-700">
                    {result.title}
                  </span>
                ) : null}
              </div>

              <div className="mt-1 text-xs text-slate-500">
                {result
                  ? `${visibleParts.length} visible rows from ${result.parts.length} total rows`
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

            <div className="flex w-full flex-col gap-2 sm:flex-row lg:w-auto">
              <div className="relative w-full sm:w-80">
                <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                <Input
                  value={searchText}
                  onChange={(e) => setSearchText(e.target.value)}
                  placeholder="Filter item, location, aisle..."
                  className="h-9 w-full rounded-xl border border-slate-200 bg-slate-50 pl-9 pr-3 text-xs text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-blue-400 focus:bg-white focus:ring-2 focus:ring-blue-100"
                />
              </div>

              <Button
                onClick={downloadInventoryPdf}
                disabled={!result || visibleParts.length === 0 || exportingPdf}
                className="h-9 shrink-0 bg-blue-950 px-3 text-white hover:bg-blue-900 disabled:cursor-not-allowed disabled:opacity-50"
              >
                <Download className="mr-2 h-4 w-4" />
                {exportingPdf ? "Exporting..." : "Export PDF"}
              </Button>
            </div>
          </div>

          <div className="m-4 max-h-[560px] overflow-auto rounded-xl border border-slate-200">
            <table className="w-full min-w-[640px] table-fixed text-xs">
              <colgroup>
                <col className="w-[190px]" />
                <col className="w-[80px]" />
                <col className="w-[270px]" />
                <col className="w-[100px]" />
              </colgroup>

              <thead className="sticky top-0 z-10 bg-blue-950">
                <tr className="text-left text-white">
                  <th className="px-3 py-2.5 font-semibold">
                    Item
                  </th>
                  <th className="px-2 py-2.5 text-center font-semibold">
                    Qty
                  </th>
                  <th
                    aria-sort={
                      sortState?.field === "location"
                        ? sortState.direction === "asc"
                          ? "ascending"
                          : "descending"
                        : "none"
                    }
                    className="px-2 py-2.5 font-semibold"
                  >
                    <button
                      type="button"
                      onClick={() => cycleSort("location")}
                      className="inline-flex items-center gap-1.5 rounded-md px-1 py-0.5 text-white transition hover:bg-white/10 focus:outline-none focus:ring-2 focus:ring-blue-300"
                      title="Sort by location: original, ascending, descending"
                    >
                      Location
                      {sortIcon("location")}
                    </button>
                  </th>
                  <th
                    aria-sort={
                      sortState?.field === "aisle"
                        ? sortState.direction === "asc"
                          ? "ascending"
                          : "descending"
                        : "none"
                    }
                    className="px-2 py-2.5 text-center font-semibold"
                  >
                    <button
                      type="button"
                      onClick={() => cycleSort("aisle")}
                      className="inline-flex items-center justify-center gap-1.5 rounded-md px-1 py-0.5 text-white transition hover:bg-white/10 focus:outline-none focus:ring-2 focus:ring-blue-300"
                      title="Sort by aisle: original, ascending, descending"
                    >
                      Aisle
                      {sortIcon("aisle")}
                    </button>
                  </th>
                </tr>
              </thead>

              <tbody className="divide-y divide-slate-200 bg-white">
                {visibleParts.map((part, index) => (
                  <tr
                    key={`${part.source_type}-${part.item_id}-${part.asset_id ?? "stock"}-${part.location_id}-${index}`}
                    className="transition hover:bg-blue-50/60"
                  >
                    <td
                      className="truncate whitespace-nowrap px-3 py-2.5 font-semibold text-slate-900"
                      title={part.item_code}
                    >
                      {part.item_code}
                    </td>

                    <td className="px-2 py-2.5 text-center font-medium text-slate-700">
                      {formatQuantity(part.quantity)}
                    </td>

                    <td
                      className="truncate whitespace-nowrap px-2 py-2.5 text-slate-600"
                      title={part.location_name || part.location_code}
                    >
                      {part.location_name || part.location_code || "—"}
                    </td>

                    <td className="px-2 py-2.5 text-center font-medium text-slate-600">
                      {part.aisle_id == null ? "—" : aisleLabel(part.aisle_id)}
                    </td>
                  </tr>
                ))}

                {!loadingInventory && result && visibleParts.length === 0 && (
                  <tr>
                    <td
                      colSpan={4}
                      className="px-4 py-8 text-center text-sm text-slate-500"
                    >
                      No parts match the current filter.
                    </td>
                  </tr>
                )}

                {!loadingInventory && !result && (
                  <tr>
                    <td
                      colSpan={4}
                      className="px-4 py-8 text-center text-sm text-slate-500"
                    >
                      Select filters and press Search to load warehouse inventory.
                    </td>
                  </tr>
                )}

                {loadingInventory && (
                  <tr>
                    <td
                      colSpan={4}
                      className="px-4 py-8 text-center text-sm text-slate-500"
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