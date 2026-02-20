import { Link } from "react-router-dom";
import { AppShell } from "../app/AppShell";
import { Package, ArrowLeftRight, MapPin, Users, Activity, Wifi } from "lucide-react";

// Si en tu proyecto existen estos componentes, úsalo.
// Si no, sustituye por <div className="..."> (te lo dejo fácil abajo).
import { Card } from "../ui/Card";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";

function StatCard(props: {
  title: string;
  value: string;
  hint?: string;
  icon: React.ComponentType<{ className?: string }>;
  to?: string;
}) {
  const Icon = props.icon;

  const inner = (
    <div className="flex items-start justify-between gap-4">
      <div className="min-w-0">
        <div className="text-xs font-medium text-slate-400">{props.title}</div>
        <div className="mt-1 text-2xl font-semibold text-slate-100">{props.value}</div>
        {props.hint ? (
          <div className="mt-1 text-xs text-slate-500">{props.hint}</div>
        ) : null}
      </div>
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-2">
        <Icon className="h-5 w-5 text-slate-300" />
      </div>
    </div>
  );

  if (props.to) {
    return (
      <Link to={props.to} className="block">
        <div className="transition hover:translate-y-[-1px] hover:border-slate-700">
          {inner}
        </div>
      </Link>
    );
  }

  return inner;
}

export default function DashboardPage() {
  // Placeholder por ahora. Luego lo conectarás a la API.
  const stats = {
    items: 42,
    stockContainers: 128,
    movementsToday: 7,
    alerts: 1,
    rfidStatus: "connected" as "connected" | "disconnected",
  };

  const recentMovements = [
    { id: 1, type: "GI", desc: "Good issue to device", when: "10:12", who: "Adrian", loc: "Door → Aisle" },
    { id: 2, type: "GT", desc: "Transfer between locations", when: "09:40", who: "System", loc: "Aisle → Shelf" },
    { id: 3, type: "GR", desc: "Good receipt", when: "08:05", who: "Adrian", loc: "Inbound → Aisle" },
  ];

  const badgeForRfid =
    stats.rfidStatus === "connected" ? (
      <Badge variant="success">RFID Connected</Badge>
    ) : (
      <Badge variant="danger">RFID Disconnected</Badge>
    );

  return (
    <AppShell
      title="Dashboard"
      subtitle="Overview of warehouse activity"
      actions={
        <div className="flex items-center gap-2">
          {badgeForRfid}
          <Link to="/movements">
            <Button variant="secondary">View Movements</Button>
          </Link>
        </div>
      }
    >
      <div className="space-y-6">
        {/* Top stats */}
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <Card className="p-5">
            <StatCard
              title="Items"
              value={String(stats.items)}
              hint="Definitions in catalog"
              icon={Package}
              to="/items"
            />
          </Card>

          <Card className="p-5">
            <StatCard
              title="Stock Containers"
              value={String(stats.stockContainers)}
              hint="Physical containers"
              icon={Activity}
              to="/stock-containers"
            />
          </Card>

          <Card className="p-5">
            <StatCard
              title="Movements (today)"
              value={String(stats.movementsToday)}
              hint="Created since 00:00"
              icon={ArrowLeftRight}
              to="/movements"
            />
          </Card>

          <Card className="p-5">
            <StatCard
              title="Alerts"
              value={String(stats.alerts)}
              hint="Need attention"
              icon={Wifi}
              to="/rfid"
            />
          </Card>
        </div>

        {/* Quick links */}
        <Card className="p-5">
          <div className="flex items-center justify-between gap-3">
            <div>
              <div className="text-sm font-semibold text-slate-100">Quick actions</div>
              <div className="mt-1 text-xs text-slate-500">Common shortcuts so you don’t click around like it’s a scavenger hunt.</div>
            </div>
          </div>

          <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <Link to="/items" className="rounded-xl border border-slate-800 bg-slate-950 p-4 transition hover:border-slate-700">
              <div className="flex items-center gap-3">
                <Package className="h-5 w-5 text-slate-300" />
                <div>
                  <div className="text-sm font-medium text-slate-100">Items</div>
                  <div className="text-xs text-slate-500">Catalog</div>
                </div>
              </div>
            </Link>

            <Link to="/movements" className="rounded-xl border border-slate-800 bg-slate-950 p-4 transition hover:border-slate-700">
              <div className="flex items-center gap-3">
                <ArrowLeftRight className="h-5 w-5 text-slate-300" />
                <div>
                  <div className="text-sm font-medium text-slate-100">Movements</div>
                  <div className="text-xs text-slate-500">History</div>
                </div>
              </div>
            </Link>

            <Link to="/locations" className="rounded-xl border border-slate-800 bg-slate-950 p-4 transition hover:border-slate-700">
              <div className="flex items-center gap-3">
                <MapPin className="h-5 w-5 text-slate-300" />
                <div>
                  <div className="text-sm font-medium text-slate-100">Locations</div>
                  <div className="text-xs text-slate-500">Map</div>
                </div>
              </div>
            </Link>

            <Link to="/users" className="rounded-xl border border-slate-800 bg-slate-950 p-4 transition hover:border-slate-700">
              <div className="flex items-center gap-3">
                <Users className="h-5 w-5 text-slate-300" />
                <div>
                  <div className="text-sm font-medium text-slate-100">Users</div>
                  <div className="text-xs text-slate-500">Access</div>
                </div>
              </div>
            </Link>
          </div>
        </Card>

        {/* Recent movements */}
        <Card className="p-5">
          <div className="flex items-center justify-between gap-3">
            <div>
              <div className="text-sm font-semibold text-slate-100">Recent movements</div>
              <div className="mt-1 text-xs text-slate-500">Last activity captured by the system</div>
            </div>
            <Link to="/movements">
              <Button variant="secondary">Open</Button>
            </Link>
          </div>

          <div className="mt-4 overflow-hidden rounded-xl border border-slate-800">
            <table className="w-full text-sm">
              <thead className="bg-slate-950">
                <tr className="text-left text-xs text-slate-400">
                  <th className="px-4 py-3">Time</th>
                  <th className="px-4 py-3">Type</th>
                  <th className="px-4 py-3">Description</th>
                  <th className="px-4 py-3">Route</th>
                  <th className="px-4 py-3">By</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800 bg-slate-900/20">
                {recentMovements.map((m) => (
                  <tr key={m.id} className="hover:bg-slate-900/40">
                    <td className="px-4 py-3 text-slate-300">{m.when}</td>
                    <td className="px-4 py-3">
                      <span className="inline-flex rounded-lg border border-slate-700 bg-slate-950 px-2 py-0.5 text-xs font-medium text-slate-200">
                        {m.type}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-slate-200">{m.desc}</td>
                    <td className="px-4 py-3 text-slate-400">{m.loc}</td>
                    <td className="px-4 py-3 text-slate-400">{m.who}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="mt-3 text-xs text-slate-500">
            Nota: esto ahora es mock. Luego lo alimentamos con la API y paginación.
          </div>
        </Card>
      </div>
    </AppShell>
  );
}