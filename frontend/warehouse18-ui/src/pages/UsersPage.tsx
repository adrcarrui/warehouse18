import { useEffect, useMemo, useState } from "react";
import { apiGet, apiJson } from "../api";
import type { PageMeta, PageOut } from "../api";

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
  password_hash: string; // en tu modelo SQLAlchemy parece NOT NULL, mejor no jugar a la ruleta
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
  // filtros
  const [q, setQ] = useState("");
  const [role, setRole] = useState("");
  const [department, setDepartment] = useState("");
  const [status, setStatus] = useState<"active" | "inactive" | "all">("active");

  // paginación
  const [page, setPage] = useState(1);
  const [pageSize] = useState(25);

  // datos
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

  const isActiveParam = useMemo(() => {
    if (status === "all") return undefined; // no filtra
    return status === "active";
  }, [status]);

  async function load(p: number) {
    setLoading(true);
    setErr(null);
    try {
      const { data, meta } = await apiGet<PageOut<UserOut>>("/api/users", {
        q: q.trim() || undefined,
        role: role.trim() || undefined,
        department: department.trim() || undefined,
        is_active: isActiveParam as any, // undefined => omit
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

      // reset mínimo
      setNewUser((u) => ({
        ...u,
        username: "",
        full_name: "",
        email: "",
        department: "",
        password_hash: "",
      }));

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

    // solo si lo rellenan
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

  return (
    <div style={{ padding: 16, fontFamily: "system-ui" }}>
      <h2 style={{ marginTop: 0 }}>Users</h2>

      {/* Create */}
      <div style={{ border: "1px solid #eee", borderRadius: 8, padding: 12, marginBottom: 14 }}>
        <div style={{ fontWeight: 700, marginBottom: 8 }}>Create user</div>

        <div style={{ display: "flex", flexWrap: "wrap", gap: 10, alignItems: "center" }}>
          <input
            value={newUser.username}
            onChange={(e) => setNewUser((u) => ({ ...u, username: e.target.value }))}
            placeholder="username *"
            style={{ padding: 8, width: 180 }}
          />
          <input
            value={newUser.full_name}
            onChange={(e) => setNewUser((u) => ({ ...u, full_name: e.target.value }))}
            placeholder="full name *"
            style={{ padding: 8, width: 260 }}
          />
          <input
            value={newUser.email ?? ""}
            onChange={(e) => setNewUser((u) => ({ ...u, email: e.target.value }))}
            placeholder="email"
            style={{ padding: 8, width: 260 }}
          />
          <input
            value={newUser.role}
            onChange={(e) => setNewUser((u) => ({ ...u, role: e.target.value }))}
            placeholder="role *"
            style={{ padding: 8, width: 140 }}
          />
          <input
            value={newUser.department ?? ""}
            onChange={(e) => setNewUser((u) => ({ ...u, department: e.target.value }))}
            placeholder="department"
            style={{ padding: 8, width: 160 }}
          />
          <input
            value={newUser.auth_provider ?? "local"}
            onChange={(e) => setNewUser((u) => ({ ...u, auth_provider: e.target.value }))}
            placeholder="auth_provider"
            style={{ padding: 8, width: 140 }}
          />
          <input
            value={newUser.password_hash}
            onChange={(e) => setNewUser((u) => ({ ...u, password_hash: e.target.value }))}
            placeholder="password_hash *"
            style={{ padding: 8, width: 220 }}
          />
          <label style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <input
              type="checkbox"
              checked={!!newUser.is_active}
              onChange={(e) => setNewUser((u) => ({ ...u, is_active: e.target.checked }))}
            />
            active
          </label>

          <button onClick={onCreate} disabled={loading}>
            Create
          </button>
        </div>

        {/*<div style={{ marginTop: 8, fontSize: 12, color: "#666" }}>
          Nota: ahora mismo estás metiendo <b>password_hash</b> “a pelo”. Cuando implementes auth de verdad, esto se
          cambia por password y hashing server-side. Humanidad en su máxima expresión.
        </div>*/}
      </div>

      {/* Filters */}
      <div style={{ display: "flex", gap: 12, alignItems: "center", marginBottom: 12, flexWrap: "wrap" }}>
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Search (q)..."
          style={{ padding: 8, width: 280 }}
        />
        <input
          value={role}
          onChange={(e) => setRole(e.target.value)}
          placeholder="role..."
          style={{ padding: 8, width: 140 }}
        />
        <input
          value={department}
          onChange={(e) => setDepartment(e.target.value)}
          placeholder="department..."
          style={{ padding: 8, width: 160 }}
        />
        <label style={{ display: "flex", gap: 8, alignItems: "center" }}>
          status
          <select value={status} onChange={(e) => setStatus(e.target.value as any)} style={{ padding: 6 }}>
            <option value="active">active</option>
            <option value="inactive">inactive</option>
            <option value="all">all</option>
          </select>
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
              <th>Username</th>
              <th>Full name</th>
              <th>Email</th>
              <th>Role</th>
              <th>Dept</th>
              <th>Active</th>
              <th>Auth</th>
              <th>Last login</th>
              <th style={{ width: 220 }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((u) => {
              const editing = editingId === u.id;

              return (
                <tr key={u.id} style={{ borderBottom: "1px solid #f2f2f2", verticalAlign: "top" }}>
                  <td>{u.id}</td>

                  <td>{u.username}</td>

                  <td>
                    {editing ? (
                      <input
                        value={(editDraft.full_name ?? "") as any}
                        onChange={(e) => setEditDraft((d) => ({ ...d, full_name: e.target.value }))}
                        style={{ padding: 6, width: 200 }}
                      />
                    ) : (
                      u.full_name
                    )}
                  </td>

                  <td>
                    {editing ? (
                      <input
                        value={(editDraft.email ?? "") as any}
                        onChange={(e) => setEditDraft((d) => ({ ...d, email: e.target.value }))}
                        style={{ padding: 6, width: 240 }}
                      />
                    ) : (
                      u.email ?? ""
                    )}
                  </td>

                  <td>
                    {editing ? (
                      <input
                        value={(editDraft.role ?? "") as any}
                        onChange={(e) => setEditDraft((d) => ({ ...d, role: e.target.value }))}
                        style={{ padding: 6, width: 120 }}
                      />
                    ) : (
                      u.role
                    )}
                  </td>

                  <td>
                    {editing ? (
                      <input
                        value={(editDraft.department ?? "") as any}
                        onChange={(e) => setEditDraft((d) => ({ ...d, department: e.target.value }))}
                        style={{ padding: 6, width: 120 }}
                      />
                    ) : (
                      u.department ?? ""
                    )}
                  </td>

                  <td>
                    {editing ? (
                      <label style={{ display: "flex", gap: 8, alignItems: "center" }}>
                        <input
                          type="checkbox"
                          checked={!!editDraft.is_active}
                          onChange={(e) => setEditDraft((d) => ({ ...d, is_active: e.target.checked }))}
                        />
                        {editDraft.is_active ? "yes" : "no"}
                      </label>
                    ) : (
                      (u.is_active ? "yes" : "no")
                    )}
                  </td>

                  <td>
                    {editing ? (
                      <input
                        value={(editDraft.auth_provider ?? "") as any}
                        onChange={(e) => setEditDraft((d) => ({ ...d, auth_provider: e.target.value }))}
                        style={{ padding: 6, width: 110 }}
                      />
                    ) : (
                      u.auth_provider
                    )}
                  </td>

                  <td>{fmtDate(u.last_login_at)}</td>

                  <td>
                    {!editing ? (
                      <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                        <button onClick={() => startEdit(u)} disabled={loading}>
                          Edit
                        </button>
                        <button onClick={() => deactivate(u.id)} disabled={loading || !u.is_active}>
                          Deactivate
                        </button>
                      </div>
                    ) : (
                      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                        <input
                          value={(editDraft.password_hash ?? "") as any}
                          onChange={(e) => setEditDraft((d) => ({ ...d, password_hash: e.target.value }))}
                          placeholder="new password_hash (optional)"
                          style={{ padding: 6, width: 210 }}
                        />
                        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                          <button onClick={() => saveEdit(u.id)} disabled={loading}>
                            Save
                          </button>
                          <button onClick={cancelEdit} disabled={loading}>
                            Cancel
                          </button>
                        </div>
                      </div>
                    )}
                  </td>
                </tr>
              );
            })}

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
    </div>
  );
}
