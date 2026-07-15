import type { ReactNode } from "react";
import { cn } from "../lib/cn";

interface CardProps {
  children: ReactNode;
  className?: string;
  clickable?: boolean;
}

export function Card({
  children,
  className,
  clickable,
}: CardProps) {
  return (
    <div
      className={cn(
        "rounded-xl border border-slate-800 bg-slate-950/40",
        "transition-all duration-150",
        clickable &&
          "hover:translate-y-[-1px] hover:border-slate-700 hover:bg-slate-900/40",
        className,
      )}
    >
      {children}
    </div>
  );
}