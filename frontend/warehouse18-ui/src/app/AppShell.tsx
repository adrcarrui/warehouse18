import { ReactNode } from "react";
import { Link, useLocation } from "react-router-dom";
import {
  LayoutDashboard,
  Package,
  ArrowLeftRight,
  MapPin,
  Users,
  Settings,
} from "lucide-react";
import { cn } from "../lib/cn";

const nav = [
  { label: "Dashboard", href: "/", icon: LayoutDashboard },
  { label: "Items", href: "/items", icon: Package },
  { label: "Movements", href: "/movements", icon: ArrowLeftRight },
  { label: "Locations", href: "/locations", icon: MapPin },
  { label: "Users", href: "/users", icon: Users },
  { label: "Settings", href: "/settings", icon: Settings },
];

export function AppShell(props: {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
  children: ReactNode;
}) {
  const { title, subtitle, actions, children } = props;
  const loc = useLocation();

  return (
    <div className="min-h-screen bg-zinc-50 text-zinc-900">
      <div className="mx-auto flex min-h-screen max-w-[1440px]">
        {/* Sidebar */}
        <aside className="hidden w-72 shrink-0 border-r border-zinc-200/70 bg-zinc-50/60 md:flex md:flex-col">
          <div className="px-4 pt-4">
            <div className="rounded-2xl bg-white px-4 py-3 shadow-sm ring-1 ring-zinc-200/60">
              <div className="flex items-center gap-3">
                <div className="h-9 w-9 rounded-2xl bg-zinc-900" />
                <div className="min-w-0">
                  <div className="truncate text-sm font-semibold leading-tight">
                    Warehouse18
                  </div>
                  <div className="truncate text-xs text-zinc-500">
                    RFID / Inventory
                  </div>
                </div>
              </div>
            </div>
          </div>

          <nav className="mt-4 px-3">
            <div className="space-y-1">
              {nav.map((item) => {
                const active = loc.pathname === item.href;
                const Icon = item.icon;

                return (
                  <Link
                    key={item.href}
                    to={item.href}
                    className={cn(
                      "group flex items-center gap-3 rounded-xl px-3 py-2 text-sm transition-colors",
                      "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-zinc-300 focus-visible:ring-offset-2 ring-offset-zinc-50",
                      active
                        ? "bg-white text-zinc-900 shadow-sm ring-1 ring-zinc-200/70"
                        : "text-zinc-700 hover:bg-white/70 hover:text-zinc-900"
                    )}
                  >
                    <Icon
                      className={cn(
                        "h-4 w-4",
                        active
                          ? "text-zinc-900"
                          : "text-zinc-500 group-hover:text-zinc-700"
                      )}
                    />
                    <span className="font-medium">{item.label}</span>
                  </Link>
                );
              })}
            </div>
          </nav>

          <div className="mt-auto px-4 pb-4">
            <div className="rounded-2xl bg-white p-4 shadow-sm ring-1 ring-zinc-200/60">
              <div className="text-xs font-semibold text-zinc-700">Status</div>
              <div className="mt-1 flex items-center justify-between">
                <div className="text-xs text-zinc-600">Local dev</div>
                <span className="inline-flex h-2 w-2 rounded-full bg-green-500" />
              </div>
              <div className="mt-3 h-px bg-zinc-100" />
              <div className="mt-3 text-xs text-zinc-500">
                Minimal UI, maximum pain.
              </div>
            </div>
          </div>
        </aside>

        {/* Main */}
        <div className="flex min-w-0 flex-1 flex-col">
          {/* Header */}
          <header className="sticky top-0 z-20 bg-zinc-50/80 backdrop-blur">
            <div className="px-4 pt-4 md:px-6">
              <div className="rounded-2xl bg-white px-4 py-3 shadow-sm ring-1 ring-zinc-200/60">
                <div className="flex items-center justify-between gap-4">
                  <div className="min-w-0">
                    <div className="truncate text-base font-semibold">
                      {title}
                    </div>
                    {subtitle ? (
                      <div className="truncate text-sm text-zinc-500">
                        {subtitle}
                      </div>
                    ) : null}
                  </div>

                  <div className="flex items-center gap-2">
                    {actions}
                    <div className="grid h-9 w-9 place-items-center rounded-full bg-zinc-900 text-xs font-semibold text-white">
                      AC
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </header>

          {/* Content */}
          <main className="flex-1 px-4 pb-8 pt-4 md:px-6">
            <div className="mx-auto w-full max-w-6xl">{children}</div>
          </main>
        </div>
      </div>
    </div>
  );
}
