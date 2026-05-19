import { useEffect, useMemo, useRef, useState } from "react";
import type { KeyboardEvent } from "react";
import { Pencil, Power, Save, UserPlus, X } from "lucide-react";

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

function errMsg(e: unknown) {
  return e instanceof Error ? e.message : String(e);
}

function fmtDate(v?: string | null) {
  if (!v) return "";

  const d = new Date(v);

  if (Number.isNaN(d.getTime())) return v;

  return d.toLocaleString();
}

function activeBadgeClassName(isActive: boolean) {
  return isActive
    ? "border-green-200 bg-green-50 text-green-700"
    : "border-red-200 bg-red-50 text-red-700";
}

function roleBadgeClassName(role?: string | null) {
  const value = (role || "").toLowerCase();

  if (value.includes("admin")) {
    return "border-purple-200 bg-purple-50 text-purple-700";
  }

  if (value.includes("manager")) {
    return "border-blue-200 bg-blue-50 text-blue-700";
  }

  return "border-zinc-200 bg-zinc-50 text-zinc-700";
}

function authBadgeClassName(authProvider?: string | null) {
  const value = (authProvider || "").toLowerCase();

  if (value === "local") {
    return "border-zinc-200 bg-zinc-50 text-zinc-700";
  }

  return "border-blue-200 bg-blue-50 text-blue-700";
}

export default function UsersPage() {
  const [usernameFilter, setUsernameFilter] = useState("");
  const [fullNameFilter, setFullNameFilter] = useState("");
  const [emailFilter, setEmailFilter] = useState("");
  const [roleFilter, setRoleFilter] = useState("");
  const [departmentFilter, setDepartmentFilter] = useState("");
  const [activeFilter, setActiveFilter] = useState<
    "active" | "inactive" | "all"
  >("active");

  const [page, setPage] = useState(1);
  const [pageSize] = useState(25);

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

  const [createOpen, setCreateOpen] = useState(false);

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

  const [editingId, setEditingId] = useState<number | null>(null);
  const [editDraft, setEditDraft] = useState<UserUpdateIn>({});

  const qCombined = useMemo(() => {
    return [
      usernameFilter.trim(),
      fullNameFilter.trim(),
      emailFilter.trim(),
      roleFilter.trim(),
      departmentFilter.trim(),
    ]
      .filter(Boolean)
      .join(" ");
  }, [
    usernameFilter,
    fullNameFilter,
    emailFilter,
    roleFilter,
    departmentFilter,
  ]);

  const includeInactive = useMemo(() => activeFilter !== "active", [
    activeFilter,
  ]);

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

      if (activeFilter === "inactive") {
        items = items.filter((u) => !u.is_active);
      }

      setRows(items);
      setMeta(meta);
      setPage(p);
    } catch (e: unknown) {
      setErr(errMsg(e));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load(1);

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const debounceRef = useRef<number | null>(null);
  const didMountRef = useRef(false);

  useEffect(() => {
    if (!didMountRef.current) {
      didMountRef.current = true;
      return;
    }

    if (debounceRef.current) {
      window.clearTimeout(debounceRef.current);
    }

    debounceRef.current = window.setTimeout(() => {
      void load(1);
    }, 300);

    return () => {
      if (debounceRef.current) {
        window.clearTimeout(debounceRef.current);
      }
    };

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [qCombined, activeFilter]);

  function onFilterKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter") {
      if (debounceRef.current) {
        window.clearTimeout(debounceRef.current);
      }

      void load(1);
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

    if (
      !payload.username ||
      !payload.full_name ||
      !payload.role ||
      !payload.password_hash
    ) {
      setErr("Faltan campos obligatorios: username, full_name, role, password.");
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
    } catch (e: unknown) {
      setErr(errMsg(e));
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

    if (editDraft.full_name !== undefined) {
      body.full_name =
        (editDraft.full_name ?? "").toString().trim() || null;
    }

    if (editDraft.email !== undefined) {
      body.email = (editDraft.email ?? "").toString().trim() || null;
    }

    if (editDraft.role !== undefined) {
      body.role = (editDraft.role ?? "").toString().trim() || null;
    }

    if (editDraft.department !== undefined) {
      body.department =
        (editDraft.department ?? "").toString().trim() || null;
    }

    if (editDraft.is_active !== undefined) {
      body.is_active = !!editDraft.is_active;
    }

    if (editDraft.auth_provider !== undefined) {
      body.auth_provider =
        (editDraft.auth_provider ?? "").toString().trim() || null;
    }

    if (editDraft.password_hash && editDraft.password_hash.trim()) {
      body.password_hash = editDraft.password_hash.trim();
    }

    try {
      await apiJson<UserOut>("PATCH", `/api/users/${userId}`, body);
      cancelEdit();
      await load(page);
    } catch (e: unknown) {
      setErr(errMsg(e));
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
    } catch (e: unknown) {
      setErr(errMsg(e));
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

    if (debounceRef.current) {
      window.clearTimeout(debounceRef.current);
    }

    window.setTimeout(() => {
      void load(1);
    }, 0);
  }

  return (
    <AppShell
      title="Users"
      subtitle="Manage application users, roles and access status."
      actions={
        <div className="flex items-center gap-2">
          <Button
            type="button"
            variant="outline"
            onClick={resetFilters}
            disabled={loading}
          >
            Reset filters
          </Button>

          <Button
            type="button"
            variant="primary"
            onClick={openCreateModal}
            disabled={loading}
          >
            <span className="inline-flex items-center gap-2">
              <UserPlus className="h-4 w-4" />
              New user
            </span>
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

        <div className="overflow-hidden rounded-2xl border border-zinc-200 bg-white shadow-sm">


          <div className="flex max-h-[750px] flex-col">
            <div className="relative flex-1 overflow-auto bg-white">
              <table className="min-w-[1100px] border-separate border-spacing-0 [table-layout:fixed]">
                <colgroup>
                  <col className="w-[70px]" />   {/* ID */}
                  <col className="w-[150px]" />  {/* Username */}
                  <col className="w-[250px]" />  {/* Full name */}
                  <col className="w-[300px]" />  {/* Email */}
                  <col className="w-[120px]" />  {/* Role */}
                  <col className="w-[150px]" />   {/* Dept */}
                  <col className="w-[150px]" />  {/* Active */}
                  <col className="w-[300px]" />  {/* Actions */}
                </colgroup>

                <thead className="bg-zinc-50">
                  <tr>
                    {[
                      "ID",
                      "Username",
                      "Full name",
                      "Email",
                      "Role",
                      "Dept",
                      "Active",
                      "Actions",
                    ].map((h) => (
                      <th
                        key={h}
                        className="sticky top-0 z-30 whitespace-nowrap border-b border-zinc-200 bg-zinc-50 px-3 py-3 text-center text-sm font-bold text-zinc-800"
                      >
                        {h}
                      </th>
                    ))}
                  </tr>

                  <tr>
                    <th className="sticky top-[45px] z-20 border-b border-zinc-200 bg-white px-3 py-2" />

                    <th className="sticky top-[45px] z-20 border-b border-zinc-200 bg-white px-3 py-2">
                      <Input
                        value={usernameFilter}
                        onChange={(e) => setUsernameFilter(e.target.value)}
                        onKeyDown={onFilterKeyDown}
                        placeholder="Username…"
                      />
                    </th>

                    <th className="sticky top-[45px] z-20 border-b border-zinc-200 bg-white px-3 py-2">
                      <Input
                        value={fullNameFilter}
                        onChange={(e) => setFullNameFilter(e.target.value)}
                        onKeyDown={onFilterKeyDown}
                        placeholder="Full name…"
                      />
                    </th>

                    <th className="sticky top-[45px] z-20 border-b border-zinc-200 bg-white px-3 py-2">
                      <Input
                        value={emailFilter}
                        onChange={(e) => setEmailFilter(e.target.value)}
                        onKeyDown={onFilterKeyDown}
                        placeholder="Email…"
                      />
                    </th>

                    <th className="sticky top-[45px] z-20 border-b border-zinc-200 bg-white px-3 py-2">
                      <Input
                        value={roleFilter}
                        onChange={(e) => setRoleFilter(e.target.value)}
                        onKeyDown={onFilterKeyDown}
                        placeholder="Role…"
                      />
                    </th>

                    <th className="sticky top-[45px] z-20 border-b border-zinc-200 bg-white px-3 py-2">
                      <Input
                        value={departmentFilter}
                        onChange={(e) =>
                          setDepartmentFilter(e.target.value)
                        }
                        onKeyDown={onFilterKeyDown}
                        placeholder="Dept…"
                      />
                    </th>

                    <th className="sticky top-[45px] z-20 border-b border-zinc-200 bg-white px-3 py-2">
                      <select
                        className="h-10 w-full rounded-xl border border-zinc-200 bg-white px-3 text-sm text-zinc-900 outline-none focus:border-zinc-500"
                        value={activeFilter}
                        onChange={(e) =>
                          setActiveFilter(
                            e.target.value as "active" | "inactive" | "all"
                          )
                        }
                      >
                        <option value="active">Active</option>
                        <option value="inactive">Inactive</option>
                        <option value="all">All</option>
                      </select>
                    </th>

                    <th className="sticky top-[45px] z-20 border-b border-zinc-200 bg-white px-3 py-2">
                      <div className="flex w-full justify-center items-center gap-2">
                        <Button
                          type="button"
                          variant="outline"
                          onClick={resetFilters}
                          disabled={loading}
                        >
                          Reset
                        </Button>

                        <Button
                          type="button"
                          variant="primary"
                          onClick={openCreateModal}
                          disabled={loading}
                        >
                          <span className="inline-flex items-center gap-2">
                            <UserPlus className="h-4 w-4" />
                          </span>
                        </Button>
                      </div>
                    </th>
                  </tr>
                </thead>

                <tbody>
                  {rows.map((u) => {
                    const editing = editingId === u.id;

                    return (
                      <tr key={u.id} className="align-middle hover:bg-zinc-50">
                        <td className="border-b border-zinc-100 px-3 py-3 text-center align-middle text-sm">
                          <span className="mx-auto inline-flex w-fit items-center rounded-full bg-blue-900 px-2 py-1 text-xs font-semibold text-white">
                            #{u.id}
                          </span>
                        </td>

                        <td className="text-center border-b border-zinc-100 px-3 py-3 text-sm font-medium text-zinc-900">
                          {u.username}
                        </td>

                        <td className="text-center border-b border-zinc-100 px-3 py-3 text-sm text-zinc-900">
                          {editing ? (
                            <input
                              value={(editDraft.full_name ?? "") as string}
                              onChange={(e) =>
                                setEditDraft((d) => ({
                                  ...d,
                                  full_name: e.target.value,
                                }))
                              }
                              className="h-9 w-56 rounded-lg border border-zinc-200 bg-white px-3 text-sm outline-none focus:border-zinc-500"
                            />
                          ) : (
                            u.full_name
                          )}
                        </td>

                        <td className="text-center border-b border-zinc-100 px-3 py-3 text-sm text-zinc-700">
                          {editing ? (
                            <input
                              value={(editDraft.email ?? "") as string}
                              onChange={(e) =>
                                setEditDraft((d) => ({
                                  ...d,
                                  email: e.target.value,
                                }))
                              }
                              className="h-9 w-64 rounded-lg border border-zinc-200 bg-white px-3 text-sm outline-none focus:border-zinc-500"
                            />
                          ) : (
                            u.email || "—"
                          )}
                        </td>

                        <td className="border-b border-zinc-100 px-3 py-3 text-center align-middle text-sm">
                          {editing ? (
                            <input
                              value={(editDraft.role ?? "") as string}
                              onChange={(e) =>
                                setEditDraft((d) => ({
                                  ...d,
                                  role: e.target.value,
                                }))
                              }
                              className="h-9 w-32 rounded-lg border border-zinc-200 bg-white px-3 text-sm outline-none focus:border-zinc-500"
                            />
                          ) : (
                            <span
                              className={`inline-flex rounded-full border px-2 py-1 text-xs font-semibold ${roleBadgeClassName(
                                u.role
                              )}`}
                            >
                              {u.role}
                            </span>
                          )}
                        </td>

                        <td className="text-center border-b border-zinc-100 px-3 py-3 text-sm text-zinc-900">
                          {editing ? (
                            <input
                              value={(editDraft.department ?? "") as string}
                              onChange={(e) =>
                                setEditDraft((d) => ({
                                  ...d,
                                  department: e.target.value,
                                }))
                              }
                              className="h-9 w-32 rounded-lg border border-zinc-200 bg-white px-3 text-sm outline-none focus:border-zinc-500"
                            />
                          ) : (
                            u.department || "—"
                          )}
                        </td>

                        <td className="border-b border-zinc-100 px-3 py-3 text-center align-middle text-sm">
                          {editing ? (
                            <label className="inline-flex items-center gap-2 text-sm text-zinc-700">
                              <input
                                type="checkbox"
                                className="h-4 w-4 rounded border-zinc-300"
                                checked={!!editDraft.is_active}
                                onChange={(e) =>
                                  setEditDraft((d) => ({
                                    ...d,
                                    is_active: e.target.checked,
                                  }))
                                }
                              />
                              {editDraft.is_active ? "Active" : "Inactive"}
                            </label>
                          ) : (
                            <span
                              className={`inline-flex rounded-full border px-2 py-1 text-xs font-semibold ${activeBadgeClassName(
                                u.is_active
                              )}`}
                            >
                              {u.is_active ? "Active" : "Inactive"}
                            </span>
                          )}
                        </td>


                        <td className="border-b border-zinc-100 px-3 py-3 text-sm">
                          {!editing ? (
                            <div className="flex items-center justify-center gap-2">
                              <button
                                type="button"
                                onClick={() => startEdit(u)}
                                disabled={loading}
                                title="Edit user"
                                className="flex h-9 w-9 items-center justify-center rounded-lg border border-zinc-300 bg-white text-zinc-700 hover:bg-zinc-50 disabled:cursor-not-allowed disabled:opacity-50"
                              >
                                <Pencil className="h-4 w-4" />
                                <span className="sr-only">Edit user</span>
                              </button>

                              <button
                                type="button"
                                onClick={() => deactivate(u.id)}
                                disabled={loading || !u.is_active}
                                title="Deactivate user"
                                className="flex h-9 w-9 items-center justify-center rounded-lg border border-red-600 bg-red-600 text-white hover:bg-red-700 disabled:cursor-not-allowed disabled:opacity-50"
                              >
                                <Power className="h-4 w-4" />
                                <span className="sr-only">
                                  Deactivate user
                                </span>
                              </button>
                            </div>
                          ) : (
                            <div className="flex flex-wrap items-center justify-center gap-2">
                              <input
                                value={
                                  (editDraft.password_hash ?? "") as string
                                }
                                onChange={(e) =>
                                  setEditDraft((d) => ({
                                    ...d,
                                    password_hash: e.target.value,
                                  }))
                                }
                                placeholder="Password optional"
                                className="h-9 w-44 rounded-lg border border-zinc-200 bg-white px-3 text-sm outline-none focus:border-zinc-500"
                              />

                              <button
                                type="button"
                                onClick={() => saveEdit(u.id)}
                                disabled={loading}
                                title="Save user"
                                className="flex h-9 w-9 items-center justify-center rounded-lg border border-green-600 bg-green-600 text-white hover:bg-green-700 disabled:cursor-not-allowed disabled:opacity-50"
                              >
                                <Save className="h-4 w-4" />
                                <span className="sr-only">Save user</span>
                              </button>

                              <button
                                type="button"
                                onClick={cancelEdit}
                                disabled={loading}
                                title="Cancel edit"
                                className="flex h-9 w-9 items-center justify-center rounded-lg border border-zinc-300 bg-white text-zinc-700 hover:bg-zinc-50 disabled:cursor-not-allowed disabled:opacity-50"
                              >
                                <X className="h-4 w-4" />
                                <span className="sr-only">Cancel edit</span>
                              </button>
                            </div>
                          )}
                        </td>
                      </tr>
                    );
                  })}

                  {!loading && rows.length === 0 && (
                    <tr>
                      <td
                        colSpan={10}
                        className="px-3 py-8 text-center text-sm text-zinc-600"
                      >
                        No results
                      </td>
                    </tr>
                  )}

                  {loading && (
                    <tr>
                      <td
                        colSpan={10}
                        className="px-3 py-8 text-center text-sm text-zinc-600"
                      >
                        Loading users…
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            <div className="border-t border-zinc-200 bg-zinc-50 px-4 py-3">
              <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                <div className="text-sm text-zinc-600">
                  Total{" "}
                  <span className="font-semibold text-zinc-900">
                    {meta.total}
                  </span>{" "}
                  • Page{" "}
                  <span className="font-semibold text-zinc-900">
                    {meta.page}
                  </span>{" "}
                  /{" "}
                  <span className="font-semibold text-zinc-900">
                    {pages}
                  </span>{" "}
                  • Size{" "}
                  <span className="font-semibold text-zinc-900">
                    {meta.pageSize}
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => load(meta.page - 1)}
                    disabled={loading || meta.page <= 1}
                  >
                    Prev
                  </Button>

                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => load(meta.page + 1)}
                    disabled={loading || meta.page >= pages}
                  >
                    Next
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>

        {createOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
            <div className="w-full max-w-3xl rounded-2xl border border-zinc-200 bg-white p-5 shadow-xl">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="text-base font-semibold text-zinc-900">
                    Create user
                  </div>
                  <div className="mt-1 text-xs text-zinc-500">
                    Fill in the required user access fields.
                  </div>
                </div>

                <Button
                  type="button"
                  variant="ghost"
                  onClick={closeCreateModal}
                  disabled={loading}
                >
                  Close
                </Button>
              </div>

              <div className="mt-4 grid gap-3 md:grid-cols-3">
                <Input
                  value={newUser.username}
                  onChange={(e) =>
                    setNewUser((u) => ({
                      ...u,
                      username: e.target.value,
                    }))
                  }
                  placeholder="Username *"
                />

                <Input
                  value={newUser.full_name}
                  onChange={(e) =>
                    setNewUser((u) => ({
                      ...u,
                      full_name: e.target.value,
                    }))
                  }
                  placeholder="Full name *"
                />

                <Input
                  value={newUser.email ?? ""}
                  onChange={(e) =>
                    setNewUser((u) => ({
                      ...u,
                      email: e.target.value,
                    }))
                  }
                  placeholder="Email"
                />

                <Input
                  value={newUser.role}
                  onChange={(e) =>
                    setNewUser((u) => ({
                      ...u,
                      role: e.target.value,
                    }))
                  }
                  placeholder="Role *"
                />

                <Input
                  value={newUser.department ?? ""}
                  onChange={(e) =>
                    setNewUser((u) => ({
                      ...u,
                      department: e.target.value,
                    }))
                  }
                  placeholder="Department"
                />

                <Input
                  value={newUser.auth_provider ?? "local"}
                  onChange={(e) =>
                    setNewUser((u) => ({
                      ...u,
                      auth_provider: e.target.value,
                    }))
                  }
                  placeholder="Auth provider"
                />

                <Input
                  value={newUser.password_hash}
                  onChange={(e) =>
                    setNewUser((u) => ({
                      ...u,
                      password_hash: e.target.value,
                    }))
                  }
                  placeholder="Password *"
                />

                <label className="flex items-center gap-2 text-sm text-zinc-700">
                  <input
                    type="checkbox"
                    className="h-4 w-4 rounded border-zinc-300"
                    checked={!!newUser.is_active}
                    onChange={(e) =>
                      setNewUser((u) => ({
                        ...u,
                        is_active: e.target.checked,
                      }))
                    }
                  />
                  Active
                </label>
              </div>

              {err && (
                <div className="mt-3 rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                  Error: {err}
                </div>
              )}

              <div className="mt-4 flex items-center justify-end gap-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={closeCreateModal}
                  disabled={loading}
                >
                  Cancel
                </Button>

                <Button
                  type="button"
                  variant="primary"
                  onClick={onCreate}
                  disabled={loading}
                >
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