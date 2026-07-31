"use client";

/**
 * Root client providers: React Query (server-state cache) + the active auth
 * provider. The auth provider is chosen from `AUTH_MODE` at build time:
 *   - clerk: wrap in <ClerkProvider> and bridge Clerk -> our AuthContext
 *   - dev:   use the offline DevAuthProvider
 * Downstream components only ever see `useAuth()`.
 */

import { ClerkProvider } from "@clerk/nextjs";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState, type ReactNode } from "react";

import { ClerkAuthBridge } from "@/lib/auth/clerk-auth";
import { DevAuthProvider } from "@/lib/auth/dev-auth";
import { AUTH_MODE } from "@/lib/config";

export function Providers({ children }: { children: ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: { staleTime: 30_000, retry: 1, refetchOnWindowFocus: false },
        },
      }),
  );

  const inner = (
    <QueryClientProvider client={queryClient}>
      {AUTH_MODE === "clerk" ? (
        <ClerkAuthBridge>{children}</ClerkAuthBridge>
      ) : (
        <DevAuthProvider>{children}</DevAuthProvider>
      )}
    </QueryClientProvider>
  );

  return AUTH_MODE === "clerk" ? <ClerkProvider>{inner}</ClerkProvider> : inner;
}
