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
