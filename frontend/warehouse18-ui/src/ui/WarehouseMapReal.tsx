import React from "react";

type WarehouseMapRealProps = {
  activeAisle?: number | null;
  showAll?: boolean;
};

const MAP_WIDTH = 2182;
const MAP_HEIGHT = 798;

/*
  Coordenadas en el sistema real de la imagen 2182x798.
*/
const AISLE_MARKERS: Record<
  number,
  { x: number; y: number; width: number; height: number; label: string }
> = {
  0: { x: 650, y: 20, width: 1190, height: 240, label: "AISLE 0" },
  1: { x: 1870, y: 20, width: 170, height: 760, label: "AISLE 1" },
  2: { x: 1620, y: 270, width: 190, height: 510, label: "AISLE 2" },
  3: { x: 1370, y: 270, width: 190, height: 510, label: "AISLE 3" },
  4: { x: 960, y: 270, width: 350, height: 510, label: "AISLE 4" },
  5: { x: 680, y: 270, width: 210, height: 510, label: "AISLE 5" },
  6: { x: 170, y: 20, width: 440, height: 760, label: "AISLE 6" },
};

function AisleOverlay({
  marker,
  animated,
}: {
  marker: { x: number; y: number; width: number; height: number; label: string };
  animated?: boolean;
}) {
  const labelX = marker.x + marker.width / 2;
  const labelY = Math.max(marker.y - 24, 24);

  return (
    <g>
      <rect
        x={marker.x}
        y={marker.y}
        width={marker.width}
        height={marker.height}
        rx={14}
        ry={14}
        fill="#3b82f6"
        opacity={animated ? undefined : 0.18}
        className={animated ? "warehouse-aisle-fill" : undefined}
      />

      <rect
        x={marker.x}
        y={marker.y}
        width={marker.width}
        height={marker.height}
        rx={14}
        ry={14}
        fill="none"
        stroke="#1d4ed8"
        strokeWidth={10}
        opacity={animated ? undefined : 0.95}
        className={animated ? "warehouse-aisle-border" : undefined}
      />

      <g transform={`translate(${labelX}, ${labelY})`}>
        <rect
          x={-74}
          y={-24}
          width={148}
          height={42}
          rx={12}
          ry={12}
          fill="#1d4ed8"
        />
        <text
          x="0"
          y="4"
          textAnchor="middle"
          fontSize="28"
          fontWeight="700"
          fill="#ffffff"
          style={{ userSelect: "none" }}
        >
          {marker.label}
        </text>
      </g>
    </g>
  );
}

export function WarehouseMapReal({
  activeAisle,
  showAll = false,
}: WarehouseMapRealProps) {
  const activeMarker = activeAisle ? AISLE_MARKERS[activeAisle] : null;

  return (
    <div className="w-full rounded-xl border border-zinc-200 bg-white p-4">
      <div className="mb-3 text-xs font-semibold text-zinc-500">WAREHOUSE MAP</div>

      <style>
        {`
          @keyframes warehouseAisleFillBlink {
            0%   { opacity: 0.14; }
            50%  { opacity: 0.42; }
            100% { opacity: 0.14; }
          }

          @keyframes warehouseAisleBorderBlink {
            0%   { opacity: 1; }
            50%  { opacity: 0.45; }
            100% { opacity: 1; }
          }

          .warehouse-aisle-fill {
            animation: warehouseAisleFillBlink 1s ease-in-out infinite;
          }

          .warehouse-aisle-border {
            animation: warehouseAisleBorderBlink 1s ease-in-out infinite;
          }
        `}
      </style>

      <div className="flex justify-center">
        <div
          className="relative w-full"
          style={{
            maxWidth: "1600px",
            aspectRatio: `${MAP_WIDTH} / ${MAP_HEIGHT}`,
          }}
        >
          <img
            src="/warehouse-map.png"
            alt="Warehouse map"
            className="absolute inset-0 h-full w-full rounded-lg border border-zinc-200 object-contain bg-zinc-50"
            draggable={false}
          />

          <svg
            viewBox={`0 0 ${MAP_WIDTH} ${MAP_HEIGHT}`}
            className="absolute inset-0 h-full w-full"
            preserveAspectRatio="xMidYMid meet"
          >
            {showAll &&
              Object.entries(AISLE_MARKERS).map(([aisle, marker]) => (
                <AisleOverlay
                  key={aisle}
                  marker={marker}
                  animated={false}
                />
              ))}

            {!showAll && activeMarker && (
              <AisleOverlay marker={activeMarker} animated />
            )}
          </svg>
        </div>
      </div>
    </div>
  );
}