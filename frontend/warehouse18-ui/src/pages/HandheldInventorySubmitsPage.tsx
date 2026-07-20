import { useEffect, useMemo, useState } from "react";
import { AppShell } from "../app/AppShell";
import { apiGet } from "../api";
import { Table } from "../ui/Table";

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

  const sessionRows = visibleItems.map((item) => [
    formatDateTime(item.at),
    getLocationName(item.location_label),
    item.reader_id || "",
    item.total_items,
    <span className="font-semibold text-emerald-700">{item.ok_items}</span>,
    <span className="font-semibold text-orange-700">{item.pending_items}</span>,
    <button
      type="button"
      onClick={() => loadDetail(item.audit_id)}
      className="rounded-lg border border-zinc-300 px-3 py-1 text-sm font-medium hover:bg-zinc-50"
    >
      View
    </button>,
  ]);

  const detailRows = (selected?.rows ?? []).map((row) => [
    row.item_code,
    row.reads,
    <StatusPill status={row.status} />,
  ]);

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
            <h2 className="text-lg font-semibold text-zinc-900">
              Submitted lists
            </h2>
            <p className="text-sm text-zinc-500">
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
                className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900 outline-none placeholder:text-zinc-400 focus:border-slate-500 focus:ring-2 focus:ring-slate-200"
              />
            </div>

            <p className="text-sm text-zinc-500">
              {filteredItems.length} submission
              {filteredItems.length === 1 ? "" : "s"}
            </p>
          </div>

          <Table
            headers={[
              "Date",
              "Location",
              "Reader",
              "Total",
              "Ok",
              "Pending",
              "",
            ]}
            rows={sessionRows}
          />

          {filteredItems.length > PAGE_SIZE ? (
            <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
              <p className="text-sm text-zinc-500">
                Showing {pageStart + 1}–
                {Math.min(pageStart + PAGE_SIZE, filteredItems.length)} of {" "}
                {filteredItems.length}
              </p>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setPage(Math.max(1, currentPage - 1))}
                  disabled={currentPage === 1}
                  className="rounded-lg border border-zinc-300 px-3 py-1.5 text-sm font-medium text-zinc-700 hover:bg-zinc-50 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  Previous
                </button>
                <span className="min-w-24 text-center text-sm text-zinc-600">
                  Page {currentPage} of {totalPages}
                </span>
                <button
                  type="button"
                  onClick={() =>
                    setPage(Math.min(totalPages, currentPage + 1))
                  }
                  disabled={currentPage === totalPages}
                  className="rounded-lg border border-zinc-300 px-3 py-1.5 text-sm font-medium text-zinc-700 hover:bg-zinc-50 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  Next
                </button>
              </div>
            </div>
          ) : null}
        </section>

        <section className="space-y-3">
          <div>
            <h2 className="text-lg font-semibold text-zinc-900">
              Selected list
            </h2>
            <p className="text-sm text-zinc-500">
              {selected
                ? `${formatDateTime(selected.at)} · ${
                    selected.location_label || "—"
                  }`
                : "Select a submitted list to see the item status."}
            </p>
          </div>

          {detailLoading ? (
            <div className="rounded-xl border border-zinc-200 bg-white px-4 py-6 text-sm text-zinc-500">
              Loading detail...
            </div>
          ) : (
            <Table headers={["Item", "Reads", "Status"]} rows={detailRows} />
          )}
        </section>
      </div>
    </AppShell>
  );
}