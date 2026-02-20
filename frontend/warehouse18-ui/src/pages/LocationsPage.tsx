import { useEffect, useMemo, useState } from "react";
import { apiDelete, apiGet, apiPatch, apiPost } from "../api";
import type { PageMeta, PageOut } from "../api";
import { AppShell } from "../app/AppShell";

type LocationOut = {
  id: number;
  code: string;
  name: string;
  type: string;
  parent_id?: number | null;
  is_active: boolean;
};

type LocationCreateIn = {
  code: string;
  name: string;
  type: string;
  parent_id?: number | null;
  is_active?: boolean;
};

type LocationUpdateIn = Partial<Omit<LocationCreateIn, "code">> & {
  is_active?: boolean;
};

function fieldRow(label: string, el: React.ReactNode) {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "140px 1fr", gap: 10, alignItems: "center" }}>
      <div style={{ color: "#444", fontSize: 13 }}>{label}</div>
      <div>{el}</div>
    </div>
  );
}

export default function LocationsPage() {
  const [q, setQ] = useState("");
  const [includeInactive, setIncludeInactive] = useState(false);
  const [parentId, setParentId] = useState<string>("");

  const [page, setPage] = useState(1);
  const [pageSize] = useState(25);

  const [rows, setRows] = useState<LocationOut[]>([]);
  const [meta, setMeta] = useState<PageMeta>({
    page: 1,
    pageSize: 25,
    total: 0,
    pages: 0,
    link: null,
  });

  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  // modal state
  const [open, setOpen] = useState(false);
  const [mode, setMode] = useState<"create" | "edit">("create");
  const [editing, setEditing] = useState<LocationOut | null>(null);

  const [form, setForm] = useState({
    code: "",
    name: "",
    type: "",
    parent_id: "",
    is_active: true,
  });

  const parentIdNum = useMemo(() => {
    const v = parentId.trim();
    if (!v) return undefined;
    const n = Number(v);
    return Number.isFinite(n) ? n : undefined;
  }, [parentId]);

  async function load(p: number) {
    setLoading(true);
    setErr(null);
    try {
      const { data, meta } = await apiGet<PageOut<LocationOut>>("/api/locations", {
        q: q.trim() || undefined,
        include_inactive: includeInactive,
        parent_id: parentIdNum ?? undefined,
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
    load(1);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const canPrev = !loading && meta.page > 1;
  const canNext = !loading && meta.pages > 0 && meta.page < meta.pages;

  function openCreate() {
    setMode("create");
    setEditing(null);
    setForm({ code: "", name: "", type: "", parent_id: "", is_active: true });
    setOpen(true);
  }

  function openEdit(r: LocationOut) {
    setMode("edit");
    setEditing(r);
    setForm({
      code: r.code,
      name: r.name,
      type: r.type,
      parent_id: r.parent_id == null ? "" : String(r.parent_id),
      is_active: r.is_active,
    });
    setOpen(true);
  }

  function closeModal() {
    setOpen(false);
    setEditing(null);
  }

  async function submit() {
    setErr(null);

    const parent_id =
      form.parent_id.trim() === ""
        ? null
        : Number.isFinite(Number(form.parent_id))
        ? Number(form.parent_id)
        : NaN;

    if (form.name.trim() === "" || form.type.trim() === "" || (mode === "create" && form.code.trim() === "")) {
      setErr("Completa code/name/type.");
      return;
    }
    if (parent_id !== null && Number.isNaN(parent_id)) {
      setErr("parent_id debe ser un número o vacío.");
      return;
    }

    try {
      if (mode === "create") {
        const payload: LocationCreateIn = {
          code: form.code.trim(),
          name: form.name.trim(),
          type: form.type.trim(),
          parent_id,
          is_active: form.is_active,
        };
        await apiPost<LocationOut>("/api/locations/", payload);
      } else {
        if (!editing) return;

        const payload: LocationUpdateIn = {
          name: form.name.trim(),
          type: form.type.trim(),
          parent_id,
          is_active: form.is_active,
        };
        await apiPatch<LocationOut>(`/api/locations/${editing.id}`, payload);
      }

      closeModal();
      await load(1);
    } catch (e: any) {
      setErr(e?.message ?? String(e));
    }
  }

  async function deactivate(r: LocationOut) {
    setErr(null);
    try {
      await apiDelete<{ status: string }>(`/api/locations/${r.id}`);
      await load(1);
    } catch (e: any) {
      setErr(e?.message ?? String(e));
    }
  }

  return (
    <AppShell title="Locations" subtitle="Manage locations">
    <div style={{ padding: 16, fontFamily: "system-ui" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12 }}>
        <h2 style={{ marginTop: 0, marginBottom: 0 }}>Locations</h2>
        <button onClick={openCreate}>+ New location</button>
      </div>

      <div style={{ display: "flex", gap: 12, alignItems: "center", marginTop: 12, marginBottom: 12, flexWrap: "wrap" }}>
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Search (q) by code/name..."
          style={{ padding: 8, width: 320 }}
        />

        <input
          value={parentId}
          onChange={(e) => setParentId(e.target.value)}
          placeholder="parent_id (optional)"
          style={{ padding: 8, width: 180 }}
        />

        <label style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <input
            type="checkbox"
            checked={includeInactive}
            onChange={(e) => setIncludeInactive(e.target.checked)}
          />
          include inactive
        </label>

        <button onClick={() => load(1)} disabled={loading}>
          Search
        </button>
      </div>

      {err && <div style={{ color: "crimson", marginBottom: 12 }}>Error: {err}</div>}

      <div style={{ marginBottom: 10, color: "#444" }}>
        Total: {meta.total} | Page {meta.page}/{meta.pages} | Page size {meta.pageSize}
      </div>

      <div style={{ border: "1px solid #eee", borderRadius: 8, overflow: "hidden" }}>
        <table width="100%" cellPadding={10} style={{ borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ textAlign: "left", background: "#fafafa", borderBottom: "1px solid #eee" }}>
              <th>ID</th>
              <th>Code</th>
              <th>Name</th>
              <th>Type</th>
              <th>Parent</th>
              <th>Active</th>
              <th style={{ width: 220 }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id} style={{ borderBottom: "1px solid #f2f2f2" }}>
                <td>{r.id}</td>
                <td>{r.code}</td>
                <td>{r.name}</td>
                <td>{r.type}</td>
                <td>{r.parent_id ?? ""}</td>
                <td>{r.is_active ? "yes" : "no"}</td>
                <td>
                  <div style={{ display: "flex", gap: 8 }}>
                    <button onClick={() => openEdit(r)}>Edit</button>
                    <button onClick={() => deactivate(r)} disabled={!r.is_active}>
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
            // click outside closes
            if (e.target === e.currentTarget) closeModal();
          }}
        >
          <div style={{ width: 560, maxWidth: "100%", background: "white", borderRadius: 12, padding: 16 }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12 }}>
              <h3 style={{ margin: 0 }}>
                {mode === "create" ? "Create location" : `Edit location #${editing?.id}`}
              </h3>
              <button onClick={closeModal}>X</button>
            </div>

            <div style={{ display: "grid", gap: 12, marginTop: 14 }}>
              {fieldRow(
                "Code",
                <input
                  value={form.code}
                  disabled={mode === "edit"}
                  onChange={(e) => setForm((s) => ({ ...s, code: e.target.value }))}
                  style={{ padding: 8, width: "100%", opacity: mode === "edit" ? 0.7 : 1 }}
                />
              )}

              {fieldRow(
                "Name",
                <input
                  value={form.name}
                  onChange={(e) => setForm((s) => ({ ...s, name: e.target.value }))}
                  style={{ padding: 8, width: "100%" }}
                />
              )}

              {fieldRow(
                "Type",
                <input
                  value={form.type}
                  onChange={(e) => setForm((s) => ({ ...s, type: e.target.value }))}
                  style={{ padding: 8, width: "100%" }}
                />
              )}

              {fieldRow(
                "Parent ID",
                <input
                  value={form.parent_id}
                  onChange={(e) => setForm((s) => ({ ...s, parent_id: e.target.value }))}
                  placeholder="(empty = no parent)"
                  style={{ padding: 8, width: "100%" }}
                />
              )}

              {fieldRow(
                "Active",
                <label style={{ display: "flex", gap: 8, alignItems: "center" }}>
                  <input
                    type="checkbox"
                    checked={form.is_active}
                    onChange={(e) => setForm((s) => ({ ...s, is_active: e.target.checked }))}
                  />
                  is_active
                </label>
              )}

              <div style={{ display: "flex", gap: 10, justifyContent: "flex-end", marginTop: 6 }}>
                <button onClick={closeModal}>Cancel</button>
                <button onClick={submit}>{mode === "create" ? "Create" : "Save"}</button>
              </div>

              <div style={{ color: "#666", fontSize: 12 }}>
                Nota: “Deactivate” hace soft-delete (is_active=false). Editar permite cambiar parent_id (evita self-parent).
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
    </AppShell>
  );
}
