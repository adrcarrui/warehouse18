import { useState } from "react";
import { AppShell } from "../app/AppShell";
import { apiJson } from "../api";
import { Button } from "../ui/Button";
import { Input } from "../ui/Input";

type SendTargetEpcResponse = {
  ok: boolean;
  device_id: string;
  message: {
    type: string;
    mode: "search" | "write";
    epc: string;
    itemKey?: string | null;
  };
};

export default function PistolSendEpcPage() {
  const [deviceId, setDeviceId] = useState("pistol-01");
  const [epc, setEpc] = useState("");
  const [itemKey, setItemKey] = useState("");
  const [mode, setMode] = useState<"search" | "write">("search");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [response, setResponse] = useState<SendTargetEpcResponse | null>(null);

  async function sendEpc() {
    const cleanDeviceId = deviceId.trim();
    const cleanEpc = epc.trim().toUpperCase();
    const cleanItemKey = itemKey.trim();

    if (!cleanDeviceId) {
      setError("Device ID is required");
      setSuccess(null);
      setResponse(null);
      return;
    }

    if (!cleanEpc) {
      setError("EPC is required");
      setSuccess(null);
      setResponse(null);
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);
    setResponse(null);

    try {
      const data = await apiJson<SendTargetEpcResponse>(
        "/api/rfid/pistol/send-target-epc",
        {
          method: "POST",
          body: JSON.stringify({
            device_id: cleanDeviceId,
            epc: cleanEpc,
            mode,
            item_key: cleanItemKey || null,
          }),
        }
      );

      setResponse(data);
      setSuccess(`EPC sent successfully to ${cleanDeviceId}`);
    } catch (e: any) {
      setError(e?.message ?? String(e));
    } finally {
      setLoading(false);
    }
  }

  function clearForm() {
    setEpc("");
    setItemKey("");
    setMode("search");
    setError(null);
    setSuccess(null);
    setResponse(null);
  }

  return (
    <AppShell
      title="Send EPC to RFID Pistol"
      subtitle="Send a target EPC to the handheld device through WebSocket"
    >
      <div className="space-y-4">
        {error && (
          <div className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            Error: {error}
          </div>
        )}

        {success && (
          <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">
            {success}
          </div>
        )}

        <div className="rounded-xl border border-zinc-200 bg-white p-5">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <label className="text-sm font-medium text-zinc-700">
                Device ID
              </label>
              <Input
                value={deviceId}
                onChange={(e) => setDeviceId(e.target.value)}
                placeholder="e.g. pistol-01"
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-zinc-700">
                Mode
              </label>
              <select
                value={mode}
                onChange={(e) =>
                  setMode(e.target.value as "search" | "write")
                }
                className="w-full rounded-xl border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900 outline-none focus:border-zinc-400"
              >
                <option value="search">Search</option>
                <option value="write">Write</option>
              </select>
            </div>

            <div className="space-y-2 md:col-span-2">
              <label className="text-sm font-medium text-zinc-700">EPC</label>
              <Input
                value={epc}
                onChange={(e) => setEpc(e.target.value.toUpperCase())}
                placeholder="e.g. E2000017221101441890ABCD"
                onKeyDown={(e) => {
                  if (e.key === "Enter") sendEpc();
                }}
              />
            </div>

            <div className="space-y-2 md:col-span-2">
              <label className="text-sm font-medium text-zinc-700">
                Item Key (optional)
              </label>
              <Input
                value={itemKey}
                onChange={(e) => setItemKey(e.target.value)}
                placeholder="e.g. CN235-015922"
              />
            </div>
          </div>

          <div className="mt-5 flex flex-wrap gap-2">
            <Button onClick={sendEpc} disabled={loading}>
              {loading ? "Sending..." : "Send EPC"}
            </Button>

            <Button onClick={clearForm} disabled={loading} variant="secondary">
              Clear
            </Button>
          </div>
        </div>

        {response && (
          <div className="rounded-xl border border-zinc-200 bg-white p-5">
            <div className="text-sm font-semibold text-zinc-900">
              Last response
            </div>

            <div className="mt-4 grid gap-3 md:grid-cols-2">
              <div className="rounded-xl border border-zinc-200 bg-zinc-50 p-3">
                <div className="text-xs text-zinc-500">Device ID</div>
                <div className="text-sm font-medium text-zinc-900">
                  {response.device_id}
                </div>
              </div>

              <div className="rounded-xl border border-zinc-200 bg-zinc-50 p-3">
                <div className="text-xs text-zinc-500">Type</div>
                <div className="text-sm font-medium text-zinc-900">
                  {response.message.type}
                </div>
              </div>

              <div className="rounded-xl border border-zinc-200 bg-zinc-50 p-3">
                <div className="text-xs text-zinc-500">Mode</div>
                <div className="text-sm font-medium text-zinc-900">
                  {response.message.mode}
                </div>
              </div>

              <div className="rounded-xl border border-zinc-200 bg-zinc-50 p-3">
                <div className="text-xs text-zinc-500">EPC</div>
                <div className="break-all text-sm font-medium text-zinc-900">
                  {response.message.epc}
                </div>
              </div>

              <div className="rounded-xl border border-zinc-200 bg-zinc-50 p-3 md:col-span-2">
                <div className="text-xs text-zinc-500">Item Key</div>
                <div className="text-sm font-medium text-zinc-900">
                  {response.message.itemKey || "—"}
                </div>
              </div>
            </div>

            <details className="mt-4 rounded-xl border border-zinc-200 bg-zinc-50 p-3">
              <summary className="cursor-pointer text-sm font-medium text-zinc-800">
                Raw response
              </summary>
              <pre className="mt-3 whitespace-pre-wrap break-words text-xs text-zinc-700">
                {JSON.stringify(response, null, 2)}
              </pre>
            </details>
          </div>
        )}
      </div>
    </AppShell>
  );
}