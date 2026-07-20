import { useState } from "react";

import { apiGet } from "../api";
import { AppShell } from "../app/AppShell";
import { Button } from "../ui/Button";
import { Input } from "../ui/Input";
import { PartBarcodeGenerator } from "../ui/PartBarcodeGenerator";
import { WarehouseMapReal } from "../ui/WarehouseMapReal";

type LocationPage = {
  items: LocationOut[];
  page: number;
  page_size: number;
  total: number;
  pages: number;
};

type ItemLocationOut = {
  item_key: string;
  found: boolean;
  part_db_id?: number | null;
  last_movement_id?: string | null;

  movement_type?: string | null;
  movement_type_name?: string | null;

  source_location?: number | null;
  source_location_name?: string | null;
  source_aisle_id?: number | null;

  destination_location?: number | null;
  destination_location_name?: string | null;
  destination_location_label?: string | null;
  destination_aisle_id?: number | null;

  done_by?: number | null;
  done_by_name?: string | null;

  movement_date?: string | null;
  raw?: Record<string, unknown> | null;
};

type LocationOut = {
  id: number;
  code?: string | null;
  name?: string | null;
  aisle_id?: number | null;
};

function fmtDate(value?: string | null) {
  if (!value) return "—";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString("en-GB");
}

function parsePartDbId(value: string): number | null {
  const normalizedValue = value.trim();

  if (!normalizedValue) return null;

  /*
   * Acepta tanto el ID interno (15922) como el código
   * completo del part (CN235-015922).
   */
  const fullPartCodeMatch = normalizedValue.match(/-(\d+)$/);
  const numericValue = fullPartCodeMatch?.[1] || normalizedValue;

  if (!/^\d+$/.test(numericValue)) return null;

  const partDbId = Number(numericValue);

  return Number.isSafeInteger(partDbId) && partDbId > 0
    ? partDbId
    : null;
}

function validLocationName(
  value: string | null | undefined,
  locationId: number | null | undefined,
) {
  const normalizedValue = value?.trim();

  if (!normalizedValue) return null;

  if (
    locationId != null &&
    normalizedValue === String(locationId)
  ) {
    return null;
  }

  return normalizedValue;
}

async function resolveLocation(
  locationCode: number | null | undefined,
): Promise<LocationOut | null> {
  if (locationCode == null) {
    return null;
  }

  const code = String(locationCode);

  try {
    const { data } = await apiGet<LocationPage>(
      "/api/locations/",
      {
        q: code,
        page: 1,
        page_size: 50,
      },
    );

    return (
      (data.items ?? []).find(
        (location) =>
          String(location.code ?? "").trim() === code,
      ) ?? null
    );
  } catch (error) {
    console.error(
      `Could not resolve location ${code}`,
      error,
    );

    return null;
  }
}

/*
 * Extrae el número de pasillo desde:
 *
 * W18-AISLE2
 * AISLE_2
 * AISLE-2
 * ALMACEN 18
 */
function extractAisleNumber(
  value?: string | null,
): number | null {
  if (!value) return null;

  const normalizedValue = value.toUpperCase();

  if (
    normalizedValue.includes("ALMACEN 18") ||
    normalizedValue.includes("ALMACÉN 18")
  ) {
    return 0;
  }

  let match = normalizedValue.match(
    /W18-AISLE\s*([1-6])/,
  );

  if (match) {
    return Number(match[1]);
  }

  match = normalizedValue.match(
    /AISLE[_\s-]*([1-6])/,
  );

  if (match) {
    return Number(match[1]);
  }

  return null;
}

export default function ItemLocationPage() {
  /*
   * Valor introducido en la barra principal.
   */
  const [partId, setPartId] = useState("");

  /*
   * Valor confirmado después de buscar.
   * Se utiliza para generar el barcode.
   */
  const [
    searchedPartDbId,
    setSearchedPartDbId,
  ] = useState("");

  const [loading, setLoading] = useState(false);

  const [err, setErr] =
    useState<string | null>(null);

  const [result, setResult] =
    useState<ItemLocationOut | null>(null);

  async function search() {
    const rawPartId = partId.trim();

    if (!rawPartId) {
      setErr("Enter a Part DB ID");
      setResult(null);
      setSearchedPartDbId("");
      return;
    }

    const numericPartId = parsePartDbId(rawPartId);

    if (numericPartId == null) {
      setErr(
        "Enter a valid Part DB ID or a complete part code, for example 15922 or CN235-015922",
      );
      setResult(null);
      setSearchedPartDbId("");
      return;
    }

    setLoading(true);
    setErr(null);
    setResult(null);
    setSearchedPartDbId("");

    try {
      const { data } =
        await apiGet<ItemLocationOut>(
          "/api/mysim/item-location",
          {
            part_id: numericPartId,
          },
        );

      const [sourceLocation, destinationLocation] =
        await Promise.all([
          resolveLocation(data.source_location),
          resolveLocation(data.destination_location),
        ]);

      setResult({
        ...data,
        source_location_name:
            sourceLocation?.name ||
            data.source_location_name ||
            null,

          source_aisle_id:
            sourceLocation?.aisle_id ?? null,

          destination_location_name:
            destinationLocation?.name ||
            data.destination_location_name ||
            data.destination_location_label ||
            null,

          destination_location_label:
            destinationLocation?.name ||
            data.destination_location_name ||
            data.destination_location_label ||
            null,

          destination_aisle_id:
            destinationLocation?.aisle_id ?? null,
      });

      /*
       * Activa el generador después de completar
       * correctamente la búsqueda principal.
       */
      setSearchedPartDbId(
        String(numericPartId),
      );
    } catch (error: unknown) {
      setErr(
        error instanceof Error
          ? error.message
          : String(error),
      );

      setSearchedPartDbId("");
    } finally {
      setLoading(false);
    }
  }

  const activeAisle =
    result?.destination_aisle_id ?? null;

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
          <div className="mb-4">
            <div className="text-base font-semibold text-zinc-900">
              Find an item's current location
            </div>

            <p className="mt-1 text-sm text-zinc-600">
              Enter the internal mySim Part DB ID or paste the complete part
              code. The numeric ID will be extracted automatically.
            </p>

            <div className="mt-3 inline-flex flex-wrap items-center gap-2 rounded-lg border border-blue-100 bg-blue-50 px-3 py-2 text-sm">
              <span className="font-medium text-zinc-700">
                Complete part code
              </span>
              <span className="font-semibold text-blue-950">
                CN235-015922
              </span>
              <span className="text-zinc-400">→</span>
              <span className="font-medium text-zinc-700">
                Part DB ID
              </span>
              <span className="font-semibold text-blue-950">15922</span>
            </div>
          </div>

          <div className="flex gap-2">
            <Input
              value={partId}
              autoComplete="off"
              placeholder="Enter 15922 or CN235-015922"
              onChange={(event) => {
                const value = event.target.value;

                setPartId(value);

                /*
                 * Limpia el resultado anterior cuando
                 * comienza una búsqueda nueva.
                 */
                setResult(null);
                setSearchedPartDbId("");
                setErr(null);
              }}
              onKeyDown={(event) => {
                if (event.key === "Enter") {
                  event.preventDefault();
                  void search();
                }
              }}
            />

            <Button
              type="button"
              onClick={() => void search()}
              disabled={
                loading || !partId.trim()
              }
            >
              {loading
                ? "Searching..."
                : "Search"}
            </Button>
          </div>
        </div>

        {/* RESULT */}

        {result && (
          <div className="rounded-xl border border-zinc-200 bg-white p-5">
            {/* SUMMARY + BARCODE */}

            {/* UNIFIED SUMMARY */}

<div className="rounded-xl bg-zinc-50 p-5">
  <div className="grid gap-6 lg:grid-cols-[260px_minmax(0,1fr)] lg:items-center">
    {/* PART INFORMATION */}

    <div className="grid grid-cols-2 gap-5 lg:grid-cols-1">
      <div>
        <div className="text-xs font-semibold uppercase tracking-wide text-zinc-500">
          Part DB ID
        </div>

        <div className="mt-1 text-xl font-bold text-zinc-900">
          {result.part_db_id ??
            result.item_key}
        </div>
      </div>

      {result.found && (
        <div>
          <div className="text-xs font-semibold uppercase tracking-wide text-zinc-500">
            Current location
          </div>

          <div className="mt-1 text-2xl font-bold text-blue-700">
            {result.destination_location_name ||
              result.destination_location_label ||
              "Location name unavailable"}
          </div>
        </div>
      )}
    </div>

    {/* BARCODE AREA */}

    {searchedPartDbId && (
      <div className="border-t border-zinc-200 pt-5 lg:border-l lg:border-t-0 lg:pl-8 lg:pt-0">
        <PartBarcodeGenerator
          partDbId={searchedPartDbId}
        />
      </div>
    )}
  </div>
</div>

            {!result.found ? (
              <div className="mt-5 rounded-xl border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
                Item not found in mySim.
              </div>
            ) : (
              <>
                {/* WAREHOUSE MAP */}

                <div className="mt-6">
                  <WarehouseMapReal
                    activeAisle={
                      activeAisle
                    }
                  />
                </div>

                {/* INFORMATION GRID */}

                <div className="mt-5 grid gap-3 md:grid-cols-2">
                  <div className="rounded-xl border border-zinc-200 bg-zinc-50 p-3">
                    <div className="text-xs text-zinc-500">
                      Last Movement ID
                    </div>

                    <div className="text-sm font-medium text-zinc-900">
                      {result.last_movement_id ||
                        "—"}
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
                    <div className="text-xs text-zinc-500">
                      Date
                    </div>

                    <div className="text-sm font-medium text-zinc-900">
                      {fmtDate(
                        result.movement_date,
                      )}
                    </div>
                  </div>

                  <div className="rounded-xl border border-zinc-200 bg-zinc-50 p-3">
                    <div className="text-xs text-zinc-500">
                      Done By
                    </div>

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
                        "Location name unavailable"}
                    </div>
                  </div>

                  <div className="rounded-xl border border-zinc-200 bg-zinc-50 p-3">
                    <div className="text-xs text-zinc-500">
                      Destination Location
                    </div>

                    <div className="text-sm font-medium text-zinc-900">
                      {result.destination_location_name ||
                        result.destination_location_label ||
                        "Location name unavailable"}
                    </div>
                  </div>
                </div>

                {/* RAW MYSIM DATA */}

                {result.raw && (
                  <details className="mt-4 rounded-xl border border-zinc-200 bg-zinc-50 p-3">
                    <summary className="cursor-pointer text-sm font-medium text-zinc-800">
                      Raw mySim movement
                    </summary>

                    <pre className="mt-3 whitespace-pre-wrap break-words text-xs text-zinc-700">
                      {JSON.stringify(
                        result.raw,
                        null,
                        2,
                      )}
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
