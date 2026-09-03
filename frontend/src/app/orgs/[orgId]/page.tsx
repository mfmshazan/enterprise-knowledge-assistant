"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { AiAssistantBanner } from "@/components/dashboard/ai-assistant-banner";
import { AnalyticsWidget } from "@/components/dashboard/analytics-widget";
import { TasksWidget } from "@/components/dashboard/tasks-widget";
import { DocumentList } from "@/components/documents/document-list";
import { UploadPanel } from "@/components/documents/upload-panel";
import { ApiKeysTab } from "@/components/enterprise/api-keys-tab";
import { AuditTab } from "@/components/enterprise/audit-tab";
import { TeamTab } from "@/components/enterprise/team-tab";
import { useAuth } from "@/lib/auth/context";
import { useDocuments } from "@/lib/documents";

type WorkspaceTab = "documents" | "team" | "audit" | "api_keys";

export default function OrgWorkspacePage() {
  const { isLoaded, isSignedIn, userLabel } = useAuth();
  const router = useRouter();
  const params = useParams<{ orgId: string }>();
  const orgId = params.orgId;
  const [activeTab, setActiveTab] = useState<WorkspaceTab>("documents");

  const documents = useDocuments(orgId);
  const docs = documents.data ?? [];

  useEffect(() => {
    if (isLoaded && !isSignedIn) router.replace("/sign-in");
  }, [isLoaded, isSignedIn, router]);

  if (!isLoaded || !isSignedIn) {
    return (
      <main className="flex min-h-screen items-center justify-center ambient-canvas">
        <div className="flex items-center gap-2 text-sm font-medium text-slate-500">
          <span className="animate-spin text-lg">⏳</span> Loading workspace…
        </div>
      </main>
    );
  }

  return (
    <div className="min-h-screen ambient-canvas pb-20">
      <main className="mx-auto max-w-6xl space-y-6 px-4 py-8 sm:px-6">
        {/* Top Navbar */}
        <div className="flex items-center justify-between">
          <Link
            href="/dashboard"
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-900 transition-colors"
          >
            <span>←</span> Back to organizations
          </Link>
          <div className="flex items-center gap-3">
            <Link
              href={`/orgs/${orgId}/chat`}
              className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2 text-xs font-semibold text-white shadow-sm hover:bg-indigo-700 transition-all active:scale-95"
            >
              <span>💬</span> AI Chat
            </Link>
          </div>
        </div>

        {/* Greeting & AI Assistant Prompt Bar */}
        <AiAssistantBanner userName={userLabel} orgId={orgId} />

        {/* Workspace Navigation Tabs */}
        <div className="flex items-center gap-2 border-b border-slate-200/80 pb-2 overflow-x-auto scrollbar-none pt-2">
          <button
            onClick={() => setActiveTab("documents")}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-xl font-semibold text-xs transition-all whitespace-nowrap ${
              activeTab === "documents"
                ? "bg-slate-900 text-white shadow-sm"
                : "text-slate-600 hover:bg-white hover:text-slate-900"
            }`}
          >
            <span>📁</span> Knowledge Base
          </button>
          <button
            onClick={() => setActiveTab("team")}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-xl font-semibold text-xs transition-all whitespace-nowrap ${
              activeTab === "team"
                ? "bg-slate-900 text-white shadow-sm"
                : "text-slate-600 hover:bg-white hover:text-slate-900"
            }`}
          >
            <span>👥</span> Team &amp; Roles
          </button>
          <button
            onClick={() => setActiveTab("audit")}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-xl font-semibold text-xs transition-all whitespace-nowrap ${
              activeTab === "audit"
                ? "bg-slate-900 text-white shadow-sm"
                : "text-slate-600 hover:bg-white hover:text-slate-900"
            }`}
          >
            <span>📜</span> Audit Trail
          </button>
          <button
            onClick={() => setActiveTab("api_keys")}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-xl font-semibold text-xs transition-all whitespace-nowrap ${
              activeTab === "api_keys"
                ? "bg-slate-900 text-white shadow-sm"
                : "text-slate-600 hover:bg-white hover:text-slate-900"
            }`}
          >
            <span>🔑</span> API Keys
          </button>
        </div>

        {/* Tab Contents */}
        <div className="pt-2">
          {activeTab === "documents" && (
            <div className="grid gap-6 lg:grid-cols-12">
              {/* Left Main Column: Documents Grid & Upload Panel */}
              <div className="space-y-6 lg:col-span-8">
                <DocumentList orgId={orgId} />
                <UploadPanel orgId={orgId} />
              </div>

              {/* Right Column: Analytics Widget & Knowledge Tasks */}
              <div className="space-y-6 lg:col-span-4">
                <AnalyticsWidget documents={docs} />
                <TasksWidget documents={docs} orgId={orgId} />
              </div>
            </div>
          )}

          {activeTab === "team" && (
            <div className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-sm">
              <TeamTab orgId={orgId} />
            </div>
          )}

          {activeTab === "audit" && (
            <div className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-sm">
              <AuditTab orgId={orgId} />
            </div>
          )}

          {activeTab === "api_keys" && (
            <div className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-sm">
              <ApiKeysTab orgId={orgId} />
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
