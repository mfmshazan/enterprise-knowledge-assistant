"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { DocumentList } from "@/components/documents/document-list";
import { UploadPanel } from "@/components/documents/upload-panel";
import { ApiKeysTab } from "@/components/enterprise/api-keys-tab";
import { AuditTab } from "@/components/enterprise/audit-tab";
import { TeamTab } from "@/components/enterprise/team-tab";
import { useAuth } from "@/lib/auth/context";

type WorkspaceTab = "documents" | "team" | "audit" | "api_keys";

export default function OrgWorkspacePage() {
  const { isLoaded, isSignedIn } = useAuth();
  const router = useRouter();
  const params = useParams<{ orgId: string }>();
  const orgId = params.orgId;
  const [activeTab, setActiveTab] = useState<WorkspaceTab>("documents");

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
    <main className="mx-auto max-w-5xl space-y-8 px-6 py-10">
      {/* Top Header */}
      <header className="space-y-3">
        <Link href="/dashboard" className="text-sm text-zinc-400 hover:text-zinc-200 transition-colors inline-flex items-center gap-1">
          ← Back to organizations
        </Link>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-extrabold text-white tracking-tight">Organization Workspace</h1>
            <p className="text-sm text-zinc-400 mt-1">
              Enterprise management hub for knowledge bases, access control, audit logs, and developer integrations.
            </p>
          </div>
          <Link
            href={`/orgs/${orgId}/chat`}
            className="inline-flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 px-5 py-2.5 text-sm font-semibold text-white shadow-lg shadow-blue-500/20 hover:from-blue-500 hover:to-indigo-500 transition-all active:scale-[0.98]"
          >
            <span>💬</span> Open AI Chat
          </Link>
        </div>
      </header>

      {/* Tab Navigation */}
      <div className="flex border-b border-zinc-800 space-x-1 overflow-x-auto scrollbar-none">
        <button
          onClick={() => setActiveTab("documents")}
          className={`flex items-center gap-2 px-5 py-3 border-b-2 font-medium text-sm transition-colors whitespace-nowrap ${
            activeTab === "documents"
              ? "border-blue-500 text-blue-400 bg-blue-500/5"
              : "border-transparent text-zinc-400 hover:text-zinc-200 hover:border-zinc-700"
          }`}
        >
          <span>📁</span> Knowledge Base
        </button>
        <button
          onClick={() => setActiveTab("team")}
          className={`flex items-center gap-2 px-5 py-3 border-b-2 font-medium text-sm transition-colors whitespace-nowrap ${
            activeTab === "team"
              ? "border-blue-500 text-blue-400 bg-blue-500/5"
              : "border-transparent text-zinc-400 hover:text-zinc-200 hover:border-zinc-700"
          }`}
        >
          <span>👥</span> Team & Roles
        </button>
        <button
          onClick={() => setActiveTab("audit")}
          className={`flex items-center gap-2 px-5 py-3 border-b-2 font-medium text-sm transition-colors whitespace-nowrap ${
            activeTab === "audit"
              ? "border-blue-500 text-blue-400 bg-blue-500/5"
              : "border-transparent text-zinc-400 hover:text-zinc-200 hover:border-zinc-700"
          }`}
        >
          <span>📜</span> Audit Trail
        </button>
        <button
          onClick={() => setActiveTab("api_keys")}
          className={`flex items-center gap-2 px-5 py-3 border-b-2 font-medium text-sm transition-colors whitespace-nowrap ${
            activeTab === "api_keys"
              ? "border-blue-500 text-blue-400 bg-blue-500/5"
              : "border-transparent text-zinc-400 hover:text-zinc-200 hover:border-zinc-700"
          }`}
        >
          <span>🔑</span> API Keys
        </button>
      </div>

      {/* Tab Contents */}
      <div className="pt-2">
        {activeTab === "documents" && (
          <div className="space-y-8">
            <section className="space-y-3 rounded-2xl border border-zinc-800 bg-zinc-900/60 p-6 shadow-xl backdrop-blur-sm">
              <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                <span>📤</span> Ingest Knowledge
              </h2>
              <UploadPanel orgId={orgId} />
            </section>

            <section className="space-y-3 rounded-2xl border border-zinc-800 bg-zinc-900/60 p-6 shadow-xl backdrop-blur-sm">
              <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                <span>📚</span> Document Index
              </h2>
              <DocumentList orgId={orgId} />
            </section>
          </div>
        )}

        {activeTab === "team" && <TeamTab orgId={orgId} />}

        {activeTab === "audit" && <AuditTab orgId={orgId} />}

        {activeTab === "api_keys" && <ApiKeysTab orgId={orgId} />}
      </div>
    </main>
  );
}
