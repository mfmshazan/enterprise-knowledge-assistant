import Link from "next/link";

import { HealthStatus } from "@/components/health-status";

export default function Home() {
  return (
    <main className="mx-auto flex min-h-screen max-w-4xl flex-col justify-center gap-10 px-6 py-16">
      <header className="space-y-4">
        <div className="inline-flex items-center gap-2 rounded-full border border-cyan-500/30 bg-cyan-950/30 px-3.5 py-1 text-xs font-medium text-cyan-300">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-cyan-400 opacity-75"></span>
            <span className="relative inline-flex h-2 w-2 rounded-full bg-cyan-500"></span>
          </span>
          Phase 6 Active: LangGraph Agentic AI &amp; Self-Correcting RAG
        </div>

        <h1 className="text-4xl font-bold tracking-tight text-white sm:text-5xl">
          🧠 Enterprise Knowledge Assistant
        </h1>
        <p className="max-w-2xl text-base text-[color:var(--color-muted)] sm:text-lg">
          Upload documents and websites, then let your organization query and receive
          <strong className="text-white"> fact-checked, cited answers</strong> powered by a
          multi-agent LangGraph workflow with real-time reasoning verification.
        </p>
      </header>

      <div className="flex flex-wrap gap-3.5">
        <Link
          href="/dashboard"
          className="flex items-center gap-2 rounded-xl bg-[color:var(--color-accent)] px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-[color:var(--color-accent)]/20 transition-transform hover:-translate-y-0.5 hover:opacity-95"
        >
          <span>Go to dashboard</span>
          <span>→</span>
        </Link>
        <Link
          href="/sign-in"
          className="flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-6 py-3 text-sm font-medium text-white transition-colors hover:bg-white/10"
        >
          <span>Sign in / Switch User</span>
        </Link>
      </div>

      <section className="grid gap-4 sm:grid-cols-3">
        <div className="rounded-2xl border border-white/10 bg-white/[0.02] p-5 backdrop-blur-sm">
          <div className="mb-2 text-2xl">📥</div>
          <h3 className="text-sm font-semibold text-white">Ingestion Pipeline</h3>
          <p className="mt-1 text-xs text-[color:var(--color-muted)]">
            PDF, DOCX, TXT, and Web scraping with recursive chunking and vector indexing.
          </p>
        </div>

        <div className="rounded-2xl border border-cyan-500/20 bg-cyan-950/10 p-5 backdrop-blur-sm">
          <div className="mb-2 text-2xl">🧠</div>
          <h3 className="text-sm font-semibold text-cyan-200">LangGraph Agents</h3>
          <p className="mt-1 text-xs text-[color:var(--color-muted)]">
            Multi-agent cycle (Planner → Retriever → Generator → Verifier) eliminating hallucinations.
          </p>
        </div>

        <div className="rounded-2xl border border-white/10 bg-white/[0.02] p-5 backdrop-blur-sm">
          <div className="mb-2 text-2xl">📚</div>
          <h3 className="text-sm font-semibold text-white">Verified Citations</h3>
          <p className="mt-1 text-xs text-[color:var(--color-muted)]">
            Traceable source passages and rank attribution linked directly to each assistant answer.
          </p>
        </div>
      </section>

      <HealthStatus />

      <footer className="flex items-center justify-between border-t border-white/10 pt-4 text-xs text-[color:var(--color-muted)]">
        <span>Enterprise Knowledge Assistant</span>
        <span>Phases 1–6 Complete • Next: Phase 7 (Enterprise Features)</span>
      </footer>
    </main>
  );
}

