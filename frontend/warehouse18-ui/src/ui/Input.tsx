import React from "react";

export function Input(props: React.InputHTMLAttributes<HTMLInputElement>) {
  const { className = "", ...rest } = props;

  return (
    <input
      {...rest}
      className={[
        "h-10 w-full rounded-xl border border-zinc-200 bg-white px-3 text-sm text-zinc-900",
        "placeholder:text-zinc-400",
        "shadow-sm",
        "outline-none transition",
        "focus:border-zinc-300 focus:ring-2 focus:ring-zinc-200",
        "disabled:opacity-50 disabled:pointer-events-none",
        className,
      ].join(" ")}
    />
  );
}
