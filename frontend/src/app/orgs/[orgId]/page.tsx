"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { FolderOpen, Users, ScrollText, KeyRound, MessageSquare, Loader2 } from "lucide-react";

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
      <main className="ambient-canvas flex min-h-screen items-center justify-center">
        <div className="flex items-center gap-2 text-sm font-medium text-slate-500">
          <Loader2 className="h-4 w-4 animate-spin" aria-hidden /> Loading workspace…
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
              className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2 text-xs font-semibold text-white shadow-sm transition-all hover:bg-indigo-700 active:scale-95"
            >
              <MessageSquare className="h-4 w-4" aria-hidden /> AI Chat
            </Link>
          </div>
        </div>

        {/* 1. Greeting & Ask AI Bar at the Top (no emoji) */}
        <AiAssistantBanner userName={userLabel} orgId={orgId} />

        {/* 2. The 4 Workspace Navigation Tabs Just Below the Ask AI Bar */}
        <div className="scrollbar-none flex items-center gap-2 overflow-x-auto border-b border-slate-200/80 pb-3 pt-1">
          {(
            [
              { id: "documents", label: "Knowledge Base", Icon: FolderOpen },
              { id: "team", label: "Team & Roles", Icon: Users },
              { id: "audit", label: "Audit Trail", Icon: ScrollText },
              { id: "api_keys", label: "API Keys", Icon: KeyRound },
            ] as const
          ).map(({ id, label, Icon }) => (
            <button
              key={id}
              onClick={() => setActiveTab(id)}
              className={`flex items-center gap-2 whitespace-nowrap rounded-xl px-4 py-2 text-xs font-semibold transition-all ${
                activeTab === id
                  ? "bg-slate-900 text-white shadow-sm"
                  : "text-slate-600 hover:bg-white hover:text-slate-900"
              }`}
            >
              <Icon className="h-4 w-4" aria-hidden /> {label}
            </button>
          ))}
        </div>

        {/* 3. Tab Contents */}
        <div className="pt-2">
          {activeTab === "documents" && (
            <div className="grid gap-6 lg:grid-cols-12 items-stretch">
              {/* Left Column: Documents Grid + Add Knowledge directly below */}
              <div className="lg:col-span-8 flex flex-col justify-between space-y-6">
                <DocumentList orgId={orgId} />
                <div className="flex-1 flex flex-col">
                  <UploadPanel orgId={orgId} />
                </div>
              </div>

              {/* Right Column: Analytics Widget + Knowledge Tasks */}
              <div className="lg:col-span-4 flex flex-col justify-between space-y-6">
                <AnalyticsWidget documents={docs} />
                <div className="flex-1 flex flex-col">
                  <TasksWidget documents={docs} orgId={orgId} />
                </div>
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
