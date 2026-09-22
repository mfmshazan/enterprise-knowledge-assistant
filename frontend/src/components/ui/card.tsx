import type { HTMLAttributes } from "react";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  /** Adds a hover lift for clickable cards. */
  interactive?: boolean;
}

/** Standard white surface matching the app's elevated card style. */
export function Card({ interactive = false, className = "", ...props }: CardProps) {
  return (
    <div
      className={`eka-card ${interactive ? "eka-card-interactive cursor-pointer" : ""} ${className}`}
      {...props}
    />
  );
}
