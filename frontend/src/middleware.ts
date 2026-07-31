/**
 * Next.js middleware.
 *
 * In clerk mode we run Clerk's middleware (required for Clerk to attach the auth
 * context to requests). In dev mode we pass through, so the app runs with no
 * Clerk configuration at all.
 */

import { clerkMiddleware } from "@clerk/nextjs/server";
import { NextResponse } from "next/server";

const middleware =
  process.env.NEXT_PUBLIC_AUTH_MODE === "clerk"
    ? clerkMiddleware()
    : () => NextResponse.next();

export default middleware;

export const config = {
  // Run on app routes, skipping Next internals and static files.
  matcher: ["/((?!_next/static|_next/image|favicon.ico|.*\\..*).*)"],
};
