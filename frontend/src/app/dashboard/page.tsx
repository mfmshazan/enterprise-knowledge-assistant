"use client";

import Link from "next/link";
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
    <form onSubmit={onSubmit} className="flex flex-col gap-2.5 sm:flex-row">
      <input
        value={name}
        onChange={(e) => setName(e.target.value)}
        placeholder="e.g. Acme Support Team"
        className="flex-1 rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-xs sm:text-sm text-slate-800 placeholder:text-slate-400 focus:border-indigo-500 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500/10"
      />
      <button
        type="submit"
        disabled={createOrg.isPending || !name.trim()}
        className="rounded-xl bg-indigo-600 px-5 py-2.5 text-xs sm:text-sm font-semibold text-white shadow-sm hover:bg-indigo-700 disabled:opacity-50 transition-colors"
      >
        {createOrg.isPending ? "Creating…" : "Create Organization"}
      </button>
      {createOrg.error && (
        <span className="self-center text-xs text-rose-500 font-medium">
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
      <main className="flex min-h-screen items-center justify-center ambient-canvas">
        <div className="flex items-center gap-2 text-sm font-medium text-slate-500">
          <span className="animate-spin text-lg">⏳</span> Loading dashboard…
        </div>
      </main>
    );
  }

  const displayName = userLabel ? userLabel.split("@")[0] : "User";

  return (
    <div className="min-h-screen ambient-canvas pb-20 pt-10">
      <main className="mx-auto max-w-3xl space-y-6 px-4 sm:px-6">
        {/* Header */}
        <header className="flex items-center justify-between rounded-2xl border border-slate-200/80 bg-white/90 p-5 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-indigo-50 text-xl font-bold text-indigo-600">
              {displayName.charAt(0).toUpperCase()}
            </div>
            <div>
              <h1 className="text-lg font-bold text-slate-900 tracking-tight">
                Welcome, {displayName}!
              </h1>
              <p className="text-xs text-slate-500">{userLabel}</p>
            </div>
          </div>
          <button
            onClick={() => {
              void signOut();
              router.replace("/sign-in");
            }}
            className="rounded-xl border border-slate-200 bg-white px-3.5 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-50 hover:text-slate-900 transition-colors shadow-2xs"
          >
            Sign out
          </button>
        </header>

        {/* Organizations List Card */}
        <section className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div className="flex items-center gap-2">
              <span className="text-slate-400 select-none text-base">⠿</span>
              <h2 className="text-sm font-bold text-slate-900 tracking-tight">Your Organizations</h2>
            </div>
            <span className="text-xs font-medium text-slate-400">
              {me.data?.memberships.length ?? 0} active
            </span>
          </div>

          {me.isLoading && (
            <p className="py-6 text-center text-xs text-slate-400 animate-pulse">
              Loading your workspaces…
            </p>
          )}

          {me.error && (
            <p className="rounded-xl bg-rose-50 p-3 text-xs font-medium text-rose-600">
              {(me.error as ApiError).message}
            </p>
          )}

          {me.data && me.data.memberships.length === 0 && (
            <div className="py-8 text-center">
              <span className="text-3xl">🏢</span>
              <p className="mt-2 text-xs text-slate-500 font-medium">
                No organizations yet. Create your first workspace below!
              </p>
            </div>
          )}

          {me.data && me.data.memberships.length > 0 && (
            <div className="grid gap-3 sm:grid-cols-2">
              {me.data.memberships.map((m) => (
                <Link
                  key={m.id}
                  href={`/orgs/${m.organization.id}`}
                  className="group flex items-center justify-between rounded-xl border border-slate-200/70 bg-slate-50/50 p-4 transition-all hover:border-indigo-200 hover:bg-indigo-50/20 hover:shadow-xs"
                >
                  <div className="min-w-0 pr-2">
                    <div className="flex items-center gap-2">
                      <span className="text-base">🏢</span>
                      <h3 className="truncate text-sm font-semibold text-slate-800 group-hover:text-indigo-600 transition-colors">
                        {m.organization.name}
                      </h3>
                    </div>
                    <p className="mt-1 text-[11px] text-slate-400 truncate">
                      slug: {m.organization.slug}
                    </p>
                  </div>
                  <span className="shrink-0 rounded-full border border-indigo-200 bg-indigo-50 px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider text-indigo-700">
                    {m.role}
                  </span>
                </Link>
              ))}
            </div>
          )}
        </section>

        {/* Create Organization Card */}
        <section className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-sm space-y-3">
          <div className="flex items-center gap-2">
            <span className="text-indigo-600 text-sm">➕</span>
            <h2 className="text-sm font-bold text-slate-900 tracking-tight">
              Create New Organization
            </h2>
          </div>
          <p className="text-xs text-slate-500">
            Set up an isolated workspace for a new department, client, or team knowledge base.
          </p>
          <CreateOrgForm />
        </section>
      </main>
    </div>
  );
}
