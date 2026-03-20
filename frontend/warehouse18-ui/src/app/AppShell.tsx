import { ReactNode, useEffect, useMemo, useState } from "react";
import { SystemHealthBadge } from "../ui/SystemHealthBadge";
import { Link, useLocation } from "react-router-dom";
import {
  LayoutDashboard,
  Package,
  ArrowLeftRight,
  MapPin,
  Users,
  Settings,
  ChevronLeft,
  ChevronRight,
  Radio,
} from "lucide-react";
import { cn } from "../lib/cn";

type NavItem = {
  label: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
};

const NAV: NavItem[] = [
  { label: "Dashboard", href: "/", icon: LayoutDashboard },
  { label: "Items", href: "/items", icon: Package },
  { label: "Movements", href: "/movements", icon: ArrowLeftRight },
  { label: "Locations", href: "/locations", icon: MapPin },
  { label: "Users", href: "/users", icon: Users },
  { label: "RFID Monitor", href: "/rfid-monitor", icon: Radio },
  { label: "Settings", href: "/settings", icon: Settings },
  { label: "RFID Review", href: "/rfid-review", icon: Radio },
];

const STORAGE_KEY = "warehouse18.sidebarCollapsed";

export function AppShell(props: {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
  children: ReactNode;
}) {
  const { title, subtitle, actions, children } = props;
  const location = useLocation();

  const [collapsed, setCollapsed] = useState<boolean>(() => {
    try {
      return localStorage.getItem(STORAGE_KEY) === "1";
    } catch {
      return false;
    }
  });

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, collapsed ? "1" : "0");
    } catch {
      // si falla, pues nada, el mundo sigue girando
    }
  }, [collapsed]);

  const activeHref = useMemo(() => location.pathname, [location.pathname]);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <div className="flex">
        {/* Sidebar */}
        <aside
          className={cn(
            "sticky top-0 hidden h-screen flex-col border-r border-blue-900 bg-[var(--blue-bg)] backdrop-blur md:flex",
            "transition-all duration-200",
            collapsed ? "w-[92px]" : "w-[260px]"
          )}
        >
          {/* Brand */}
          <div className="flex h-14 items-center justify-between px-3">
            <Link to="/" className="flex items-center gap-2 overflow-hidden">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl border border-slate-800 bg-slate-900/40">
                <span className="text-xs font-bold text-slate-200">W18</span>
              </div>
              {!collapsed && (
                <div className="min-w-0">
                  <div className="truncate text-sm font-semibold">Warehouse18</div>
                  <div className="truncate text-[11px] text-slate-500">RFID Inventory</div>
                </div>
              )}
            </Link>

            <button
              type="button"
              onClick={() => setCollapsed((v) => !v)}
              className={cn(
                "inline-flex h-9 w-9 items-center justify-center rounded-xl",
                "border border-slate-800 bg-slate-900/30",
                "hover:border-slate-700 hover:bg-slate-900/60 transition"
              )}
              aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
              title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
            >
              {collapsed ? (
                <ChevronRight className="h-4 w-4 text-slate-300" />
              ) : (
                <ChevronLeft className="h-4 w-4 text-slate-300" />
              )}
            </button>
          </div>

          {/* Nav */}
          <nav className="px-2 py-2">
            <div className="space-y-1">
              {NAV.map((it) => {
                const active =
                  it.href === "/" ? activeHref === "/" : activeHref.startsWith(it.href);

                const Icon = it.icon;

                return (
                  <Link
                    key={it.href}
                    to={it.href}
                    className={cn(
                      "group flex items-center gap-3 rounded-xl px-3 py-2",
                      "border border-transparent transition",
                      active
                        ? "bg-slate-900/50 border-slate-800"
                        : "hover:bg-slate-900/30 hover:border-slate-800"
                    )}
                    title={collapsed ? it.label : undefined}
                  >
                    <Icon
                      className={cn(
                        "h-5 w-5",
                        active ? "text-slate-100" : "text-slate-400 group-hover:text-slate-200"
                      )}
                    />
                    {!collapsed && (
                      <span className={cn("text-sm", active ? "text-slate-100" : "text-slate-300")}>
                        {it.label}
                      </span>
                    )}
                    <span
                      className={cn(
                        "ml-auto h-2 w-2 rounded-full",
                        active ? "bg-blue-500" : "bg-transparent"
                      )}
                    />
                  </Link>
                );
              })}
            </div>
          </nav>
          <div className="mt-auto px-2 pb-3">
            <SystemHealthBadge collapsed={collapsed} />
          </div>
        </aside>

        {/* Main */}
        <main className="min-w-0 flex-1 bg-[var(--white-bg)] text-zinc-900">
          {/* Header */}
          <header className="sticky top-0 z-10 border-b bg-slate-950/70 backdrop-blur">
            <div className="mx-auto flex w-full max-w-screen-2xl items-center justify-between gap-4 px-4 py-4 sm:px-6">
              <div className="min-w-0">
                <div className="truncate text-lg font-semibold text-slate-100">{title}</div>
                {subtitle ? (
                  <div className="truncate text-sm text-slate-400">{subtitle}</div>
                ) : null}
              </div>
              {actions ? <div className="flex items-center gap-2">{actions}</div> : null}
            </div>
          </header>

          {/* Content */}
          <div className="mx-auto w-full max-w-screen-2xl px-4 py-6 sm:px-6">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}