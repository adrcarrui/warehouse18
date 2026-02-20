import React from "react";

type Props = {
  children: React.ReactNode;
  variant?: "neutral" | "success" | "warning" | "danger";
};

export function Badge({ children, variant = "neutral" }: Props) {
  const styles =
    variant === "success"
      ? "border-green-200 bg-green-50 text-green-700"
      : variant === "warning"
      ? "border-amber-200 bg-amber-50 text-amber-700"
      : variant === "danger"
      ? "border-red-200 bg-red-50 text-red-700"
      : "border-zinc-200 bg-zinc-50 text-zinc-700";

  return (
    <span className={`inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-medium ${styles}`}>
      {children}
    </span>
  );
}
