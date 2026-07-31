"use client";

/**
 * The provider-agnostic auth contract the whole UI depends on.
 *
 * Both the dev provider and the Clerk bridge populate this same `AuthContext`,
 * so components call `useAuth()` without knowing or caring which backend is
 * active — the exact mirror of the backend's `AuthProvider` abstraction.
 */

import { createContext, useContext } from "react";

export interface AuthState {
  /** False until the provider has resolved the initial session (avoids flticker). */
  isLoaded: boolean;
  isSignedIn: boolean;
  /** Human-readable label for the signed-in user (email or name). */
  userLabel: string | null;
  /** Returns a bearer token to attach to API calls, or null if signed out. */
  getToken: () => Promise<string | null>;
  signOut: () => void | Promise<void>;
}

export const AuthContext = createContext<AuthState | null>(null);

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (ctx === null) {
    throw new Error("useAuth must be used within an <AuthProvider>.");
  }
  return ctx;
}
