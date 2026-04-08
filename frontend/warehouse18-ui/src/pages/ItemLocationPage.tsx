import { useState } from "react";
import { AppShell } from "../app/AppShell";
import { apiGet } from "../api";
import { Button } from "../ui/Button";
import { Input } from "../ui/Input";
import { WarehouseMapReal } from "../ui/WarehouseMapReal";

type ItemLocationOut = {
  item_key: string;
  found: boolean;
  part_db_id?: number | null;
  last_movement_id?: string | null;

  movement_type?: string | null;
  movement_type_name?: string | null;

  source_location?: number | null;
  source_location_name?: string | null;

  destination_location?: number | null;
  destination_location_name?: string | null;
  destination_location_label?: string | null;

  done_by?: number | null;
  done_by_name?: string | null;

  movement_date?: string | null;
  raw?: Record<string, unknown> | null;
};

function fmtDate(v?: string | null) {
  if (!v) return "";
  const d = new Date(v);
  if (Number.isNaN(d.getTime())) return v;
  return d.toLocaleString("en-GB");
}

/*
  Extrae el número de pasillo desde:
  - W18-AISLE2
  - AISLE_2
  - AISLE-2
*/
function extractAisleNumber(value?: string | null): number | null {
  if (!value) return null;

  const v = value.toUpperCase();

  let match = v.match(/W18-AISLE\s*([1-6])/);
  if (match) return Number(match[1]);

  match = v.match(/AISLE[_\s-]*([1-6])/);
  if (match) return Number(match[1]);

  return null;
}

export default function ItemLocationPage() {
  const [partId, setPartId] = useState("");
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [result, setResult] = useState<ItemLocationOut | null>(null);

  async function search() {
    const raw = partId.trim();
    if (!raw) return;

    const n = Number(raw);
    if (!Number.isFinite(n) || n <= 0) {
      setErr("Part ID must be a positive number");
      setResult(null);
      return;
    }

    setLoading(true);
    setErr(null);
    setResult(null);

    try {
      const { data } = await apiGet<ItemLocationOut>(
        "/api/mysim/item-location",
        { part_id: n }
      );
      setResult(data);
    } catch (e: any) {
      setErr(e?.message ?? String(e));
    } finally {
      setLoading(false);
    }
  }

  const activeAisle = extractAisleNumber(
    result?.destination_location_name ||
      result?.destination_location_label ||
      null
  );

  return (
    <AppShell
      title="Item Location"
      subtitle="Check the current location from the latest mySim movement"
    >
      <div className="space-y-4">

        {/* ERROR */}
        {err && (
          <div className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            Error: {err}
          </div>
        )}

        {/* SEARCH */}
        <div className="rounded-xl border border-zinc-200 bg-white p-4">
          <div className="flex gap-2">
            <Input
              value={partId}
              onChange={(e) => setPartId(e.target.value)}
              placeholder="Part DB ID, e.g. 15922"
              onKeyDown={(e) => {
                if (e.key === "Enter") search();
              }}
            />
            <Button onClick={search} disabled={loading}>
              {loading ? "Searching..." : "Search"}
            </Button>
          </div>
        </div>

        {/* RESULT */}
        {result && (
          <div className="rounded-xl border border-zinc-200 bg-white p-5">

            {/* PART ID */}
            <div className="text-xs font-semibold text-zinc-500">
              PART DB ID
            </div>
            <div className="text-lg font-semibold text-zinc-900">
              {result.part_db_id ?? result.item_key}
            </div>

            {!result.found ? (
              <div className="mt-4 rounded-xl border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
                Item not found in mySim.
              </div>
            ) : (
              <>
                {/* CURRENT LOCATION */}
                <div className="mt-5 text-xs font-semibold text-zinc-500">
                  CURRENT LOCATION
                </div>

                <div className="mt-1 text-2xl font-bold text-blue-700">
                  {result.destination_location_name ||
                    result.destination_location_label ||
                    "Unknown"}
                </div>

                {/* MAPA CENTRADO */}
                <div className="mt-5 flex justify-center">
                  <WarehouseMapReal activeAisle={activeAisle} />
                </div>

                {/* INFO GRID */}
                <div className="mt-5 grid gap-3 md:grid-cols-2">

                  <div className="rounded-xl border border-zinc-200 bg-zinc-50 p-3">
                    <div className="text-xs text-zinc-500">
                      Last Movement ID
                    </div>
                    <div className="text-sm font-medium text-zinc-900">
                      {result.last_movement_id || "—"}
                    </div>
                  </div>

                  <div className="rounded-xl border border-zinc-200 bg-zinc-50 p-3">
                    <div className="text-xs text-zinc-500">
                      Movement Type
                    </div>
                    <div className="text-sm font-medium text-zinc-900">
                      {result.movement_type_name ||
                        result.movement_type ||
                        "—"}
                    </div>
                  </div>

                  <div className="rounded-xl border border-zinc-200 bg-zinc-50 p-3">
                    <div className="text-xs text-zinc-500">Date</div>
                    <div className="text-sm font-medium text-zinc-900">
                      {fmtDate(result.movement_date)}
                    </div>
                  </div>

                  <div className="rounded-xl border border-zinc-200 bg-zinc-50 p-3">
                    <div className="text-xs text-zinc-500">Done By</div>
                    <div className="text-sm font-medium text-zinc-900">
                      {result.done_by_name ||
                        result.done_by ||
                        "—"}
                    </div>
                  </div>

                  <div className="rounded-xl border border-zinc-200 bg-zinc-50 p-3">
                    <div className="text-xs text-zinc-500">
                      Source Location
                    </div>
                    <div className="text-sm font-medium text-zinc-900">
                      {result.source_location_name ||
                        result.source_location ||
                        "—"}
                    </div>
                  </div>

                  <div className="rounded-xl border border-zinc-200 bg-zinc-50 p-3">
                    <div className="text-xs text-zinc-500">
                      Destination Location
                    </div>
                    <div className="text-sm font-medium text-zinc-900">
                      {result.destination_location_name ||
                        result.destination_location ||
                        "—"}
                    </div>
                  </div>

                </div>

                {/* RAW DEBUG */}
                {result.raw && (
                  <details className="mt-4 rounded-xl border border-zinc-200 bg-zinc-50 p-3">
                    <summary className="cursor-pointer text-sm font-medium text-zinc-800">
                      Raw mySim movement
                    </summary>
                    <pre className="mt-3 whitespace-pre-wrap break-words text-xs text-zinc-700">
                      {JSON.stringify(result.raw, null, 2)}
                    </pre>
                  </details>
                )}

              </>
            )}
          </div>
        )}
      </div>
    </AppShell>
  );
}