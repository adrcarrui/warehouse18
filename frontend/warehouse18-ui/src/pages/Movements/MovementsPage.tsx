import React, { useMemo, useState } from "react";
import { AppShell } from "../../app/AppShell";
import { Button } from "../../ui/Button";
import { Input } from "../../ui/Input";
import { Badge } from "../../ui/Badge";
import { Table } from "../../ui/Table";

type MovementRow = {
  id: number;
  type: "GI" | "GR" | "GT";
  partCode: string;
  origin: string;
  dest: string;
  qty: number;
  at: string;
  status: "ok" | "pending" | "error";
};

const seed: MovementRow[] = [
  { id: 10021, type: "GI", partCode: "235-0839", origin: "1485", dest: "1", qty: 1, at: "2026-02-19 16:22", status: "ok" },
  { id: 10022, type: "GT", partCode: "A-1001", origin: "Door", dest: "Aisle 1", qty: 3, at: "2026-02-19 16:25", status: "pending" },
  { id: 10023, type: "GR", partCode: "B-9911", origin: "Vendor", dest: "1485", qty: 12, at: "2026-02-19 16:30", status: "error" },
];

function StatusBadge({ s }: { s: MovementRow["status"] }) {
  const v = s === "ok" ? "success" : s === "pending" ? "warning" : "danger";
  return <Badge variant={v}>{s}</Badge>;
}

export function MovementsPage() {
  const [q, setQ] = useState("");
  const [type, setType] = useState<"" | MovementRow["type"]>("");

  const rows = useMemo(() => {
    return seed.filter((r) => {
      const matchesQ =
        !q ||
        r.partCode.toLowerCase().includes(q.toLowerCase()) ||
        r.origin.toLowerCase().includes(q.toLowerCase()) ||
        r.dest.toLowerCase().includes(q.toLowerCase()) ||
        String(r.id).includes(q);

      const matchesType = !type || r.type === type;
      return matchesQ && matchesType;
    });
  }, [q, type]);

  return (
    <AppShell
      title="Movements"
      actions={
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => alert("TODO: export")}>
            Export
          </Button>
          <Button size="sm" onClick={() => alert("TODO: abrir modal/new movement")}>
            + New
          </Button>
        </div>
      }
    >
      <div className="space-y-4">
        {/* Header section */}
        <div className="rounded-2xl border border-zinc-200 bg-white p-4 shadow-sm">
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div className="min-w-0">
              <div className="text-sm font-semibold text-zinc-900">Movement log</div>
              <div className="text-sm text-zinc-500">Filter and review recent movements</div>
            </div>

            <div className="flex items-center gap-2">
              <Badge>{rows.length} results</Badge>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  setQ("");
                  setType("");
                }}
              >
                Reset
              </Button>
            </div>
          </div>
<div className="bg-red-500 text-white p-6 rounded-2xl">
  Tailwind test
</div>

          <div className="mt-4 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div className="w-full md:max-w-md">
              <Input
                placeholder="Search id, part, origin, dest..."
                value={q}
                onChange={(e) => setQ(e.target.value)}
              />
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <Button variant={type === "" ? "primary" : "secondary"} size="sm" onClick={() => setType("")}>
                All
              </Button>
              <Button variant={type === "GI" ? "primary" : "secondary"} size="sm" onClick={() => setType("GI")}>
                GI
              </Button>
              <Button variant={type === "GR" ? "primary" : "secondary"} size="sm" onClick={() => setType("GR")}>
                GR
              </Button>
              <Button variant={type === "GT" ? "primary" : "secondary"} size="sm" onClick={() => setType("GT")}>
                GT
              </Button>
            </div>
          </div>
        </div>

        {/* Table */}
        <Table
          headers={["ID", "Type", "Part", "Origin", "Dest", "Qty", "At", "Status"]}
          rows={rows.map((r) => [
            <span className="font-semibold tabular-nums">{r.id}</span>,
            <Badge>{r.type}</Badge>,
            <span className="font-medium text-zinc-900">{r.partCode}</span>,
            <span className="text-zinc-700">{r.origin}</span>,
            <span className="text-zinc-700">{r.dest}</span>,
            <span className="tabular-nums">{r.qty}</span>,
            <span className="text-zinc-500">{r.at}</span>,
            <StatusBadge s={r.status} />,
          ])}
        />
      </div>
    </AppShell>
  );
}
