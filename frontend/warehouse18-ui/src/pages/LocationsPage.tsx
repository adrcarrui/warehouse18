import { useEffect, useMemo, useState } from "react";
import { apiDelete, apiGet, apiPatch, apiPost } from "../api";
import type { PageMeta, PageOut } from "../api";
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

export default function LocationsPage() {
  // Column filters
  const [codeFilter, setCodeFilter] = useState("");
  const [nameFilter, setNameFilter] = useState("");
  const [activeFilter, setActiveFilter] = useState<"active" | "inactive" | "all">("active");

  // paging
  const [page, setPage] = useState(1);
  const [pageSize] = useState(25);

  // data
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

  const includeInactive = activeFilter !== "active";

  const qCombined = useMemo(() => {
    return [codeFilter.trim(), nameFilter.trim()].filter(Boolean).join(" ");
  }, [codeFilter, nameFilter]);

  async function load(p: number) {
    setLoading(true);
    setErr(null);
    try {
      const { data, meta } = await apiGet<PageOut<LocationOut>>("/api/locations", {
        q: qCombined || undefined,
        include_inactive: includeInactive,
        page: p,
        page_size: pageSize,
      });

      // Backend likely only supports include/exclude inactive.
      // If the user explicitly wants ONLY inactive, filter client-side.
      let items = data.items;
      if (activeFilter === "inactive") {
        items = items.filter((x) => !x.is_active);
      }

      setRows(items);
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

  // If your Title row height is not exactly 40px, adjust this number:
  // - try 42 or 44 if you see overlap.
  const FILTER_ROW_TOP = "32px";

const pages = useMemo(() => {
  const ps = meta.pageSize || pageSize || 25;
  const t = meta.total || 0;
  const computed = Math.max(1, Math.ceil(t / ps));
  return meta.pages && meta.pages > 0 ? meta.pages : computed;
}, [meta.pages, meta.pageSize, meta.total, pageSize]);

  return (
    <AppShell
      title="Locations"
      subtitle="Manage locations"
      actions={
        <Button variant="primary" onClick={openCreate}>
          + New location
        </Button>
      }
    >
      <div className="space-y-4">
        {err && (
          <div className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">Error: {err}</div>
        )}

        {/* Table */}
        <div className="rounded-xl border border-zinc-200 bg-white">
          <div className="relative max-h-[750px] overflow-auto bg-white">
            <table className="min-w-full border-separate border-spacing-0 [table-layout:fixed]">
              <thead>
                {/* Row 1: Titles */}
                <tr>
                  {["ID", "Code", "Name", "Active", "Actions"].map((h) => (
                    <th
                      key={h}
                      className="sticky top-0 z-30 whitespace-nowrap border-b border-zinc-200 bg-zinc-50 px-3 py-2 text-left text-xs font-semibold text-zinc-700"
                    >
                      {h}
                    </th>
                  ))}
                </tr>

                {/* Row 2: Filters */}
                <tr>
                  <th
                    className="sticky z-20 border-b border-zinc-200 bg-white px-3 py-2"
                    style={{ top: FILTER_ROW_TOP }}
                  />
                  <th
                    className="sticky z-20 border-b border-zinc-200 bg-white px-3 py-2"
                    style={{ top: FILTER_ROW_TOP }}
                  >
                    <Input value={codeFilter} onChange={(e) => setCodeFilter(e.target.value)} placeholder="Code…" />
                  </th>
                  <th
                    className="sticky z-20 border-b border-zinc-200 bg-white px-3 py-2"
                    style={{ top: FILTER_ROW_TOP }}
                  >
                    <Input value={nameFilter} onChange={(e) => setNameFilter(e.target.value)} placeholder="Name…" />
                  </th>
                  <th
                    className="sticky z-20 border-b border-zinc-200 bg-white px-3 py-2"
                    style={{ top: FILTER_ROW_TOP }}
                  >
                    <select
                      className="h-10 w-full rounded-xl border border-zinc-200 bg-white px-3 text-sm"
                      value={activeFilter}
                      onChange={(e) => setActiveFilter(e.target.value as any)}
                    >
                      <option value="active">Active</option>
                      <option value="inactive">Inactive</option>
                      <option value="all">All</option>
                    </select>
                  </th>
                  <th
                    className="sticky z-20 border-b border-zinc-200 bg-white px-3 py-2"
                    style={{ top: FILTER_ROW_TOP }}
                  >
                    <div className="flex justify-end">
                      <Button variant="outline" onClick={() => load(1)} disabled={loading}>
                        Search
                      </Button>
                    </div>
                  </th>
                </tr>
              </thead>

              <tbody>
                {rows.map((r) => (
                  <tr key={r.id} className="hover:bg-zinc-50">
                    <td className="border-b border-zinc-100 px-3 py-2 text-sm font-medium text-black">{r.id}</td>
                    <td className="border-b border-zinc-100 px-3 py-2 text-sm text-black">{r.code}</td>
                    <td className="border-b border-zinc-100 px-3 py-2 text-sm text-black">{r.name}</td>
                    <td className="border-b border-zinc-100 px-3 py-2 text-sm text-black">{r.is_active ? "yes" : "no"}</td>
                    <td className="border-b border-zinc-100 px-3 py-2 text-sm text-black">
                      <div className="flex flex-wrap gap-2">
                        <Button variant="outline" size="sm" onClick={() => openEdit(r)}>
                          Edit
                        </Button>
                        <Button variant="danger" size="sm" onClick={() => deactivate(r)} disabled={!r.is_active}>
                          Deactivate
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}

                {!loading && rows.length === 0 && (
                  <tr>
                    <td colSpan={5} className="px-3 py-6 text-sm text-zinc-600">
                      No results
                    </td>
                  </tr>
                )}

                {loading && (
                  <tr>
                    <td colSpan={5} className="px-3 py-6 text-sm text-zinc-600">
                      Loading…
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Pagination (bottom) */}
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <div className="text-sm text-zinc-600">
              Total <span className="font-semibold text-zinc-900">{meta.total}</span> • Page{" "}
              <span className="font-semibold text-zinc-900">{meta.page}</span> /{" "}
              <span className="font-semibold text-zinc-900">{pages}</span> • Size{" "}
              <span className="font-semibold text-zinc-900">{meta.pageSize}</span>
            </div>

            <div className="flex items-center gap-2">
              <Button onClick={() => load(meta.page - 1)} disabled={loading || meta.page <= 1}>
                Prev
              </Button>
              <Button onClick={() => load(meta.page + 1)} disabled={loading || meta.page >= pages}>
                Next
              </Button>
          </div>
        </div>

        {/* Modal */}
        {open && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
            <div className="w-full max-w-xl rounded-2xl border border-zinc-200 bg-white p-5 shadow-xl">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="text-sm font-semibold text-zinc-900">
                    {mode === "create" ? "Create location" : `Edit location #${editing?.id}`}
                  </div>
                  <div className="mt-1 text-xs text-zinc-500">code / name / type / parent_id</div>
                </div>

                <Button variant="ghost" onClick={closeModal}>
                  Close
                </Button>
              </div>

              <div className="mt-4 grid gap-3 md:grid-cols-2">
                <Input
                  value={form.code}
                  onChange={(e) => setForm((f) => ({ ...f, code: e.target.value }))}
                  placeholder="code *"
                  disabled={mode === "edit"}
                />
                <Input
                  value={form.type}
                  onChange={(e) => setForm((f) => ({ ...f, type: e.target.value }))}
                  placeholder="type *"
                />
                <div className="md:col-span-2">
                  <Input
                    value={form.name}
                    onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                    placeholder="name *"
                  />
                </div>
                <Input
                  value={form.parent_id}
                  onChange={(e) => setForm((f) => ({ ...f, parent_id: e.target.value }))}
                  placeholder="parent_id (optional)"
                />

                <label className="flex items-center gap-2 text-sm text-zinc-700">
                  <input
                    type="checkbox"
                    className="h-4 w-4 rounded border-zinc-300"
                    checked={!!form.is_active}
                    onChange={(e) => setForm((f) => ({ ...f, is_active: e.target.checked }))}
                  />
                  active
                </label>
              </div>

              {err && (
                <div className="mt-3 rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                  Error: {err}
                </div>
              )}

              <div className="mt-4 flex items-center justify-end gap-2">
                <Button variant="outline" onClick={closeModal}>
                  Cancel
                </Button>
                <Button variant="primary" onClick={submit}>
                  {mode === "create" ? "Create" : "Save"}
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}