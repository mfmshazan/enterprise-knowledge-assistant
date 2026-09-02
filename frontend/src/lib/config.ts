/** Centralized, typed access to public runtime config.
 *  `NEXT_PUBLIC_*` vars are inlined at build time by Next.js. */

export type AuthMode = "dev" | "clerk";

export const AUTH_MODE: AuthMode =
  process.env.NEXT_PUBLIC_AUTH_MODE === "clerk" ? "clerk" : "dev";

export const API_BASE_URL = (
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"
).replace(/\/+$/, "");
