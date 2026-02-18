console.log("USING api.ts at /src/api.ts");

export type PageMeta = {
  page: number;
  pageSize: number;
  total: number;
  pages: number;
  link?: string | null;
};

export type PageOut<T> = {
  items: T[];
  page: number;
  page_size: number;
  total: number;
  pages: number;
};

function getNumberHeader(h: Headers, name: string, fallback: number) {
  const v = h.get(name);
  if (!v) return fallback;
  const n = Number(v);
  return Number.isFinite(n) ? n : fallback;
}

async function readError(res: Response): Promise<string> {
  let msg = `${res.status} ${res.statusText}`;
  try {
    const j = await res.json();
    if (j?.detail) msg = j.detail;
  } catch {
    // ignore
  }
  return msg;
}

export async function apiGet<T>(
  path: string,
  params?: Record<string, string | number | boolean | null | undefined>
): Promise<{ data: T; meta: PageMeta }> {
  const url = new URL(path, window.location.origin);

  if (params) {
    for (const [k, v] of Object.entries(params)) {
      if (v === undefined || v === null || v === "") continue;
      url.searchParams.set(k, String(v));
    }
  }

  const res = await fetch(url.toString(), {
    headers: { Accept: "application/json" },
  });

  if (!res.ok) {
    let msg = `${res.status} ${res.statusText}`;
    try {
      const j = await res.json();
      if (j?.detail) msg = j.detail;
    } catch {}
    throw new Error(msg);
  }

  const data = (await res.json()) as T;

  const meta: PageMeta = {
    page: getNumberHeader(res.headers, "x-page", 1),
    pageSize: getNumberHeader(res.headers, "x-page-size", 50),
    total: getNumberHeader(res.headers, "x-total-count", 0),
    pages: getNumberHeader(res.headers, "x-total-pages", 0),
    link: res.headers.get("link"),
  };

  return { data, meta };
}

export async function apiJson<T>(
  method: "POST" | "PATCH" | "PUT" | "DELETE",
  path: string,
  body?: unknown
): Promise<T> {
  const url = new URL(path, window.location.origin);

  const res = await fetch(url.toString(), {
    method,
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: body === undefined ? undefined : JSON.stringify(body),
  });

  if (!res.ok) throw new Error(await readError(res));

  // DELETE puede devolver vacío según implementaciones futuras
  const text = await res.text();
  return (text ? JSON.parse(text) : ({} as T)) as T;
}



export async function apiSend<TOut>(
  method: "POST" | "PATCH" | "DELETE",
  path: string,
  body?: any
): Promise<TOut> {
  const url = new URL(path, window.location.origin);

  const res = await fetch(url.toString(), {
    method,
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: body === undefined ? undefined : JSON.stringify(body),
  });

  if (!res.ok) {
    let msg = `${res.status} ${res.statusText}`;
    try {
      const j = await res.json();
      if (j?.detail) msg = j.detail;
    } catch {}
    throw new Error(msg);
  }

  // DELETE a veces devuelve vacío, tu API devuelve {"status":"ok"} pero por si acaso:
  if (res.status === 204) return undefined as unknown as TOut;

  try {
    return (await res.json()) as TOut;
  } catch {
    return undefined as unknown as TOut;
  }
}

export function apiPost<TOut>(path: string, body: any) {
  return apiSend<TOut>("POST", path, body);
}

export function apiPatch<TOut>(path: string, body: any) {
  return apiSend<TOut>("PATCH", path, body);
}

export function apiDelete<TOut>(path: string) {
  return apiSend<TOut>("DELETE", path);
}
