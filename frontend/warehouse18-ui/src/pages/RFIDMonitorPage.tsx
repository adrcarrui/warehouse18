import { useEffect, useMemo, useRef, useState } from "react";
import { AppShell } from "../app/AppShell";
import { getRfidSettings, setRfidSettings } from "../api/settings";

type RfidEvent = {
  ts?: string;
  type?: string;
  epc?: string;
  antenna?: number;
  rssi?: number;
  [k: string]: any;
};

const MAX_EVENTS = 250;

function safeStr(v: any) {
  if (v == null) return "";
  return String(v);
}

export default function RFIDMonitorPage() {
  const [connected, setConnected] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const [events, setEvents] = useState<RfidEvent[]>([]);

  // filters
  const [epcFilter, setEpcFilter] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [antennaFilter, setAntennaFilter] = useState("");

  const esRef = useRef<EventSource | null>(null);

  // settings (create movements)
  const [createMovements, setCreateMovements] = useState(true);
  const [loadingSettings, setLoadingSettings] = useState(true);
  const [savingSettings, setSavingSettings] = useState(false);
  const [settingsErr, setSettingsErr] = useState<string | null>(null);

  // SSE connection
  useEffect(() => {
    const url = "/api/rfid/events"; // mismo host/puerto que la UI (proxy si aplica)
    const es = new EventSource(url);
    esRef.current = es;

    setErr(null);
    setConnected(false);

    es.onopen = () => {
      setConnected(true);
      setErr(null);
    };

    es.onerror = () => {
      // EventSource reintenta solo; marcamos desconectado y dejamos que se recupere.
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
        // si llega keep-alive o algo no JSON, lo ignoramos
      }
    };

    return () => {
      es.close();
      esRef.current = null;
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

    setCreateMovements(v); // optimista
    setSavingSettings(true);

    try {
      const res = await setRfidSettings(v);
      setCreateMovements(!!res.create_movements); // lo que diga el backend
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
      return true;
    });
  }, [events, epcFilter, typeFilter, antennaFilter]);

  return (
    <AppShell title="RFID Monitor" subtitle="Live stream of RFID events from the readers">
      <div style={{ padding: 16, fontFamily: "system-ui" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12 }}>
          <h2 style={{ marginTop: 0, marginBottom: 0 }}>RFID Monitor</h2>

          <div style={{ display: "flex", gap: 14, alignItems: "center", flexWrap: "wrap" }}>
            <label style={{ display: "flex", gap: 8, alignItems: "center", fontSize: 12, color: "#333" }}>
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
            style={{ padding: 8, width: 180 }}
          />
          <input
            value={antennaFilter}
            onChange={(e) => setAntennaFilter(e.target.value)}
            placeholder="antenna (exact)"
            style={{ padding: 8, width: 140 }}
          />
          <div style={{ color: "#666", fontSize: 12, alignSelf: "center" }}>
            Showing {filtered.length} / {events.length} (max {MAX_EVENTS})
          </div>
        </div>

        <div style={{ marginTop: 12, border: "1px solid #eee", borderRadius: 8, overflow: "hidden" }}>
          <table width="100%" cellPadding={10} style={{ borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ textAlign: "left", background: "#fafafa", borderBottom: "1px solid #eee" }}>
                <th style={{ width: 220 }}>ts</th>
                <th style={{ width: 120 }}>type</th>
                <th style={{ width: 90 }}>ant</th>
                <th style={{ width: 110 }}>rssi</th>
                <th>epc</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((e, idx) => (
                <tr key={idx} style={{ borderBottom: "1px solid #f2f2f2" }}>
                  <td style={{ whiteSpace: "nowrap" }}>{safeStr(e.ts)}</td>
                  <td>{safeStr(e.type)}</td>
                  <td>{safeStr(e.antenna)}</td>
                  <td>{safeStr(e.rssi)}</td>
                  <td style={{ fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace" }}>
                    {safeStr(e.epc)}
                  </td>
                </tr>
              ))}

              {filtered.length === 0 && (
                <tr>
                  <td colSpan={5} style={{ padding: 16, color: "#666" }}>
                    No events (or filtered out)
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        <div style={{ marginTop: 10, color: "#666", fontSize: 12 }}>
          Nota: esto es monitor en vivo. La trazabilidad real vive en Movements/DB.
        </div>
      </div>
    </AppShell>
  );
}