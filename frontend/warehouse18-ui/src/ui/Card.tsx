import { ReactNode } from "react";
import { cn } from "../lib/cn"; // si tienes helper para className (opcional)

interface CardProps {
  children: ReactNode;
  className?: string;
  clickable?: boolean;
}

export function Card({ children, className, clickable }: CardProps) {
  return (
    <div
      className={cn(
        "rounded-xl border border-slate-800 bg-slate-950/40",
        "transition-all duration-150",
        clickable && "hover:border-slate-700 hover:bg-slate-900/40 hover:translate-y-[-1px]",
        className
      )}
    >
      {children}
    </div>
  );
}