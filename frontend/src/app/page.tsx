import { HealthStatus } from "@/components/health-status";

export default function Home() {
  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col justify-center gap-8 px-6 py-16">
      <header className="space-y-3">
        <h1 className="text-3xl font-semibold tracking-tight">
          🧠 Enterprise Knowledge Assistant
        </h1>
        <p className="text-[color:var(--color-muted)]">
          Phase 1 — the full stack is wired up. This page fetches the backend
          <code className="mx-1 rounded bg-white/10 px-1.5 py-0.5">/health</code>
          endpoint through the typed API client and React Query.
        </p>
      </header>

      <HealthStatus />

      <footer className="text-sm text-[color:var(--color-muted)]">
        Next: authentication &amp; organizations (Phase 2).
      </footer>
    </main>
  );
}
