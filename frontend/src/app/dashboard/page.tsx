"use client";

/**
 * Protected dashboard.
 *
 * Demonstrates the full Phase 2 loop from the browser: it reads the session via
 * `useAuth()`, redirects to /sign-in when signed out, then calls the protected
 * `/users/me` and `/orgs` endpoints (with the bearer token attached) and lets
 * the user create an organization.
 */

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth/context";
import { useCreateOrg, useMe } from "@/lib/hooks";

function CreateOrgForm() {
  const createOrg = useCreateOrg();
  const [name, setName] = useState("");

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    createOrg.mutate({ name: name.trim() }, { onSuccess: () => setName("") });
  };

  return (
    <form onSubmit={onSubmit} className="flex flex-col gap-2 sm:flex-row">
      <input
        value={name}
        onChange={(e) => setName(e.target.value)}
        placeholder="New organization name"
        className="flex-1 rounded-md border border-white/10 bg-black/30 px-3 py-2 text-sm"
      />
      <button
        type="submit"
        disabled={createOrg.isPending}
        className="rounded-md bg-[color:var(--color-accent)] px-4 py-2 text-sm font-medium text-white hover:opacity-90 disabled:opacity-50"
      >
        {createOrg.isPending ? "Creating…" : "Create"}
      </button>
      {createOrg.error && (
        <span className="self-center text-sm text-red-400">
          {(createOrg.error as ApiError).message}
        </span>
      )}
    </form>
  );
}

export default function DashboardPage() {
  const { isLoaded, isSignedIn, userLabel, signOut } = useAuth();
  const router = useRouter();
  const me = useMe();

  useEffect(() => {
    if (isLoaded && !isSignedIn) router.replace("/sign-in");
  }, [isLoaded, isSignedIn, router]);

  if (!isLoaded || !isSignedIn) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <p className="text-[color:var(--color-muted)]">Loading…</p>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-2xl space-y-8 px-6 py-12">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Dashboard</h1>
          <p className="text-sm text-[color:var(--color-muted)]">
            Signed in as {userLabel ?? "unknown"}
          </p>
        </div>
        <button
          onClick={() => {
            void signOut();
            router.replace("/sign-in");
          }}
          className="rounded-md border border-white/10 px-3 py-1.5 text-sm hover:bg-white/5"
        >
          Sign out
        </button>
      </header>

      <section className="space-y-3 rounded-xl border border-white/10 bg-white/5 p-5">
        <h2 className="font-medium">Your organizations</h2>
        {me.isLoading && <p className="text-sm text-[color:var(--color-muted)]">Loading…</p>}
        {me.error && (
          <p className="text-sm text-red-400">{(me.error as ApiError).message}</p>
        )}
        {me.data && me.data.memberships.length === 0 && (
          <p className="text-sm text-[color:var(--color-muted)]">
            No organizations yet — create your first one below.
          </p>
        )}
        {me.data && me.data.memberships.length > 0 && (
          <ul className="divide-y divide-white/10">
            {me.data.memberships.map((m) => (
              <li key={m.id} className="flex items-center justify-between py-2">
                <span>{m.organization.name}</span>
                <span className="rounded-full bg-white/10 px-2 py-0.5 text-xs uppercase tracking-wide">
                  {m.role}
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="space-y-3 rounded-xl border border-white/10 bg-white/5 p-5">
        <h2 className="font-medium">Create an organization</h2>
        <CreateOrgForm />
      </section>
    </main>
  );
}
