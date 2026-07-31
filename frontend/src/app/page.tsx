import Link from "next/link";

import { HealthStatus } from "@/components/health-status";

export default function Home() {
  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col justify-center gap-8 px-6 py-16">
      <header className="space-y-3">
        <h1 className="text-3xl font-semibold tracking-tight">
          🧠 Enterprise Knowledge Assistant
        </h1>
        <p className="text-[color:var(--color-muted)]">
          Phase 2 — authentication &amp; organizations. Sign in to create a
          workspace and manage members. Auth runs through a pluggable provider
          (dev or Clerk).
        </p>
      </header>

      <div className="flex gap-3">
        <Link
          href="/sign-in"
          className="rounded-md bg-[color:var(--color-accent)] px-4 py-2 text-sm font-medium text-white hover:opacity-90"
        >
          Sign in
        </Link>
        <Link
          href="/dashboard"
          className="rounded-md border border-white/10 px-4 py-2 text-sm hover:bg-white/5"
        >
          Go to dashboard
        </Link>
      </div>

      <HealthStatus />

      <footer className="text-sm text-[color:var(--color-muted)]">
        Next: document ingestion pipeline (Phase 3).
      </footer>
    </main>
  );
}
