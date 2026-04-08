import React from "react";

type WarehouseMapProps = {
  activeArea?: number | null;
};

const areaFill = (area: number, activeArea?: number | null) =>
  activeArea === area ? "#cfe8ff" : "#eef2f7";

export default function WarehouseMapSVG({ activeArea }: WarehouseMapProps) {
  return (
    <svg
      viewBox="0 0 1200 500"
      className="w-full h-auto"
      xmlns="http://www.w3.org/2000/svg"
    >
      <rect x="0" y="0" width="1200" height="500" fill="#f5f7fa" />

      {/* Áreas */}
      <rect x="0" y="100" width="280" height="350" fill={areaFill(6, activeArea)} />
      <rect x="280" y="100" width="180" height="350" fill={areaFill(5, activeArea)} />
      <rect x="460" y="100" width="280" height="350" fill={areaFill(4, activeArea)} />
      <rect x="740" y="100" width="170" height="350" fill={areaFill(3, activeArea)} />
      <rect x="910" y="100" width="170" height="350" fill={areaFill(2, activeArea)} />
      <rect x="1080" y="100" width="120" height="350" fill={areaFill(1, activeArea)} />
      <rect x="280" y="0" width="920" height="100" fill={areaFill(7, activeArea)} />

      {/* Racks / columnas */}
      <rect x="320" y="140" width="60" height="320" fill="#9a9a9a" stroke="#666" />
      <rect x="500" y="140" width="60" height="320" fill="#9a9a9a" stroke="#666" />
      <rect x="760" y="140" width="60" height="320" fill="#9a9a9a" stroke="#666" />
      <rect x="920" y="140" width="60" height="320" fill="#9a9a9a" stroke="#666" />
      <rect x="1080" y="140" width="60" height="320" fill="#9a9a9a" stroke="#666" />

      {/* Línea superior */}
      <line
        x1="350"
        y1="135"
        x2="1110"
        y2="135"
        stroke="#aab3bc"
        strokeWidth="2"
        strokeDasharray="4 6"
      />

      {/* Textos */}
      <text x="120" y="260" fontSize="28" fill="#333" textAnchor="middle">AREA 6</text>
      <text x="370" y="320" fontSize="28" fill="#333" textAnchor="middle">AREA 5</text>
      <text x="600" y="320" fontSize="28" fill="#333" textAnchor="middle">AREA 4</text>
      <text x="825" y="320" fontSize="28" fill="#333" textAnchor="middle">AREA 3</text>
      <text x="995" y="320" fontSize="28" fill="#333" textAnchor="middle">AREA 2</text>
      <text x="1140" y="260" fontSize="28" fill="#333" textAnchor="middle">AREA 1</text>
      <text x="740" y="70" fontSize="30" fill="#333" textAnchor="middle">AREA 7</text>
    </svg>
  );
}