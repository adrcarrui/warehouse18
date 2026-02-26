import { useEffect, useMemo, useRef, useState } from "react";
import { apiGet, apiJson } from "../api";
import type { PageMeta, PageOut } from "../api";
import { AppShell } from "../app/AppShell";

import { Button } from "../ui/Button";
import { Input } from "../ui/Input";

type UserOut = {
  id: number;
  username: string;
  full_name: string;
  email?: string | null;
  role: string;
  department?: string | null;
  is_active: boolean;
  auth_provider: string;
  last_login_at?: string | null;
  created_at: string;
  updated_at: string;
};

type UserCreateIn = {
  username: string;
  full_name: string;
  email?: string | null;
  role: string;
  department?: string | null;
  is_active?: boolean;
  password_hash: string;
  auth_provider?: string;
};

type UserUpdateIn = Partial<{
  full_name: string | null;
  email: string | null;
  role: string | null;
  department: string | null;
  is_active: boolean | null;
  password_hash: string | null;
  auth_provider: string | null;
}>;

function fmtDate(v?: string | null) {
  if (!v) return "";
  const d = new Date(v);
  if (Number.isNaN(d.getTime())) return v;
  return d.toLocaleString();
}

export default function UsersPage() {
  // Column filters (Locations-style)
  const [usernameFilter, setUsernameFilter] = useState("");
  const [fullNameFilter, setFullNameFilter] = useState("");
  const [emailFilter, setEmailFilter] = useState("");
  const [roleFilter, setRoleFilter] = useState("");
  const [departmentFilter, setDepartmentFilter] = useState("");
  const [activeFilter, setActiveFilter] = useState<"active" | "inactive" | "all">("active");

  // paging
  const [page, setPage] = useState(1);
  const [pageSize] = useState(25);

  // data
  const [rows, setRows] = useState<UserOut[]>([]);
  const [meta, setMeta] = useState<PageMeta>({
    page: 1,
    pageSize: 25,
    total: 0,
    pages: 0,
    link: null,
  });

  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  // create modal
  const [createOpen, setCreateOpen] = useState(false);

  // create form
  const [newUser, setNewUser] = useState<UserCreateIn>({
    username: "",
    full_name: "",
    email: "",
    role: "User",
    department: "",
    password_hash: "",
    auth_provider: "local",
    is_active: true,
  });

  // edit
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editDraft, setEditDraft] = useState<UserUpdateIn>({});

  const qCombined = useMemo(() => {
    return [usernameFilter.trim(), fullNameFilter.trim(), emailFilter.trim(), roleFilter.trim(), departmentFilter.trim()]
      .filter(Boolean)
      .join(" ");
  }, [usernameFilter, fullNameFilter, emailFilter, roleFilter, departmentFilter]);

  const includeInactive = useMemo(() => activeFilter !== "active", [activeFilter]);

  const pages = useMemo(() => {
    const ps = meta.pageSize || pageSize || 25;
    const t = meta.total || 0;
    const computed = Math.max(1, Math.ceil(t / ps));
    return meta.pages && meta.pages > 0 ? meta.pages : computed;
  }, [meta.pages, meta.pageSize, meta.total, pageSize]);

  async function load(p: number) {
    setLoading(true);
    setErr(null);
    try {
      const { data, meta } = await apiGet<PageOut<UserOut>>("/api/users", {
        q: qCombined || undefined,
        include_inactive: includeInactive,
        page: p,
        page_size: pageSize,
      });

      let items = data.items;

      // si el usuario pide SOLO inactivos, filtramos client-side
      if (activeFilter === "inactive") {
        items = items.filter((u) => !u.is_active);
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

  // Initial load (IMPORTANT)
  useEffect(() => {
    load(1);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Debounced auto-search (only after first mount)
  const debounceRef = useRef<number | null>(null);
  const didMountRef = useRef(false);

  useEffect(() => {
    // avoid double-load on first render (we already did load(1) in the effect above)
    if (!didMountRef.current) {
      didMountRef.current = true;
      return;
    }

    if (debounceRef.current) window.clearTimeout(debounceRef.current);

    debounceRef.current = window.setTimeout(() => {
      load(1);
    }, 300);

    return () => {
      if (debounceRef.current) window.clearTimeout(debounceRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [qCombined, activeFilter]);

  function onFilterKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter") {
      if (debounceRef.current) window.clearTimeout(debounceRef.current);
      load(1);
    }
  }

  function openCreateModal() {
    setErr(null);
    setCreateOpen(true);
  }

  function closeCreateModal() {
    setCreateOpen(false);
  }

  async function onCreate() {
    setErr(null);

    const payload: UserCreateIn = {
      username: newUser.username.trim(),
      full_name: newUser.full_name.trim(),
      email: (newUser.email ?? "").trim() || null,
      role: newUser.role.trim(),
      department: (newUser.department ?? "").trim() || null,
      password_hash: newUser.password_hash.trim(),
      auth_provider: (newUser.auth_provider ?? "local").trim() || "local",
      is_active: !!newUser.is_active,
    };

    if (!payload.username || !payload.full_name || !payload.role || !payload.password_hash) {
      setErr("Faltan campos obligatorios: username, full_name, role, password_hash.");
      return;
    }

    setLoading(true);
    try {
      await apiJson<UserOut>("POST", "/api/users", payload);

      setNewUser((u) => ({
        ...u,
        username: "",
        full_name: "",
        email: "",
        department: "",
        password_hash: "",
      }));

      setCreateOpen(false);
      await load(1);
    } catch (e: any) {
      setErr(e?.message ?? String(e));
    } finally {
      setLoading(false);
    }
  }

  function startEdit(u: UserOut) {
    setEditingId(u.id);
    setEditDraft({
      full_name: u.full_name,
      email: u.email ?? "",
      role: u.role,
      department: u.department ?? "",
      is_active: u.is_active,
      auth_provider: u.auth_provider,
      password_hash: "",
    });
  }

  function cancelEdit() {
    setEditingId(null);
    setEditDraft({});
  }

  async function saveEdit(userId: number) {
    setErr(null);
    setLoading(true);

    const body: UserUpdateIn = {};
    if (editDraft.full_name !== undefined) body.full_name = (editDraft.full_name ?? "").toString().trim() || null;
    if (editDraft.email !== undefined) body.email = (editDraft.email ?? "").toString().trim() || null;
    if (editDraft.role !== undefined) body.role = (editDraft.role ?? "").toString().trim() || null;
    if (editDraft.department !== undefined) body.department = (editDraft.department ?? "").toString().trim() || null;
    if (editDraft.is_active !== undefined) body.is_active = !!editDraft.is_active;
    if (editDraft.auth_provider !== undefined)
      body.auth_provider = (editDraft.auth_provider ?? "").toString().trim() || null;

    if (editDraft.password_hash && editDraft.password_hash.trim()) {
      body.password_hash = editDraft.password_hash.trim();
    }

    try {
      await apiJson<UserOut>("PATCH", `/api/users/${userId}`, body);
      cancelEdit();
      await load(page);
    } catch (e: any) {
      setErr(e?.message ?? String(e));
    } finally {
      setLoading(false);
    }
  }

  async function deactivate(userId: number) {
    setErr(null);
    setLoading(true);
    try {
      await apiJson<{ status: string }>("DELETE", `/api/users/${userId}`);
      await load(page);
    } catch (e: any) {
      setErr(e?.message ?? String(e));
    } finally {
      setLoading(false);
    }
  }

  function resetFilters() {
    setUsernameFilter("");
    setFullNameFilter("");
    setEmailFilter("");
    setRoleFilter("");
    setDepartmentFilter("");
    setActiveFilter("active");
    if (debounceRef.current) window.clearTimeout(debounceRef.current);
    load(1);
  }

  return (
    <AppShell
      title="Users"
      subtitle="Manage access and roles"
      actions={
        <div className="flex items-center gap-2">
          <Button type="button" variant="outline" onClick={resetFilters} disabled={loading}>
            Reset
          </Button>
          <Button type="button" variant="primary" onClick={openCreateModal} disabled={loading}>
            + New user
          </Button>
        </div>
      }
    >
      <div className="space-y-4">
        {err && (
          <div className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">Error: {err}</div>
        )}

        {/* Table + Pagination (Locations-style) */}
        <div className="rounded-xl border border-zinc-200 bg-white">
          <div className="flex max-h-[750px] flex-col">
            {/* Scroll area */}
            <div className="relative flex-1 overflow-auto bg-white">
              <table className="min-w-full border-separate border-spacing-0">
                <thead className="bg-zinc-50">
                  {/* Row 1: Titles */}
                  <tr>
                    {[
                      "ID",
                      "Username",
                      "Full name",
                      "Email",
                      "Role",
                      "Dept",
                      "Active",
                      "Auth",
                      "Last login",
                      "Actions",
                    ].map((h) => (
                      <th
                        key={h}
                        className="whitespace-nowrap border-b border-zinc-200 bg-zinc-50 px-3 py-2 text-left text-xs font-semibold text-zinc-700"
                      >
                        {h}
                      </th>
                    ))}
                  </tr>

                  {/* Row 2: Filters */}
                  <tr>
                    <th className="border-b border-zinc-200 bg-white px-3 py-2" />

                    <th className="border-b border-zinc-200 bg-white px-3 py-2">
                      <Input
                        value={usernameFilter}
                        onChange={(e) => setUsernameFilter(e.target.value)}
                        onKeyDown={onFilterKeyDown}
                        placeholder="Filter username…"
                      />
                    </th>

                    <th className="border-b border-zinc-200 bg-white px-3 py-2">
                      <Input
                        value={fullNameFilter}
                        onChange={(e) => setFullNameFilter(e.target.value)}
                        onKeyDown={onFilterKeyDown}
                        placeholder="Filter name…"
                      />
                    </th>

                    <th className="border-b border-zinc-200 bg-white px-3 py-2">
                      <Input
                        value={emailFilter}
                        onChange={(e) => setEmailFilter(e.target.value)}
                        onKeyDown={onFilterKeyDown}
                        placeholder="Filter email…"
                      />
                    </th>

                    <th className="border-b border-zinc-200 bg-white px-3 py-2">
                      <Input
                        value={roleFilter}
                        onChange={(e) => setRoleFilter(e.target.value)}
                        onKeyDown={onFilterKeyDown}
                        placeholder="Filter role…"
                      />
                    </th>

                    <th className="border-b border-zinc-200 bg-white px-3 py-2">
                      <Input
                        value={departmentFilter}
                        onChange={(e) => setDepartmentFilter(e.target.value)}
                        onKeyDown={onFilterKeyDown}
                        placeholder="Filter dept…"
                      />
                    </th>

                    <th className="border-b border-zinc-200 bg-white px-3 py-2">
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

                    <th className="border-b border-zinc-200 bg-white px-3 py-2" />
                    <th className="border-b border-zinc-200 bg-white px-3 py-2" />
                    <th className="border-b border-zinc-200 bg-white px-3 py-2" />
                  </tr>
                </thead>

                <tbody>
                  {rows.map((u) => {
                    const editing = editingId === u.id;

                    return (
                      <tr key={u.id} className="hover:bg-zinc-50 align-top">
                        <td className="border-b border-zinc-100 px-3 py-2 text-sm font-medium text-black">{u.id}</td>
                        <td className="border-b border-zinc-100 px-3 py-2 text-sm text-black">{u.username}</td>

                        <td className="border-b border-zinc-100 px-3 py-2 text-sm text-black">
                          {editing ? (
                            <input
                              value={(editDraft.full_name ?? "") as any}
                              onChange={(e) => setEditDraft((d) => ({ ...d, full_name: e.target.value }))}
                              className="h-9 w-56 rounded-lg border border-zinc-200 bg-white px-3 text-sm"
                            />
                          ) : (
                            u.full_name
                          )}
                        </td>

                        <td className="border-b border-zinc-100 px-3 py-2 text-sm text-black">
                          {editing ? (
                            <input
                              value={(editDraft.email ?? "") as any}
                              onChange={(e) => setEditDraft((d) => ({ ...d, email: e.target.value }))}
                              className="h-9 w-64 rounded-lg border border-zinc-200 bg-white px-3 text-sm"
                            />
                          ) : (
                            u.email ?? ""
                          )}
                        </td>

                        <td className="border-b border-zinc-100 px-3 py-2 text-sm text-black">
                          {editing ? (
                            <input
                              value={(editDraft.role ?? "") as any}
                              onChange={(e) => setEditDraft((d) => ({ ...d, role: e.target.value }))}
                              className="h-9 w-32 rounded-lg border border-zinc-200 bg-white px-3 text-sm"
                            />
                          ) : (
                            u.role
                          )}
                        </td>

                        <td className="border-b border-zinc-100 px-3 py-2 text-sm text-black">
                          {editing ? (
                            <input
                              value={(editDraft.department ?? "") as any}
                              onChange={(e) => setEditDraft((d) => ({ ...d, department: e.target.value }))}
                              className="h-9 w-32 rounded-lg border border-zinc-200 bg-white px-3 text-sm"
                            />
                          ) : (
                            u.department ?? ""
                          )}
                        </td>

                        <td className="border-b border-zinc-100 px-3 py-2 text-sm text-black">
                          {editing ? (
                            <label className="inline-flex items-center gap-2 text-sm text-zinc-700">
                              <input
                                type="checkbox"
                                className="h-4 w-4 rounded border-zinc-300"
                                checked={!!editDraft.is_active}
                                onChange={(e) => setEditDraft((d) => ({ ...d, is_active: e.target.checked }))}
                              />
                              {editDraft.is_active ? "yes" : "no"}
                            </label>
                          ) : (
                            u.is_active ? "yes" : "no"
                          )}
                        </td>

                        <td className="border-b border-zinc-100 px-3 py-2 text-sm text-black">
                          {editing ? (
                            <input
                              value={(editDraft.auth_provider ?? "") as any}
                              onChange={(e) => setEditDraft((d) => ({ ...d, auth_provider: e.target.value }))}
                              className="h-9 w-28 rounded-lg border border-zinc-200 bg-white px-3 text-sm"
                            />
                          ) : (
                            u.auth_provider
                          )}
                        </td>

                        <td className="border-b border-zinc-100 px-3 py-2 text-sm text-black">{fmtDate(u.last_login_at)}</td>

                        <td className="border-b border-zinc-100 px-3 py-2 text-sm">
                          <div className="flex flex-wrap gap-2">
                            {!editing ? (
                              <>
                                <Button type="button" variant="outline" size="sm" onClick={() => startEdit(u)} disabled={loading}>
                                  Edit
                                </Button>
                                <Button
                                  type="button"
                                  variant="danger"
                                  size="sm"
                                  onClick={() => deactivate(u.id)}
                                  disabled={loading || !u.is_active}
                                >
                                  Deactivate
                                </Button>
                              </>
                            ) : (
                              <>
                                <input
                                  value={(editDraft.password_hash ?? "") as any}
                                  onChange={(e) => setEditDraft((d) => ({ ...d, password_hash: e.target.value }))}
                                  placeholder="password_hash (optional)"
                                  className="h-9 w-56 rounded-lg border border-zinc-200 bg-white px-3 text-sm"
                                />
                                <Button type="button" variant="primary" size="sm" onClick={() => saveEdit(u.id)} disabled={loading}>
                                  Save
                                </Button>
                                <Button type="button" variant="ghost" size="sm" onClick={cancelEdit} disabled={loading}>
                                  Cancel
                                </Button>
                              </>
                            )}
                          </div>
                        </td>
                      </tr>
                    );
                  })}

                  {!loading && rows.length === 0 && (
                    <tr>
                      <td colSpan={10} className="px-3 py-6 text-sm text-zinc-600">
                        No results
                      </td>
                    </tr>
                  )}

                  {loading && (
                    <tr>
                      <td colSpan={10} className="px-3 py-6 text-sm text-zinc-600">
                        Loading…
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            {/* Footer pagination fixed */}
            <div className="border-t border-zinc-200 bg-white px-3 py-2">
              <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                <div className="text-sm text-zinc-600">
                  Total <span className="font-semibold text-zinc-900">{meta.total}</span> • Page{" "}
                  <span className="font-semibold text-zinc-900">{meta.page}</span> /{" "}
                  <span className="font-semibold text-zinc-900">{pages}</span> • Size{" "}
                  <span className="font-semibold text-zinc-900">{meta.pageSize}</span>
                </div>

                <div className="flex items-center gap-2">
                  <Button type="button" onClick={() => load(meta.page - 1)} disabled={loading || meta.page <= 1}>
                    Prev
                  </Button>
                  <Button type="button" onClick={() => load(meta.page + 1)} disabled={loading || meta.page >= pages}>
                    Next
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Create Modal */}
        {createOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
            <div className="w-full max-w-3xl rounded-2xl border border-zinc-200 bg-white p-5 shadow-xl">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="text-sm font-semibold text-zinc-900">Create user</div>
                  <div className="mt-1 text-xs text-zinc-500">username / full_name / role / password_hash</div>
                </div>

                <Button type="button" variant="ghost" onClick={closeCreateModal} disabled={loading}>
                  Close
                </Button>
              </div>

              <div className="mt-4 grid gap-3 md:grid-cols-3">
                <Input
                  value={newUser.username}
                  onChange={(e) => setNewUser((u) => ({ ...u, username: e.target.value }))}
                  placeholder="username *"
                />
                <Input
                  value={newUser.full_name}
                  onChange={(e) => setNewUser((u) => ({ ...u, full_name: e.target.value }))}
                  placeholder="full name *"
                />
                <Input value={newUser.email ?? ""} onChange={(e) => setNewUser((u) => ({ ...u, email: e.target.value }))} placeholder="email" />

                <Input value={newUser.role} onChange={(e) => setNewUser((u) => ({ ...u, role: e.target.value }))} placeholder="role *" />
                <Input value={newUser.department ?? ""} onChange={(e) => setNewUser((u) => ({ ...u, department: e.target.value }))} placeholder="department" />
                <Input
                  value={newUser.auth_provider ?? "local"}
                  onChange={(e) => setNewUser((u) => ({ ...u, auth_provider: e.target.value }))}
                  placeholder="auth_provider"
                />

                <Input
                  value={newUser.password_hash}
                  onChange={(e) => setNewUser((u) => ({ ...u, password_hash: e.target.value }))}
                  placeholder="password_hash *"
                />

                <label className="flex items-center gap-2 text-sm text-zinc-700">
                  <input
                    type="checkbox"
                    className="h-4 w-4 rounded border-zinc-300"
                    checked={!!newUser.is_active}
                    onChange={(e) => setNewUser((u) => ({ ...u, is_active: e.target.checked }))}
                  />
                  active
                </label>
              </div>

              {err && (
                <div className="mt-3 rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">Error: {err}</div>
              )}

              <div className="mt-4 flex items-center justify-end gap-2">
                <Button type="button" variant="outline" onClick={closeCreateModal} disabled={loading}>
                  Cancel
                </Button>
                <Button type="button" variant="primary" onClick={onCreate} disabled={loading}>
                  Create
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}