import { useEffect, useRef, useState } from "react";
import { AppShell } from "../app/AppShell";
import { Button } from "../ui/Button";
import { Input } from "../ui/Input";

type LogEntry = {
  ts: string;
  text: string;
};

function nowText() {
  return new Date().toLocaleTimeString("en-GB");
}

export default function PistolWsTestPage() {
  const [deviceId, setDeviceId] = useState("pistol-01");
  const [connected, setConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<any | null>(null);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const wsRef = useRef<WebSocket | null>(null);

  function addLog(text: string) {
    setLogs((prev) => [{ ts: nowText(), text }, ...prev].slice(0, 100));
  }

  function connect() {
    if (wsRef.current) {
      addLog("WebSocket already created");
      return;
    }

    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    const host = window.location.host;
    const url = `${protocol}://${host}/api/rfid/pistol/ws/${encodeURIComponent(deviceId.trim())}`;

    addLog(`Connecting to ${url}`);

    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
      addLog("Connected");
    };

    ws.onmessage = (event) => {
      addLog(`Received: ${event.data}`);

      try {
        const data = JSON.parse(event.data);
        setLastMessage(data);
      } catch {
        setLastMessage(event.data);
      }
    };

    ws.onclose = () => {
      setConnected(false);
      addLog("Disconnected");
      wsRef.current = null;
    };

    ws.onerror = () => {
      addLog("WebSocket error");
    };
  }

  function disconnect() {
    wsRef.current?.close();
    wsRef.current = null;
    setConnected(false);
  }

  function sendJson(payload: unknown) {
    const ws = wsRef.current;
    if (!ws || ws.readyState !== WebSocket.OPEN) {
      addLog("Cannot send: socket not connected");
      return;
    }

    const text = JSON.stringify(payload);
    ws.send(text);
    addLog(`Sent: ${text}`);
  }

  function sendPing() {
    sendJson({ type: "ping" });
  }

  function sendAck() {
    const epc =
      lastMessage && typeof lastMessage === "object" ? lastMessage.epc : null;

    sendJson({
      type: "ack",
      status: "received",
      epc: epc || "TEST-EPC",
    });
  }

  function sendSearchFound() {
    const epc =
      lastMessage && typeof lastMessage === "object" ? lastMessage.epc : "TEST-EPC";

    sendJson({
      type: "search_result",
      status: "found",
      epc,
      rssi: -48,
    });
  }

  function sendWriteOk() {
    const epc =
      lastMessage && typeof lastMessage === "object" ? lastMessage.epc : "TEST-EPC";

    sendJson({
      type: "write_result",
      status: "ok",
      epc,
    });
  }

  useEffect(() => {
    return () => {
      wsRef.current?.close();
      wsRef.current = null;
    };
  }, []);

  return (
    <AppShell
      title="RFID Pistol WebSocket Test"
      subtitle="Simulate a handheld device from the browser"
    >
      <div className="space-y-4">
        <div className="rounded-xl border border-zinc-200 bg-white p-5">
          <div className="grid gap-4 md:grid-cols-[1fr_auto_auto]">
            <Input
              value={deviceId}
              onChange={(e) => setDeviceId(e.target.value)}
              placeholder="pistol-01"
            />
            <Button onClick={connect} disabled={connected}>
              Connect
            </Button>
            <Button onClick={disconnect} disabled={!connected} variant="secondary">
              Disconnect
            </Button>
          </div>

          <div className="mt-4 flex flex-wrap gap-2">
            <Button onClick={sendPing} disabled={!connected}>
              Send Ping
            </Button>
            <Button onClick={sendAck} disabled={!connected}>
              Send ACK
            </Button>
            <Button onClick={sendSearchFound} disabled={!connected}>
              Send Search Result
            </Button>
            <Button onClick={sendWriteOk} disabled={!connected}>
              Send Write Result
            </Button>
          </div>

          <div className="mt-4 text-sm">
            <span className="font-medium">Status: </span>
            <span className={connected ? "text-emerald-600" : "text-zinc-500"}>
              {connected ? "Connected" : "Disconnected"}
            </span>
          </div>
        </div>

        <div className="rounded-xl border border-zinc-200 bg-white p-5">
          <div className="text-sm font-semibold text-zinc-900">Last message</div>
          <pre className="mt-3 whitespace-pre-wrap break-words rounded-xl bg-zinc-50 p-3 text-xs text-zinc-700">
            {lastMessage ? JSON.stringify(lastMessage, null, 2) : "No message received yet"}
          </pre>
        </div>

        <div className="rounded-xl border border-zinc-200 bg-white p-5">
          <div className="text-sm font-semibold text-zinc-900">Logs</div>
          <div className="mt-3 max-h-[420px] overflow-auto rounded-xl bg-zinc-50 p-3">
            {logs.length === 0 ? (
              <div className="text-sm text-zinc-500">No logs yet</div>
            ) : (
              <div className="space-y-2">
                {logs.map((log, i) => (
                  <div key={`${log.ts}-${i}`} className="text-xs text-zinc-700">
                    <span className="font-semibold text-zinc-500">[{log.ts}]</span>{" "}
                    {log.text}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </AppShell>
  );
}