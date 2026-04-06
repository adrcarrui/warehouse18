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

function shouldAttachRfidKey(path: string): boolean {
  return path.startsWith("/api/rfid/");
}

function buildHeaders(
  path: string,
  extra?: Record<string, string>
): Record<string, string> {
  const headers: Record<string, string> = {
    ...(extra ?? {}),
  };

  if (shouldAttachRfidKey(path)) {
    const rfidApiKey = (import.meta.env.VITE_RFID_API_KEY as string | undefined)?.trim();

    if (rfidApiKey) {
      headers["X-RFID-KEY"] = rfidApiKey;
    }
  }

  return headers;
}

export async function apiGet<T>(
  path: string,
  params?: Record<string, string | number | boolean | null | undefined>
): Promise<{ data: T; meta: PageMeta }> {
  const url = new URL(path, window.location.origin);
  console.log("apiGet path =", path, "url =", url.toString());

  if (params) {
    for (const [k, v] of Object.entries(params)) {
      if (v === undefined || v === null || v === "") continue;
      url.searchParams.set(k, String(v));
    }
  }

  const res = await fetch(url.toString(), {
    headers: buildHeaders(path, { Accept: "application/json" }),
  });

  if (!res.ok) {
    let msg = `${res.status} ${res.statusText}`;
    try {
      const j = await res.json();
      if (j?.detail) msg = j.detail;
    } catch {
      // ignore
    }
    throw new Error(msg);
  }

  const data = (await res.json()) as T;
  const anyData = data as any;

  const pageH = getNumberHeader(res.headers, "x-page", NaN);
  const pageSizeH = getNumberHeader(res.headers, "x-page-size", NaN);
  const totalH = getNumberHeader(res.headers, "x-total-count", NaN);
  const pagesH = getNumberHeader(res.headers, "x-total-pages", NaN);

  const meta: PageMeta = {
    page: Number.isFinite(pageH) ? pageH : (anyData?.page ?? 1),
    pageSize: Number.isFinite(pageSizeH) ? pageSizeH : (anyData?.page_size ?? 50),
    total: Number.isFinite(totalH) ? totalH : (anyData?.total ?? 0),
    pages: Number.isFinite(pagesH) ? pagesH : (anyData?.pages ?? 0),
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
    headers: buildHeaders(path, {
      Accept: "application/json",
      "Content-Type": "application/json",
    }),
    body: body === undefined ? undefined : JSON.stringify(body),
  });

  if (!res.ok) throw new Error(await readError(res));

  const text = await res.text();
  return (text ? JSON.parse(text) : ({} as T)) as T;
}

export async function getRfidSettings() {
  const r = await fetch("/api/settings/rfid", {
    headers: { Accept: "application/json" },
  });
  if (!r.ok) throw new Error("Failed to load settings");
  return r.json() as Promise<{ create_movements: boolean }>;
}

export async function setRfidSettings(create_movements: boolean) {
  const r = await fetch("/api/settings/rfid", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ create_movements }),
  });
  if (!r.ok) throw new Error("Failed to update settings");
  return r.json() as Promise<{ create_movements: boolean }>;
}

export async function apiSend<TOut>(
  method: "POST" | "PATCH" | "DELETE",
  path: string,
  body?: any
): Promise<TOut> {
  const url = new URL(path, window.location.origin);

  const res = await fetch(url.toString(), {
    method,
    headers: buildHeaders(path, {
      Accept: "application/json",
      "Content-Type": "application/json",
    }),
    body: body === undefined ? undefined : JSON.stringify(body),
  });

  if (!res.ok) {
    let msg = `${res.status} ${res.statusText}`;
    try {
      const j = await res.json();
      if (j?.detail) msg = j.detail;
    } catch {
      // ignore
    }
    throw new Error(msg);
  }

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