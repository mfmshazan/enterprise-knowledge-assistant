"use client";

/**
 * Clerk bridge — adapts Clerk's hooks to our provider-agnostic `AuthState`.
 *
 * This component must render *inside* `<ClerkProvider>` (wired in Providers for
 * clerk mode). It is never mounted in dev mode, so Clerk hooks never run without
 * their provider.
 */

import { useAuth as useClerkAuth, useClerk, useUser } from "@clerk/nextjs";
import { useMemo, type ReactNode } from "react";

import { AuthContext, type AuthState } from "@/lib/auth/context";

export function ClerkAuthBridge({ children }: { children: ReactNode }) {
  const { isLoaded, isSignedIn, getToken } = useClerkAuth();
  const { user } = useUser();
  const clerk = useClerk();

  const value = useMemo<AuthState>(
    () => ({
      isLoaded,
      isSignedIn: Boolean(isSignedIn),
      userLabel: user?.primaryEmailAddress?.emailAddress ?? user?.fullName ?? null,
      getToken: () => getToken(),
      signOut: () => clerk.signOut(),
    }),
    [isLoaded, isSignedIn, user, getToken, clerk],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
