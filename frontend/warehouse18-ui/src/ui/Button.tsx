import React from "react";

type Props = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "outline" | "ghost" | "danger";
  size?: "sm" | "md";
};

export function Button({
  variant = "primary",
  size = "md",
  className = "",
  type = "button",
  ...props
}: Props) {
  const base =
    "inline-flex items-center justify-center gap-2 rounded-xl font-medium transition-colors " +
    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-zinc-400 focus-visible:ring-offset-2 " +
    "disabled:opacity-50 disabled:pointer-events-none ring-offset-zinc-50";

  const sizes =
    size === "sm" ? "h-9 px-3 text-sm" : "h-10 px-4 text-sm";

  const styles =
    variant === "primary"
      ? "bg-zinc-900 text-white hover:bg-zinc-800"
      : variant === "secondary"
      ? "bg-zinc-100 text-zinc-900 hover:bg-zinc-200"
      : variant === "outline"
      ? "border border-zinc-200 bg-white text-zinc-900 hover:bg-zinc-50"
      : variant === "danger"
      ? "bg-red-600 text-white hover:bg-red-500"
      : "bg-transparent text-zinc-700 hover:bg-zinc-100";

  return (
    <button className={`${base} ${sizes} ${styles} ${className}`} {...props} />
  );
}
