import { useEffect, useRef, useState } from "react";
import JsBarcode from "jsbarcode";

import { Button } from "./Button";

type MySimPartResult = {
  part_db_id: number;
  part_code: string;
  family: string;
};

type PartBarcodeGeneratorProps = {
  partDbId: string;
};

export function PartBarcodeGenerator({
  partDbId,
}: PartBarcodeGeneratorProps) {
  const barcodeRef =
    useRef<SVGSVGElement | null>(null);

  const [part, setPart] =
    useState<MySimPartResult | null>(null);

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState<string | null>(null);

  /*
   * Consulta mySim automáticamente cuando
   * ItemLocationPage proporciona un partDbId.
   */
  useEffect(() => {
    const normalizedId = partDbId.trim();
    const numericId = Number(normalizedId);

    if (
      !normalizedId ||
      !Number.isInteger(numericId) ||
      numericId <= 0
    ) {
      setPart(null);
      setError("Invalid mySim part DB ID");
      setLoading(false);
      return;
    }

    const controller = new AbortController();

    async function loadPart() {
      setLoading(true);
      setError(null);
      setPart(null);

      try {
        const response = await fetch(
          `/api/mysim/parts/${numericId}`,
          {
            signal: controller.signal,
            headers: {
              Accept: "application/json",
            },
          },
        );

        if (!response.ok) {
          const body = await response
            .json()
            .catch(() => null);

          throw new Error(
            body?.detail ??
              `Could not find part ${numericId}`,
          );
        }

        const result =
          (await response.json()) as MySimPartResult;

        if (!result.part_code) {
          throw new Error(
            "mySim returned a part without part_code",
          );
        }

        setPart(result);
      } catch (requestError) {
        if (
          requestError instanceof DOMException &&
          requestError.name === "AbortError"
        ) {
          return;
        }

        setError(
          requestError instanceof Error
            ? requestError.message
            : String(requestError),
        );
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    void loadPart();

    return () => {
      controller.abort();
    };
  }, [partDbId]);

  /*
   * Genera el barcode automáticamente cuando
   * mySim devuelve el part_code completo.
   */
  useEffect(() => {
    const barcodeElement =
      barcodeRef.current;

    if (!barcodeElement || !part?.part_code) {
      return;
    }

    barcodeElement.innerHTML = "";

    JsBarcode(
      barcodeElement,
      part.part_code,
      {
        format: "CODE128",
        displayValue: true,
        font: "Arial",
        fontSize: 18,
        fontOptions: "bold",
        textMargin: 8,
        height: 80,
        width: 2,
        margin: 14,
        background: "#ffffff",
        lineColor: "#020617",
      },
    );
  }, [part?.part_code]);

  function printBarcode() {
    if (!barcodeRef.current || !part) {
      return;
    }

    const barcodeSvg =
      barcodeRef.current.outerHTML;

    const printWindow = window.open(
      "",
      "_blank",
      "width=650,height=450",
    );

    if (!printWindow) {
      setError(
        "The browser blocked the print window",
      );
      return;
    }

    printWindow.document.write(`
      <!doctype html>
      <html lang="en">
        <head>
          <meta charset="UTF-8" />

          <title>${part.part_code}</title>

          <style>
            @page {
              margin: 10mm;
            }

            body {
              margin: 0;
              min-height: 100vh;
              display: flex;
              align-items: center;
              justify-content: center;
              font-family: Arial, sans-serif;
              background: white;
            }

            .barcode-label {
              padding: 24px;
              text-align: center;
              background: white;
            }

            .family {
              margin-bottom: 10px;
              font-size: 18px;
              font-weight: 700;
            }

            svg {
              max-width: 100%;
            }
          </style>
        </head>

        <body>
          <div class="barcode-label">
            <div class="family">
              ${part.family}
            </div>

            ${barcodeSvg}
          </div>

          <script>
            window.onload = function () {
              window.print();
              window.close();
            };
          </script>
        </body>
      </html>
    `);

    printWindow.document.close();
  }

return (
  <div className="w-full">
    {loading && (
      <div className="flex min-h-40 items-center justify-center text-sm text-blue-700">
        Loading barcode…
      </div>
    )}

    {error && (
      <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
        {error}
      </div>
    )}

    {part && (
      <div className="w-full">
        {/* BARCODE HEADER */}

        <div className="mb-3 flex flex-wrap items-start justify-between gap-3">
          <div>
            <div className="text-xs font-semibold uppercase tracking-wide text-zinc-500">
              Barcode
            </div>

            <div className="mt-1 text-base font-semibold text-zinc-900">
              {part.part_code}
            </div>

            <div className="mt-0.5 text-xs text-zinc-500">
              Family: {part.family} · mySim ID:{" "}
              {part.part_db_id}
            </div>
          </div>

          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={printBarcode}
          >
            Print
          </Button>
        </div>

        {/* BARCODE */}

        <div className="flex min-h-32 items-center justify-center overflow-x-auto rounded-lg bg-white px-4 py-3">
          <svg
            ref={barcodeRef}
            className="max-w-full"
          />
        </div>
      </div>
    )}
  </div>
);
}