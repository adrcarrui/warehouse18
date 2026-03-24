import { useEffect, useMemo, useState } from "react";
import { apiGet, apiPost, apiPatch, apiDelete } from "../api";
import type { PageMeta, PageOut } from "../api";
import { useNavigate, useSearchParams } from "react-router-dom";
import { AppShell } from "../app/AppShell";

type StockContainerOut = {
  id: number;
  container_code?: string | null;
  item_id: number;
  location_id: number;
  quantity: number | string; // Decimal a veces viene como string
  status?: string | null;
  is_active?: boolean;
  created_at?: string | null;
};

type StockContainerCreateIn = {
  item_id: number;
  container_code?: string | null;
  location_id: number;
  quantity: number; // si tu backend pide string, cambia a string
  status?: string;
};

type StockContainerUpdateIn = Partial<StockContainerCreateIn> & {
  is_active?: boolean;
};

type ItemOut = {
  id: number;
  code?: string | null;
  name?: string | null;
};

type LocationOut = {
  id: number;
  code: string;
  name: string;
  type: string;
  parent_id?: number | null;
  is_active: boolean;
};

function numOrUndef(v: string): number | undefined {
  const s = v.trim();
  if (!s) return undefined;
  const n = Number(s);
  return Number.isFinite(n) ? n : undefined;
}

function labelItem(i?: ItemOut): string {
  if (!i) return "";
  const a = (i.code ?? "").trim();
  const b = (i.name ?? "").trim();
  if (a && b) return `${a} · ${b}`;
  return a || b || String(i.id);
}

function labelLoc(l?: LocationOut): string {
  if (!l) return "";
  const a = (l.code ?? "").trim();
  const b = (l.name ?? "").trim();
  if (a && b) return `${a} · ${b}`;
  return a || b || String(l.id);
}

function fieldRow(label: string, el: React.ReactNode) {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "140px 1fr", gap: 10, alignItems: "center" }}>
      <div style={{ color: "#444", fontSize: 13 }}>{label}</div>
      <div>{el}</div>
    </div>
  );
}

export default function StockContainersPage() {
  const nav = useNavigate();
  const [sp] = useSearchParams();

  // allow deep-linking from elsewhere:
  const initialItem = sp.get("item_id") ?? "";
  const initialLoc = sp.get("location_id") ?? "";

  const [itemId, setItemId] = useState(initialItem);
  const [locationId, setLocationId] = useState(initialLoc);
  const [status, setStatus] = useState("");
  const [includeInactive, setIncludeInactive] = useState(false);

  const [page, setPage] = useState(1);
  const [pageSize] = useState(25);

  const [rows, setRows] = useState<StockContainerOut[]>([]);
  const [meta, setMeta] = useState<PageMeta>({
    page: 1,
    pageSize: 25,
    total: 0,
    pages: 0,
    link: null,
  });

  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  // lookups
  const [itemsById, setItemsById] = useState<Record<number, ItemOut>>({});
  const [locsById, setLocsById] = useState<Record<number, LocationOut>>({});
  const [lookupLoading, setLookupLoading] = useState(false);

  // modal
  const [open, setOpen] = useState(false);
  const [mode, setMode] = useState<"create" | "edit">("create");
  const [editing, setEditing] = useState<StockContainerOut | null>(null);

  const [form, setForm] = useState({
    item_id: "",
    container_code: "",
    location_id: "",
    quantity: "",
    status: "available",
    is_active: true,
  });

  const itemIdNum = useMemo(() => numOrUndef(itemId), [itemId]);
  const locationIdNum = useMemo(() => numOrUndef(locationId), [locationId]);

  function itemLabel(id: number) {
    return labelItem(itemsById[id]) || String(id);
  }
  function locLabel(id: number) {
    return labelLoc(locsById[id]) || String(id);
  }

  async function loadLookups() {
    setLookupLoading(true);
    setErr(null);
    try {
      const itemsResp = await apiGet<PageOut<ItemOut>>("/api/items", { page: 1, page_size: 200 });
      const locsResp = await apiGet<PageOut<LocationOut>>("/api/locations", {
        page: 1,
        page_size: 200,
        include_inactive: true,
      });

      const itemsMap: Record<number, ItemOut> = {};
      for (const it of itemsResp.data.items) itemsMap[it.id] = it;

      const locsMap: Record<number, LocationOut> = {};
      for (const l of locsResp.data.items) locsMap[l.id] = l;

      setItemsById(itemsMap);
      setLocsById(locsMap);
    } catch (e: any) {
      setErr(e?.message ?? String(e));
    } finally {
      setLookupLoading(false);
    }
  }

  async function load(p: number) {
    setLoading(true);
    setErr(null);
    try {
      const { data, meta } = await apiGet<PageOut<StockContainerOut>>("/api/stock-containers", {
        item_id: itemIdNum ?? undefined,
        location_id: locationIdNum ?? undefined,
        status: status.trim() || undefined,
        include_inactive: includeInactive, // si tu backend no lo soporta, quítalo
        page: p,
        page_size: pageSize,
      });

      setRows(data.items);
      setMeta(meta);
      setPage(p);
    } catch (e: any) {
      setErr(e?.message ?? String(e));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    (async () => {
      await loadLookups();
      await load(1);
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const canPrev = !loading && meta.page > 1;
  const canNext = !loading && meta.pages > 0 && meta.page < meta.pages;

  function openCreate() {
    setMode("create");
    setEditing(null);
    setForm({ item_id: "", container_code: "", location_id: "", quantity: "", status: "open", is_active: true });
    setOpen(true);
  }

  function openEdit(r: StockContainerOut) {
    setMode("edit");
    setEditing(r);
    setForm({
      item_id: String(r.item_id),
      container_code: r.container_code ?? "",
      location_id: String(r.location_id),
      quantity: String(r.quantity),
      status: (r.status ?? "available") as string,
      is_active: r.is_active ?? true,
    });
    setOpen(true);
  }

  function closeModal() {
    setOpen(false);
    setEditing(null);
  }

  async function submit() {
    setErr(null);

    const item_id = Number(form.item_id);
    const container_code = form.container_code.trim() || null;
    const location_id = Number(form.location_id);
    const quantity = Number(form.quantity);

    if (!Number.isFinite(item_id) || !Number.isFinite(location_id) || !Number.isFinite(quantity)) {
      setErr("item_id, location_id y quantity deben ser numéricos.");
      return;
    }
    if (quantity <= 0) {
      setErr("quantity debe ser > 0.");
      return;
    }

    try {
      if (mode === "create") {
        const payload: StockContainerCreateIn = {
          item_id,
          container_code,
          location_id,
          quantity,
          status: form.status?.trim() || "available",
        };
        await apiPost<StockContainerOut>("/api/stock-containers/", payload);
      } else {
        if (!editing) return;

        const payload: StockContainerUpdateIn = {
          item_id,
          container_code,
          location_id,
          quantity,
          status: form.status?.trim() || undefined,
          is_active: form.is_active,
        };

        await apiPatch<StockContainerOut>(`/api/stock-containers/${editing.id}`, payload);
      }

      closeModal();
      await load(1);
    } catch (e: any) {
      setErr(e?.message ?? String(e));
    }
  }

  async function deactivate(r: StockContainerOut) {
    setErr(null);
    try {
      await apiDelete<{ status: string }>(`/api/stock-containers/${r.id}`);
      await load(1);
    } catch (e: any) {
      setErr(e?.message ?? String(e));
    }
  }

  function goMovements(r: StockContainerOut) {
    nav(`/movements?stock_container_id=${encodeURIComponent(String(r.id))}`);
  }

  return (
    <AppShell title="Stock Containers" subtitle="Manage inventory containers and their contents">
    <div style={{ padding: 16, fontFamily: "system-ui" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12 }}>
        <h2 style={{ marginTop: 0, marginBottom: 0 }}>Stock Containers</h2>
        <div style={{ display: "flex", gap: 8 }}>
          <button onClick={loadLookups} disabled={lookupLoading}>
            Reload lookups
          </button>
          <button onClick={openCreate}>+ New container</button>
        </div>
      </div>

      <div style={{ display: "flex", gap: 12, alignItems: "center", marginTop: 12, marginBottom: 12, flexWrap: "wrap" }}>
        <input value={itemId} onChange={(e) => setItemId(e.target.value)} placeholder="item_id" style={{ padding: 8, width: 140 }} />
        <input value={locationId} onChange={(e) => setLocationId(e.target.value)} placeholder="location_id" style={{ padding: 8, width: 140 }} />
        <input value={status} onChange={(e) => setStatus(e.target.value)} placeholder="status (optional)" style={{ padding: 8, width: 180 }} />

        <label style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <input type="checkbox" checked={includeInactive} onChange={(e) => setIncludeInactive(e.target.checked)} />
          include inactive
        </label>

        <button onClick={() => load(1)} disabled={loading}>
          Search
        </button>
      </div>

      {err && <div style={{ color: "crimson", marginBottom: 12 }}>Error: {err}</div>}

      <div style={{ marginBottom: 10, color: "#444" }}>
        Total: {meta.total} | Page {meta.page}/{meta.pages} | Page size {meta.pageSize}
        {lookupLoading && <span style={{ marginLeft: 10, color: "#666" }}>Loading lookups…</span>}
      </div>

      <div style={{ border: "1px solid #eee", borderRadius: 8, overflow: "hidden" }}>
        <table width="100%" cellPadding={10} style={{ borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ textAlign: "left", background: "#fafafa", borderBottom: "1px solid #eee" }}>
              <th>ID</th>
              <th>Container Code</th>
              <th>Item</th>
              <th>Location</th>
              <th>Qty</th>
              <th>Status</th>
              <th>Active</th>
              <th style={{ width: 280 }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id} style={{ borderBottom: "1px solid #f2f2f2" }}>
                <td>{r.id}</td>
                <td style={{ fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace" }}>
                  {r.container_code ?? ""}
                </td>
                <td>{itemLabel(r.item_id)}</td>
                <td>{locLabel(r.location_id)}</td>
                <td>{String(r.quantity)}</td>
                <td>{r.status ?? ""}</td>
                <td>{r.is_active === undefined ? "-" : r.is_active ? "yes" : "no"}</td>
                <td>
                  <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                    <button onClick={() => openEdit(r)}>Edit</button>
                    <button onClick={() => goMovements(r)}>Movements</button>
                    <button onClick={() => deactivate(r)} disabled={r.is_active === false}>
                      Deactivate
                    </button>
                  </div>
                </td>
              </tr>
            ))}

            {!loading && rows.length === 0 && (
              <tr>
                <td colSpan={7} style={{ padding: 16, color: "#666" }}>
                  No results
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
        <button onClick={() => load(page - 1)} disabled={!canPrev}>
          Prev
        </button>
        <button onClick={() => load(page + 1)} disabled={!canNext}>
          Next
        </button>
      </div>

      {open && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0,0,0,0.25)",
            display: "grid",
            placeItems: "center",
            padding: 16,
          }}
          onMouseDown={(e) => {
            if (e.target === e.currentTarget) closeModal();
          }}
        >
          <div style={{ width: 560, maxWidth: "100%", background: "white", borderRadius: 12, padding: 16 }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12 }}>
              <h3 style={{ margin: 0 }}>{mode === "create" ? "Create stock container" : `Edit stock container #${editing?.id}`}</h3>
              <button onClick={closeModal}>X</button>
            </div>

            <div style={{ display: "grid", gap: 12, marginTop: 14 }}>
              {fieldRow(
                "Container Code (EPC)",
                <input value={form.container_code} onChange={(e) => setForm((s) => ({ ...s, container_code: e.target.value }))} placeholder="E200..." style={{ padding: 8, width: "100%" }}
                />
              )}
              {fieldRow(
                "Item ID",
                <input value={form.item_id} onChange={(e) => setForm((s) => ({ ...s, item_id: e.target.value }))} style={{ padding: 8, width: "100%" }} />
              )}

              {fieldRow(
                "Location ID",
                <input value={form.location_id} onChange={(e) => setForm((s) => ({ ...s, location_id: e.target.value }))} style={{ padding: 8, width: "100%" }} />
              )}

              {fieldRow(
                "Quantity",
                <input value={form.quantity} onChange={(e) => setForm((s) => ({ ...s, quantity: e.target.value }))} style={{ padding: 8, width: "100%" }} />
              )}

              {fieldRow(
                "Status",
                <input value={form.status} onChange={(e) => setForm((s) => ({ ...s, status: e.target.value }))} placeholder="available" style={{ padding: 8, width: "100%" }} />
              )}

              {fieldRow(
                "Active",
                <label style={{ display: "flex", gap: 8, alignItems: "center" }}>
                  <input type="checkbox" checked={form.is_active} onChange={(e) => setForm((s) => ({ ...s, is_active: e.target.checked }))} />
                  is_active
                </label>
              )}

              <div style={{ display: "flex", gap: 10, justifyContent: "flex-end", marginTop: 6 }}>
                <button onClick={closeModal}>Cancel</button>
                <button onClick={submit}>{mode === "create" ? "Create" : "Save"}</button>
              </div>

              <div style={{ color: "#666", fontSize: 12 }}>
                Nota: este modal sigue usando IDs para crear rápido. Luego metemos selectores por código si te cansas de memorizar números.
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
    </AppShell>
  );
}
