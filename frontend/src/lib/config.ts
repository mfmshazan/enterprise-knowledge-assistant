/** Centralized, typed access to public runtime config.
 *  `NEXT_PUBLIC_*` vars are inlined at build time by Next.js. */

export type AuthMode = "dev" | "clerk";

export const AUTH_MODE: AuthMode =
  process.env.NEXT_PUBLIC_AUTH_MODE === "clerk" ? "clerk" : "dev";

const PRODUCTION_API_URL = "https://enterprise-knowledge-assistant-api-r2jf.onrender.com";

export const API_BASE_URL = (
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  (typeof window !== "undefined" && !window.location.hostname.includes("localhost")
    ? PRODUCTION_API_URL
    : process.env.NODE_ENV === "production"
    ? PRODUCTION_API_URL
    : "http://localhost:8000")
).replace(/\/+$/, "");
