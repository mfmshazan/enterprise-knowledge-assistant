import Link from "next/link";
import { HealthStatus } from "@/components/health-status";

export default function Home() {
  return (
    <div className="min-h-screen ambient-canvas flex flex-col justify-between py-12 px-6">
      <main className="mx-auto flex max-w-4xl flex-col justify-center gap-10">
        {/* Top Tag */}
        <header className="space-y-4">
          <div className="inline-flex items-center gap-2 rounded-full border border-indigo-200/80 bg-white/80 px-3.5 py-1 text-xs font-semibold text-indigo-700 shadow-xs backdrop-blur-sm">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-indigo-400 opacity-75"></span>
              <span className="relative inline-flex h-2 w-2 rounded-full bg-indigo-600"></span>
            </span>
            LangGraph Multi-Agent AI &amp; Self-Correcting RAG
          </div>

          <h1 className="text-4xl font-extrabold tracking-tight text-slate-900 sm:text-5xl">
            🧠 Enterprise Knowledge Assistant
          </h1>
          <p className="max-w-2xl text-base text-slate-600 leading-relaxed sm:text-lg">
            Upload enterprise documents and web knowledge, then let your organization query and receive{" "}
            <strong className="text-slate-900 font-semibold">fact-checked, cited answers</strong> powered by a
            multi-agent LangGraph workflow with real-time reasoning verification.
          </p>
        </header>

        {/* Action Buttons */}
        <div className="flex flex-wrap items-center gap-3.5">
          <Link
            href="/dashboard"
            className="flex items-center gap-2 rounded-xl bg-indigo-600 px-6 py-3 text-sm font-semibold text-white shadow-md shadow-indigo-600/20 transition-all hover:bg-indigo-700 hover:shadow-lg active:scale-95"
          >
            <span>Go to dashboard</span>
            <span>→</span>
          </Link>
          <Link
            href="/sign-in"
            className="flex items-center gap-2 rounded-xl border border-slate-200/90 bg-white px-6 py-3 text-sm font-semibold text-slate-700 shadow-xs transition-all hover:bg-slate-50 hover:text-slate-900 active:scale-95"
          >
            <span>Sign in / Switch User</span>
          </Link>
        </div>

        {/* Feature Cards Grid */}
        <section className="grid gap-4 sm:grid-cols-3">
          <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-xs transition-all hover:shadow-md hover:border-slate-300">
            <div className="mb-2.5 flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-50 text-xl text-indigo-600">
              📥
            </div>
            <h3 className="text-sm font-bold text-slate-900">Ingestion Pipeline</h3>
            <p className="mt-1.5 text-xs text-slate-500 leading-relaxed">
              PDF, DOCX, TXT, and Web scraping with recursive chunking and 3072-dimensional vector indexing.
            </p>
          </div>

          <div className="rounded-2xl border border-indigo-200 bg-indigo-50/40 p-5 shadow-xs transition-all hover:shadow-md hover:border-indigo-300">
            <div className="mb-2.5 flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-100 text-xl text-indigo-700">
              🧠
            </div>
            <h3 className="text-sm font-bold text-indigo-950">LangGraph Agents</h3>
            <p className="mt-1.5 text-xs text-slate-600 leading-relaxed">
              Multi-agent cycle (Planner → Retriever → Generator → Verifier) eliminating hallucinations.
            </p>
          </div>

          <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-xs transition-all hover:shadow-md hover:border-slate-300">
            <div className="mb-2.5 flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-50 text-xl text-emerald-600">
              📚
            </div>
            <h3 className="text-sm font-bold text-slate-900">Verified Citations</h3>
            <p className="mt-1.5 text-xs text-slate-500 leading-relaxed">
              Traceable source passages and rank attribution linked directly to each assistant answer.
            </p>
          </div>
        </section>

        {/* System Health */}
        <HealthStatus />
      </main>

      <footer className="mx-auto w-full max-w-4xl flex items-center justify-between border-t border-slate-200 pt-6 text-xs text-slate-400">
        <span>Enterprise Knowledge Assistant</span>
        <span>Secure Multi-Tenant RAG • Production Ready</span>
      </footer>
    </div>
  );
}
