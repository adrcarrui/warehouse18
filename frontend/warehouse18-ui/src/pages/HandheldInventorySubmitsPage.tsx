import { useEffect, useMemo, useState } from "react";
import { AppShell } from "../app/AppShell";
import { apiGet } from "../api";
import { jsPDF } from "jspdf";
import { autoTable } from "jspdf-autotable";

const API_BASE = "/api";
const PAGE_SIZE = 5;

type SubmitSummary = {
  audit_id: number;
  id?: number;
  at: string;
  location_id: number;
  location_label?: string | null;
  reader_id?: string | null;
  total_items: number;
  ok_items: number;
  pending_items: number;
};

type SubmitRow = {
  item_code: string;
  reads: number;
  status: "OK" | "PENDING";
};

type SubmitDetail = SubmitSummary & {
  rows: SubmitRow[];
  payload: Record<string, unknown>;
};

type SubmitPage = {
  items: SubmitSummary[];
  page: number;
  page_size: number;
  total: number;
  pages: number;
};

function formatDateTime(value: string) {
  if (!value) return "";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString("es-ES", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

function getLocationName(locationLabel?: string | null) {
  if (!locationLabel) {
    return "—";
  }

  return (
    locationLabel
      .trim()
      .replace(/^\d+\s*[-–—:]\s*/, "")
      .trim() || "—"
  );
}

function sanitizeFileName(value: string) {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-zA-Z0-9_-]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .toLowerCase();
}

function formatPdfDate(value: string) {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "unknown-date";
  }

  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  const hours = String(date.getHours()).padStart(2, "0");
  const minutes = String(date.getMinutes()).padStart(2, "0");

  return `${year}-${month}-${day}_${hours}-${minutes}`;
}

function StatusPill({ status }: { status: "OK" | "PENDING" }) {
  const className =
    status === "OK"
      ? "rounded-full bg-emerald-100 px-2 py-1 text-xs font-semibold text-emerald-700"
      : "rounded-full bg-orange-100 px-2 py-1 text-xs font-semibold text-orange-700";

  return <span className={className}>{status}</span>;
}

function normalizeAuditId(item: SubmitSummary) {
  return item.audit_id ?? item.id ?? 0;
}

export default function HandheldInventorySubmitsPage() {
  const [items, setItems] = useState<SubmitSummary[]>([]);
  const [selected, setSelected] = useState<SubmitDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState("");
  const [page, setPage] = useState(1);
  const [exportingAuditId, setExportingAuditId] = useState<number | null>(null);

  async function loadList() {
    setLoading(true);
    setError(null);

    try {
      const { data } = await apiGet<SubmitPage>(
        `${API_BASE}/handheld-inventory-submits`,
        {
          page: 1,
          page_size: 100,
        }
      );

      const normalizedItems = (data.items ?? []).map((item) => ({
        ...item,
        audit_id: normalizeAuditId(item),
      }));

      setItems(normalizedItems);
      setPage(1);
    } catch (ex: any) {
      console.error("Error loading handheld inventory submits", ex);
      setError(ex?.message ?? "Error loading handheld inventory submits");
    } finally {
      setLoading(false);
    }
  }

  async function loadDetail(auditId: number) {
    if (!auditId) {
      setError("Invalid audit id.");
      return;
    }

    setDetailLoading(true);
    setError(null);

    try {
      const { data } = await apiGet<SubmitDetail>(
        `${API_BASE}/handheld-inventory-submits/${auditId}`
      );

      setSelected({
        ...data,
        audit_id: normalizeAuditId(data),
        rows: data.rows ?? [],
      });
    } catch (ex: any) {
      console.error("Error loading submit detail", ex);
      setError(ex?.message ?? "Error loading submit detail");
    } finally {
      setDetailLoading(false);
    }
  }

  async function downloadPdf(auditId: number) {
    if (!auditId) {
      setError("Invalid audit id.");
      return;
    }

    setExportingAuditId(auditId);
    setError(null);

    try {
      const { data } = await apiGet<SubmitDetail>(
        `${API_BASE}/handheld-inventory-submits/${auditId}`
      );

      const detail: SubmitDetail = {
        ...data,
        audit_id: normalizeAuditId(data),
        rows: data.rows ?? [],
      };

      const locationName = getLocationName(detail.location_label);
      const document = new jsPDF({
        orientation: "portrait",
        unit: "mm",
        format: "a4",
      });

      document.setFontSize(18);
      document.text("Handheld Inventory", 14, 18);

      document.setFontSize(10);
      document.text(`Submitted: ${formatDateTime(detail.at)}`, 14, 27);
      document.text(`Location: ${locationName}`, 14, 33);
      document.text(`Reader: ${detail.reader_id || "—"}`, 14, 39);
      document.text(
        `Total: ${detail.total_items}   OK: ${detail.ok_items}   Pending: ${detail.pending_items}`,
        14,
        45
      );

      autoTable(document, {
        startY: 52,
        head: [["Item", "Reads", "Status"]],
        body: detail.rows.map((row) => [
          row.item_code,
          String(row.reads),
          row.status,
        ]),
        styles: {
          fontSize: 9,
          cellPadding: 2.5,
        },
        headStyles: {
          fillColor: [30, 41, 59],
          textColor: [255, 255, 255],
        },
        alternateRowStyles: {
          fillColor: [248, 250, 252],
        },
        columnStyles: {
          1: { halign: "center", cellWidth: 25 },
          2: { halign: "center", cellWidth: 30 },
        },
        margin: {
          left: 14,
          right: 14,
        },
      });

      const safeLocation =
        sanitizeFileName(locationName) || `location-${detail.location_id}`;

      document.save(
        `handheld-inventory-${safeLocation}-${formatPdfDate(detail.at)}.pdf`
      );
    } catch (ex: any) {
      console.error("Error exporting handheld inventory PDF", ex);
      setError(ex?.message ?? "Error exporting handheld inventory PDF");
    } finally {
      setExportingAuditId(null);
    }
  }

  useEffect(() => {
    loadList();
  }, []);

  useEffect(() => {
    setPage(1);
  }, [filter]);

  const filteredItems = useMemo(() => {
    const normalizedFilter = filter.trim().toLocaleLowerCase("es-ES");

    if (!normalizedFilter) {
      return items;
    }

    return items.filter((item) => {
      const searchableValues = [
        formatDateTime(item.at),
        item.location_label ?? "",
        item.reader_id ?? "",
        String(item.total_items),
        String(item.ok_items),
        String(item.pending_items),
      ];

      return searchableValues.some((value) =>
        value.toLocaleLowerCase("es-ES").includes(normalizedFilter)
      );
    });
  }, [filter, items]);

  const totalPages = Math.max(1, Math.ceil(filteredItems.length / PAGE_SIZE));
  const currentPage = Math.min(page, totalPages);
  const pageStart = (currentPage - 1) * PAGE_SIZE;
  const visibleItems = filteredItems.slice(pageStart, pageStart + PAGE_SIZE);



  return (
    <AppShell
      title="Handheld Inventory"
      subtitle="Submitted inventory checks from Zebra handhelds"
      actions={
        <button
          type="button"
          onClick={loadList}
          disabled={loading}
          className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm font-medium text-slate-100 hover:bg-slate-800 disabled:opacity-60"
        >
          {loading ? "Loading..." : "Refresh"}
        </button>
      }
    >
      <div className="space-y-6">
        {error ? (
          <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        ) : null}

        <section className="space-y-3">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">
              Submitted lists
            </h2>
            <p className="text-sm text-slate-500">
              Each row is one list sent from the Zebra app after pressing ✓.
            </p>
          </div>

          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="w-full sm:max-w-md">
              <label htmlFor="handheld-submit-filter" className="sr-only">
                Filter submitted lists
              </label>
              <input
                id="handheld-submit-filter"
                type="search"
                value={filter}
                onChange={(event) => setFilter(event.target.value)}
                placeholder="Filter by date, location, reader or totals..."
                className="h-9 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 text-xs text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-blue-400 focus:bg-white focus:ring-2 focus:ring-blue-100"
              />
            </div>
          </div>

          <div className="overflow-auto rounded-xl border border-slate-200">
            <table className="w-full min-w-[860px] table-fixed text-xs">
              <colgroup>
                <col className="w-[155px]" />
                <col className="w-[190px]" />
                <col className="w-[135px]" />
                <col className="w-[70px]" />
                <col className="w-[70px]" />
                <col className="w-[80px]" />
                <col className="w-[112px]" />
              </colgroup>

              <thead className="sticky top-0 z-10 bg-blue-950">
                <tr className="text-left text-white">
                  <th className="px-3 py-2.5 font-semibold">Date</th>
                  <th className="px-2 py-2.5 font-semibold">Location</th>
                  <th className="px-2 py-2.5 font-semibold">Reader</th>
                  <th className="px-2 py-2.5 text-center font-semibold">
                    Total
                  </th>
                  <th className="px-2 py-2.5 text-center font-semibold">OK</th>
                  <th className="px-2 py-2.5 text-center font-semibold">
                    Pending
                  </th>
                  <th className="px-2 py-2.5 text-right font-semibold">
                    Actions
                  </th>
                </tr>
              </thead>

              <tbody className="divide-y divide-slate-200 bg-white">
                {visibleItems.map((item) => (
                  <tr
                    key={item.audit_id}
                    className="transition hover:bg-blue-50/60"
                  >
                    <td
                      className="truncate whitespace-nowrap px-3 py-2.5 text-slate-600"
                      title={formatDateTime(item.at)}
                    >
                      {formatDateTime(item.at)}
                    </td>
                    <td
                      className="truncate px-2 py-2.5 font-medium text-slate-900"
                      title={getLocationName(item.location_label)}
                    >
                      {getLocationName(item.location_label)}
                    </td>
                    <td
                      className="truncate px-2 py-2.5 text-slate-600"
                      title={item.reader_id || "—"}
                    >
                      {item.reader_id || "—"}
                    </td>
                    <td className="px-2 py-2.5 text-center font-semibold text-slate-900">
                      {item.total_items}
                    </td>
                    <td className="px-2 py-2.5 text-center font-semibold text-emerald-700">
                      {item.ok_items}
                    </td>
                    <td className="px-2 py-2.5 text-center font-semibold text-orange-700">
                      {item.pending_items}
                    </td>
                    <td className="px-2 py-2 text-right">
                      <div className="flex items-center justify-end gap-1 whitespace-nowrap">
                        <button
                          type="button"
                          onClick={() => void loadDetail(item.audit_id)}
                          className="inline-flex h-7 items-center justify-center rounded-lg border border-slate-200 bg-slate-50 px-2 text-xs font-medium text-slate-700 transition hover:bg-slate-100"
                        >
                          View
                        </button>
                        <button
                          type="button"
                          onClick={() => void downloadPdf(item.audit_id)}
                          disabled={exportingAuditId === item.audit_id}
                          className="inline-flex h-7 items-center justify-center rounded-lg border border-blue-200 bg-blue-50 px-2 text-xs font-medium text-blue-700 transition hover:bg-blue-100 disabled:cursor-not-allowed disabled:opacity-60"
                        >
                          {exportingAuditId === item.audit_id
                            ? "..."
                            : "PDF"}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}

                {!loading && visibleItems.length === 0 ? (
                  <tr>
                    <td
                      colSpan={7}
                      className="px-3 py-12 text-center text-slate-400"
                    >
                      No submitted lists match this search.
                    </td>
                  </tr>
                ) : null}

                {loading ? (
                  <tr>
                    <td
                      colSpan={7}
                      className="px-3 py-12 text-center text-slate-400"
                    >
                      Loading submitted lists…
                    </td>
                  </tr>
                ) : null}
              </tbody>
            </table>
          </div>

          {filteredItems.length > PAGE_SIZE ? (
            <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
              <p className="text-sm text-slate-500">
                Showing {pageStart + 1}–
                {Math.min(pageStart + PAGE_SIZE, filteredItems.length)} of {" "}
                {filteredItems.length}
              </p>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setPage(Math.max(1, currentPage - 1))}
                  disabled={currentPage === 1}
                  className="inline-flex h-9 items-center justify-center rounded-xl border border-slate-200 bg-slate-50 px-3 text-sm font-medium text-slate-800 transition hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  Previous
                </button>
                <span className="min-w-24 text-center text-sm text-slate-600">
                  Page {currentPage} of {totalPages}
                </span>
                <button
                  type="button"
                  onClick={() =>
                    setPage(Math.min(totalPages, currentPage + 1))
                  }
                  disabled={currentPage === totalPages}
                  className="inline-flex h-9 items-center justify-center rounded-xl border border-slate-200 bg-slate-50 px-3 text-sm font-medium text-slate-800 transition hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  Next
                </button>
              </div>
            </div>
          ) : null}
        </section>

        <section className="space-y-3">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <h2 className="text-lg font-semibold text-slate-900">
                Selected list
              </h2>
              <p className="text-sm text-slate-500">
                {selected
                  ? `${formatDateTime(selected.at)} · ${getLocationName(
                      selected.location_label
                    )}`
                  : "Select a submitted list to see the item status."}
              </p>
            </div>

            {selected ? (
              <button
                type="button"
                onClick={() => void downloadPdf(selected.audit_id)}
                disabled={exportingAuditId === selected.audit_id}
                className="rounded-lg border border-blue-200 bg-blue-50 px-3 py-2 text-sm font-medium text-blue-700 hover:bg-blue-100 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {exportingAuditId === selected.audit_id
                  ? "Exporting PDF..."
                  : "Download PDF"}
              </button>
            ) : null}
          </div>

          <div className="overflow-auto rounded-xl border border-slate-200">
            <table className="w-full min-w-[520px] table-fixed text-xs">
              <colgroup>
                <col />
                <col className="w-[100px]" />
                <col className="w-[125px]" />
              </colgroup>

              <thead className="sticky top-0 z-10 bg-blue-950">
                <tr className="text-left text-white">
                  <th className="px-3 py-2.5 font-semibold">Item</th>
                  <th className="px-2 py-2.5 text-center font-semibold">
                    Reads
                  </th>
                  <th className="px-2 py-2.5 text-center font-semibold">
                    Status
                  </th>
                </tr>
              </thead>

              <tbody className="divide-y divide-slate-200 bg-white">
                {detailLoading ? (
                  <tr>
                    <td
                      colSpan={3}
                      className="px-3 py-12 text-center text-slate-400"
                    >
                      Loading detail…
                    </td>
                  </tr>
                ) : selected ? (
                  selected.rows.length > 0 ? (
                    selected.rows.map((row, index) => (
                      <tr
                        key={`${row.item_code}-${index}`}
                        className="transition hover:bg-blue-50/60"
                      >
                        <td
                          className="truncate px-3 py-2.5 font-medium text-slate-900"
                          title={row.item_code}
                        >
                          {row.item_code}
                        </td>
                        <td className="px-2 py-2.5 text-center text-slate-600">
                          {row.reads}
                        </td>
                        <td className="px-2 py-2.5 text-center">
                          <StatusPill status={row.status} />
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td
                        colSpan={3}
                        className="px-3 py-12 text-center text-slate-400"
                      >
                        This submitted list contains no items.
                      </td>
                    </tr>
                  )
                ) : (
                  <tr>
                    <td
                      colSpan={3}
                      className="px-3 py-12 text-center text-slate-400"
                    >
                      Select a submitted list to see its items.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </AppShell>
  );
}