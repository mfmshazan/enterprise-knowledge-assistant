"use client";

/**
 * Development auth provider — no Clerk, no network.
 *
 * It stores a backend-compatible dev token (`dev:<email>[:<org>[:<role>]]`) in
 * localStorage and hands it to API calls. This lets the entire app be clicked
 * through offline, and pairs with the backend's `DevAuthProvider`.
 *
 * `useDevSignIn` is exposed *only* for the dev sign-in form; everything else
 * uses the provider-agnostic `useAuth()`.
 */

import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";

import { AuthContext, type AuthState } from "@/lib/auth/context";

const STORAGE_KEY = "eka.dev.token";

export interface DevSignInInput {
  email: string;
  orgSlug?: string;
  role?: "owner" | "admin" | "member";
}

function buildDevToken({ email, orgSlug, role }: DevSignInInput): string {
  const parts = [email.trim().toLowerCase()];
  if (orgSlug?.trim()) {
    parts.push(orgSlug.trim().toLowerCase());
    if (role) parts.push(role);
  }
  return `dev:${parts.join(":")}`;
}

// Module-level setter shared with the sign-in hook (single provider instance).
let externalSetToken: ((token: string | null) => void) | null = null;

export function useDevSignIn() {
  const signIn = useCallback((input: DevSignInInput) => {
    const token = buildDevToken(input);
    window.localStorage.setItem(STORAGE_KEY, token);
    externalSetToken?.(token);
  }, []);
  return { signIn };
}

export function DevAuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [isLoaded, setIsLoaded] = useState(false);

  useEffect(() => {
    setToken(window.localStorage.getItem(STORAGE_KEY));
    setIsLoaded(true);
    externalSetToken = setToken;
    return () => {
      externalSetToken = null;
    };
  }, []);

  const value = useMemo<AuthState>(() => {
    const email = token?.startsWith("dev:") ? token.slice(4).split(":")[0] : null;
    return {
      isLoaded,
      isSignedIn: token !== null,
      userLabel: email,
      getToken: async () => token,
      signOut: () => {
        window.localStorage.removeItem(STORAGE_KEY);
        setToken(null);
      },
    };
  }, [token, isLoaded]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
