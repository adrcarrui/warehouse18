import { useEffect, useMemo, useRef, useState } from "react";
import { AppShell } from "../app/AppShell";
import { getRfidSettings, setRfidSettings } from "../api/settings";

type RfidEvent = {
  ts?: string;
  seen_at?: string;
  at?: string;

  type?: string;
  epc?: string;

  antenna?: number;
  rssi?: number;

  reader_id?: string;
  protocol?: string;
  raw?: string;

  status?: string;
  message?: string;

  [k: string]: any;
};

type EpcSchema = {
  magic_hex?: string;
  version?: number;
  checksum?: string;
  families?: Record<string, number>;
};

const MAX_EVENTS = 250;

function safeStr(v: any) {
  if (v == null) return "";
  return String(v);
}

function eventTime(e: RfidEvent) {
  return safeStr(e.seen_at || e.at || e.ts);
}

function formatDateTime(value: string) {
  if (!value) return "";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleString("es-ES", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

function getFamilyMap(schema: EpcSchema | null) {
  if (!schema?.families) return {};

  const map: Record<string, string> = {};

  for (const [name, code] of Object.entries(schema.families)) {
    const hex = Number(code).toString(16).toUpperCase().padStart(2, "0");
    map[hex] = name;
  }

  return map;
}

function parsePartId(epc?: string, schema?: EpcSchema | null) {
  const value = safeStr(epc).trim().toUpperCase();
  if (!value || value.length !== 24) return "";

  const familyHex = value.slice(6, 8);
  const serialHex = value.slice(8, 22);
  const familyCode = parseInt(familyHex, 16);

  let familyName = familyHex;

  console.log("RFID parsePartId", {
    epc: value,
    familyHex,
    familyCode,
    schema,
    families: schema?.families,
  });

  if (schema?.families) {
    for (const [name, code] of Object.entries(schema.families)) {
      console.log("Comparando familia", { name, code, familyCode });
      if (Number(code) === familyCode) {
        familyName = name;
        break;
      }
    }
  }

  let serialDec = "";
  try {
    serialDec = BigInt("0x" + serialHex).toString();
  } catch {
    serialDec = serialHex;
  }

  return `${familyName}-${serialDec}`;
}

export default function RFIDMonitorPage() {
  const [connected, setConnected] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const [events, setEvents] = useState<RfidEvent[]>([]);
  const [epcSchema, setEpcSchema] = useState<EpcSchema | null>(null);

  // filters
  const [epcFilter, setEpcFilter] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [antennaFilter, setAntennaFilter] = useState("");
  const [readerFilter, setReaderFilter] = useState("");

  const esRef = useRef<EventSource | null>(null);

  // settings (create movements)
  const [createMovements, setCreateMovements] = useState(true);
  const [loadingSettings, setLoadingSettings] = useState(true);
  const [savingSettings, setSavingSettings] = useState(false);
  const [settingsErr, setSettingsErr] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;

    fetch("/api/rfid/epc-schema")
      .then((r) => {
        console.log("RFID schema fetch status", r.status, r.ok);
        if (!r.ok) throw new Error("schema fetch failed");
        return r.json();
      })
      .then((data) => {
        console.log("RFID schema loaded", data);
        if (!alive) return;
        setEpcSchema(data);
      })
      .catch((err) => {
        console.error("RFID schema fetch error", err);
        if (!alive) return;
        setEpcSchema(null);
      });

    return () => {
      alive = false;
    };
  }, []);

  // SSE connection
  useEffect(() => {
    const url = "/api/rfid/events";
    const es = new EventSource(url);
    esRef.current = es;

    setErr(null);
    setConnected(false);

    es.onopen = () => {
      setConnected(true);
      setErr(null);
    };

    es.onerror = () => {
      setConnected(false);
      setErr("SSE disconnected (will retry)...");
    };

    es.onmessage = (msg) => {
      try {
        const data = JSON.parse(msg.data);
        setEvents((prev) => {
          const next = [data, ...prev];
          if (next.length > MAX_EVENTS) next.length = MAX_EVENTS;
          return next;
        });
      } catch {
        // ignorar keep-alives / payload no JSON
      }
    };

    return () => {
      es.close();
      esRef.current = null;
    };
  }, []);

  // Load EPC schema
  useEffect(() => {
    let alive = true;

    fetch("/api/rfid/epc-schema")
      .then((r) => {
        if (!r.ok) throw new Error("schema fetch failed");
        return r.json();
      })
      .then((data) => {
        if (!alive) return;
        setEpcSchema(data);
      })
      .catch(() => {
        if (!alive) return;
        setEpcSchema(null);
      });

    return () => {
      alive = false;
    };
  }, []);

  // Load RFID settings once
  useEffect(() => {
    let alive = true;

    setLoadingSettings(true);
    setSettingsErr(null);

    getRfidSettings()
      .then((s) => {
        if (!alive) return;
        setCreateMovements(!!s.create_movements);
      })
      .catch(() => {
        if (!alive) return;
        setSettingsErr("No se pudo cargar la configuración RFID.");
      })
      .finally(() => {
        if (!alive) return;
        setLoadingSettings(false);
      });

    return () => {
      alive = false;
    };
  }, []);

  async function toggleMovements(v: boolean) {
    setSettingsErr(null);
    const prev = createMovements;

    setCreateMovements(v);
    setSavingSettings(true);

    try {
      const res = await setRfidSettings(v);
      setCreateMovements(!!res.create_movements);
    } catch {
      setCreateMovements(prev);
      setSettingsErr("No se pudo guardar. Revisa backend / permisos.");
    } finally {
      setSavingSettings(false);
    }
  }

  const filtered = useMemo(() => {
    const epcQ = epcFilter.trim().toLowerCase();
    const typeQ = typeFilter.trim().toLowerCase();
    const antQ = antennaFilter.trim();
    const readerQ = readerFilter.trim().toLowerCase();

    return events.filter((e) => {
      if (epcQ) {
        const epc = safeStr(e.epc).toLowerCase();
        if (!epc.includes(epcQ)) return false;
      }
      if (typeQ) {
        const t = safeStr(e.type).toLowerCase();
        if (!t.includes(typeQ)) return false;
      }
      if (antQ) {
        const a = safeStr(e.antenna);
        if (a !== antQ) return false;
      }
      if (readerQ) {
        const r = safeStr(e.reader_id).toLowerCase();
        if (!r.includes(readerQ)) return false;
      }
      return true;
    });
  }, [events, epcFilter, typeFilter, antennaFilter, readerFilter]);

  return (
    <AppShell title="RFID Monitor" subtitle="Live stream of RFID events from the readers">
      <div style={{ padding: 16, fontFamily: "system-ui" }}>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: 12,
          }}
        >
          <h2 style={{ marginTop: 0, marginBottom: 0 }}>RFID Monitor</h2>

          <div style={{ display: "flex", gap: 14, alignItems: "center", flexWrap: "wrap" }}>
            <label
              style={{
                display: "flex",
                gap: 8,
                alignItems: "center",
                fontSize: 12,
                color: "#333",
              }}
            >
              <input
                type="checkbox"
                disabled={loadingSettings || savingSettings}
                checked={createMovements}
                onChange={(e) => toggleMovements(e.target.checked)}
              />
              Movimientos: {createMovements ? "ON" : "OFF"}
              {(loadingSettings || savingSettings) && (
                <span style={{ color: "#666" }}>
                  {loadingSettings ? "(cargando...)" : "(guardando...)"}
                </span>
              )}
            </label>

            <span style={{ fontSize: 12, color: connected ? "green" : "#666" }}>
              {connected ? "connected" : "disconnected"}
            </span>

            <button onClick={() => setEvents([])}>Clear</button>
          </div>
        </div>

        {settingsErr && <div style={{ color: "#b45309", marginTop: 8 }}>{settingsErr}</div>}
        {err && <div style={{ color: "#b45309", marginTop: 8 }}>{err}</div>}

        <div style={{ display: "flex", gap: 12, marginTop: 12, flexWrap: "wrap" }}>
          <input
            value={epcFilter}
            onChange={(e) => setEpcFilter(e.target.value)}
            placeholder="filter epc contains…"
            style={{ padding: 8, width: 220 }}
          />
          <input
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            placeholder="filter type contains…"
            style={{ padding: 8, width: 160 }}
          />
          <input
            value={antennaFilter}
            onChange={(e) => setAntennaFilter(e.target.value)}
            placeholder="antenna (exact)"
            style={{ padding: 8, width: 140 }}
          />
          <input
            value={readerFilter}
            onChange={(e) => setReaderFilter(e.target.value)}
            placeholder="reader contains…"
            style={{ padding: 8, width: 180 }}
          />
          <div style={{ color: "#666", fontSize: 12, alignSelf: "center" }}>
            Showing {filtered.length} / {events.length} (max {MAX_EVENTS})
          </div>
        </div>

        <div
          style={{
            marginTop: 12,
            border: "1px solid #eee",
            borderRadius: 8,
            overflow: "auto",
          }}
        >
          <table width="100%" cellPadding={10} style={{ borderCollapse: "collapse", minWidth: 1250 }}>
            <thead>
              <tr style={{ textAlign: "left", background: "#fafafa", borderBottom: "1px solid #eee" }}>
                <th style={{ width: 180 }}>time</th>
                <th style={{ width: 110 }}>type</th>
                <th style={{ width: 180 }}>reader</th>
                <th style={{ width: 80 }}>ant</th>
                <th style={{ width: 100 }}>rssi</th>
                <th style={{ width: 220 }}>Part ID</th>
                <th style={{ width: 320 }}>epc</th>
                <th style={{ minWidth: 320 }}>raw / status</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((e, idx) => {
                const time = formatDateTime(eventTime(e));
                const type = safeStr(e.type);
                const reader = safeStr(e.reader_id);
                const antenna = safeStr(e.antenna);
                const rssi = safeStr(e.rssi);
                const epc = safeStr(e.epc);
                const partId = parsePartId(e.epc, epcSchema);
                const rawOrStatus = safeStr(e.raw || e.message || e.status);

                return (
                  <tr key={idx} style={{ borderBottom: "1px solid #f2f2f2" }}>
                    <td style={{ whiteSpace: "nowrap" }}>{time}</td>
                    <td>{type}</td>
                    <td>{reader}</td>
                    <td>{antenna}</td>
                    <td>{rssi}</td>
                    <td
                      style={{
                        fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
                        whiteSpace: "nowrap",
                      }}
                    >
                      {partId}
                    </td>
                    <td
                      style={{
                        fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
                        whiteSpace: "nowrap",
                      }}
                    >
                      {epc}
                    </td>
                    <td
                      title={rawOrStatus}
                      style={{
                        fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
                        maxWidth: 420,
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        whiteSpace: "nowrap",
                      }}
                    >
                      {rawOrStatus}
                    </td>
                  </tr>
                );
              })}

              {filtered.length === 0 && (
                <tr>
                  <td colSpan={8} style={{ padding: 16, color: "#666" }}>
                    No events (or filtered out)
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        <div style={{ marginTop: 10, color: "#666", fontSize: 12 }}>
          Nota: Part ID se calcula desde el EPC usando el schema cargado desde backend.
        </div>
      </div>
      <div style={{ marginTop: 10, fontSize: 12, color: "#666" }}>
  schema loaded: {epcSchema ? "yes" : "no"}
</div>
<pre style={{ fontSize: 11, background: "#f7f7f7", padding: 8, borderRadius: 6 }}>
  {JSON.stringify(epcSchema, null, 2)}
</pre>
    </AppShell>
  );
}