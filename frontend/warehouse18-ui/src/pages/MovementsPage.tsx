import { useEffect, useMemo, useState } from "react";
import { apiGet } from "../api";
import type { PageMeta, PageOut } from "../api";
import { useSearchParams } from "react-router-dom";


type MovementOut = {
  id: number;

  movement_type_id?: number | null;

  stock_container_id?: number | null;
  item_id?: number | null;

  from_location_id?: number | null;
  to_location_id?: number | null;

  quantity?: number | string | null;

  user_id?: number | null;
  notes?: string | null;

  created_at?: string | null;
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

export default function MovementsPage() {
  // filters
  const [sp] = useSearchParams();
  const initialSC = sp.get("stock_container_id") ?? "";
  const [itemId, setItemId] = useState("");
  const [stockContainerId, setStockContainerId] = useState(initialSC);
  const [locationId, setLocationId] = useState("");
  const [movementTypeId, setMovementTypeId] = useState("");
  const [userId, setUserId] = useState("");

  const [fromDate, setFromDate] = useState(""); // YYYY-MM-DD
  const [toDate, setToDate] = useState(""); // YYYY-MM-DD

  // pagination
  const [page, setPage] = useState(1);
  const [pageSize] = useState(25);

  // data
  const [rows, setRows] = useState<MovementOut[]>([]);
  const [meta, setMeta] = useState<PageMeta>({
    page: 1,
    pageSize: 25,
    total: 0,
    pages: 0,
    link: null,
  });

  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  // lookup maps
  const [itemsById, setItemsById] = useState<Record<number, ItemOut>>({});
  const [locsById, setLocsById] = useState<Record<number, LocationOut>>({});
  const [lookupLoading, setLookupLoading] = useState(false);

  // modal
  const [selected, setSelected] = useState<MovementOut | null>(null);

  const itemIdNum = useMemo(() => numOrUndef(itemId), [itemId]);
  const scIdNum = useMemo(() => numOrUndef(stockContainerId), [stockContainerId]);
  const locIdNum = useMemo(() => numOrUndef(locationId), [locationId]);
  const mtIdNum = useMemo(() => numOrUndef(movementTypeId), [movementTypeId]);
  const userIdNum = useMemo(() => numOrUndef(userId), [userId]);

  async function loadLookups() {
    setLookupLoading(true);
    setErr(null);

    try {
      // Ajusta page_size si tienes muchos. Para MVP vale 200-500.
      const itemsResp = await apiGet<PageOut<ItemOut>>("/api/items", { page: 1, page_size: 500 });
      const locsResp = await apiGet<PageOut<LocationOut>>("/api/locations", {
        page: 1,
        page_size: 500,
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
      // Ajusta el path si tu API usa otro (stock-moves, etc.)
      const { data, meta } = await apiGet<PageOut<MovementOut>>("/api/movements", {
        item_id: itemIdNum ?? undefined,
        stock_container_id: scIdNum ?? undefined,

        // location_id suele significar "from o to"
        location_id: locIdNum ?? undefined,

        movement_type_id: mtIdNum ?? undefined,
        user_id: userIdNum ?? undefined,

        date_from: fromDate.trim() || undefined,
        date_to: toDate.trim() || undefined,

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
    // 1) lookups primero (para pintar bonito)
    // 2) luego movimientos
    (async () => {
      await loadLookups();
      await load(1);
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const canPrev = !loading && meta.page > 1;
  const canNext = !loading && meta.pages > 0 && meta.page < meta.pages;

  function itemLabelFromId(id?: number | null) {
    if (!id) return "";
    return labelItem(itemsById[id]) || String(id);
  }

  function locLabelFromId(id?: number | null) {
    if (!id) return "";
    return labelLoc(locsById[id]) || String(id);
  }

  return (
    <div style={{ padding: 16, fontFamily: "system-ui" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12 }}>
        <h2 style={{ marginTop: 0, marginBottom: 0 }}>Movements</h2>
        <div style={{ display: "flex", gap: 8 }}>
          <button onClick={loadLookups} disabled={lookupLoading}>
            Reload lookups
          </button>
          <button onClick={() => load(1)} disabled={loading}>
            Refresh
          </button>
        </div>
      </div>

      <div
        style={{
          display: "flex",
          gap: 12,
          alignItems: "center",
          marginTop: 12,
          marginBottom: 12,
          flexWrap: "wrap",
        }}
      >
        <input value={itemId} onChange={(e) => setItemId(e.target.value)} placeholder="item_id" style={{ padding: 8, width: 120 }} />
        <input value={stockContainerId} onChange={(e) => setStockContainerId(e.target.value)} placeholder="stock_container_id" style={{ padding: 8, width: 170 }} />
        <input value={locationId} onChange={(e) => setLocationId(e.target.value)} placeholder="location_id (from/to)" style={{ padding: 8, width: 170 }} />
        <input value={movementTypeId} onChange={(e) => setMovementTypeId(e.target.value)} placeholder="movement_type_id" style={{ padding: 8, width: 170 }} />
        <input value={userId} onChange={(e) => setUserId(e.target.value)} placeholder="user_id" style={{ padding: 8, width: 120 }} />

        <input type="date" value={fromDate} onChange={(e) => setFromDate(e.target.value)} style={{ padding: 8 }} title="date_from" />
        <input type="date" value={toDate} onChange={(e) => setToDate(e.target.value)} style={{ padding: 8 }} title="date_to" />

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
              <th>Type</th>
              <th>SC</th>
              <th>Item</th>
              <th>From</th>
              <th>To</th>
              <th>Qty</th>
              <th>User</th>
              <th>When</th>
              <th>Notes</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr
                key={r.id}
                onClick={() => setSelected(r)}
                style={{ borderBottom: "1px solid #f2f2f2", cursor: "pointer" }}
                title="Click for details"
              >
                <td>{r.id}</td>
                <td>{r.movement_type_id ?? ""}</td>
                <td>{r.stock_container_id ?? ""}</td>
                <td>{r.item_id ? itemLabelFromId(r.item_id) : ""}</td>
                <td>{r.from_location_id ? locLabelFromId(r.from_location_id) : ""}</td>
                <td>{r.to_location_id ? locLabelFromId(r.to_location_id) : ""}</td>
                <td>{r.quantity == null ? "" : String(r.quantity)}</td>
                <td>{r.user_id ?? ""}</td>
                <td style={{ whiteSpace: "nowrap" }}>{r.created_at ?? ""}</td>
                <td style={{ maxWidth: 320, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {r.notes ?? ""}
                </td>
              </tr>
            ))}

            {!loading && rows.length === 0 && (
              <tr>
                <td colSpan={10} style={{ padding: 16, color: "#666" }}>
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

      {/* Modal */}
      {selected && (
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
            if (e.target === e.currentTarget) setSelected(null);
          }}
        >
          <div style={{ width: 720, maxWidth: "100%", background: "white", borderRadius: 12, padding: 16 }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12 }}>
              <h3 style={{ margin: 0 }}>Movement #{selected.id}</h3>
              <button onClick={() => setSelected(null)}>X</button>
            </div>

            <div style={{ marginTop: 10, color: "#444", fontSize: 13 }}>
              <div><b>Item:</b> {selected.item_id ? itemLabelFromId(selected.item_id) : ""}</div>
              <div><b>From:</b> {selected.from_location_id ? locLabelFromId(selected.from_location_id) : ""}</div>
              <div><b>To:</b> {selected.to_location_id ? locLabelFromId(selected.to_location_id) : ""}</div>
            </div>

            <pre
              style={{
                marginTop: 12,
                background: "#fafafa",
                border: "1px solid #eee",
                borderRadius: 8,
                padding: 12,
                maxHeight: 420,
                overflow: "auto",
                fontSize: 12,
              }}
            >
{JSON.stringify(selected, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}
