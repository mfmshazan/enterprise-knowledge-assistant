import type { ReactNode } from "react";

export type BadgeTone =
  | "neutral"
  | "indigo"
  | "emerald"
  | "amber"
  | "rose"
  | "blue"
  | "violet";

const TONES: Record<BadgeTone, string> = {
  neutral: "bg-slate-50 text-slate-600 border-slate-200",
  indigo: "bg-indigo-50 text-indigo-700 border-indigo-200",
  emerald: "bg-emerald-50 text-emerald-700 border-emerald-200",
  amber: "bg-amber-50 text-amber-700 border-amber-200",
  rose: "bg-rose-50 text-rose-700 border-rose-200",
  blue: "bg-blue-50 text-blue-700 border-blue-200",
  violet: "bg-violet-50 text-violet-700 border-violet-200",
};

const DOTS: Record<BadgeTone, string> = {
  neutral: "bg-slate-400",
  indigo: "bg-indigo-500",
  emerald: "bg-emerald-500",
  amber: "bg-amber-400",
  rose: "bg-rose-500",
  blue: "bg-blue-500",
  violet: "bg-violet-500",
};

interface BadgeProps {
  tone?: BadgeTone;
  /** Show a leading status dot. Pass "pulse" to animate it. */
  dot?: boolean | "pulse";
  uppercase?: boolean;
  className?: string;
  children: ReactNode;
}

/** Consistent pill badge used for statuses, roles, and audit actions. */
export function Badge({
  tone = "neutral",
  dot = false,
  uppercase = false,
  className = "",
  children,
}: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-[10px] font-semibold tracking-wider ${
        uppercase ? "uppercase" : ""
      } ${TONES[tone]} ${className}`}
    >
      {dot && (
        <span
          className={`h-1.5 w-1.5 rounded-full ${DOTS[tone]} ${
            dot === "pulse" ? "animate-pulse" : ""
          }`}
        />
      )}
      {children}
    </span>
  );
}
