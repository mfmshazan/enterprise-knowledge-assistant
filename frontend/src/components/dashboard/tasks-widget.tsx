"use client";

import Link from "next/link";
import { Activity, Globe, FileText, File, ArrowRight } from "lucide-react";

import type { DocumentItem } from "@/lib/api";
import { StatusBadge } from "@/components/documents/status-badge";

interface RecentActivityWidgetProps {
  documents: DocumentItem[];
  orgId: string;
}

function relativeTime(dateString: string): string {
  try {
    const diffMins = Math.floor((Date.now() - new Date(dateString).getTime()) / 60000);
    if (diffMins < 1) return "just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    const h = Math.floor(diffMins / 60);
    if (h < 24) return `${h}h ago`;
    return `${Math.floor(h / 24)}d ago`;
  } catch {
    return "recently";
  }
}

function DocIcon({ doc }: { doc: DocumentItem }) {
  const cls = "h-3.5 w-3.5 text-slate-400";
  if (doc.source_type === "url") return <Globe className={cls} aria-hidden />;
  if (doc.filename?.endsWith(".pdf")) return <FileText className={cls} aria-hidden />;
  return <File className={cls} aria-hidden />;
}

/**
 * Recent Activity — driven entirely by real document data (latest uploads with
 * their live ingestion status), replacing the former mock "Knowledge Tasks".
 */
export function TasksWidget({ documents, orgId }: RecentActivityWidgetProps) {
  const recent = [...documents]
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    .slice(0, 5);

  return (
    <div className="eka-card flex h-full flex-col justify-between space-y-3.5 p-5">
      <div className="space-y-3.5">
        {/* Header */}
        <div className="flex items-center gap-2">
          <Activity className="h-4 w-4 text-indigo-500" aria-hidden />
          <h2 className="text-sm font-bold tracking-tight text-slate-800">Recent Activity</h2>
        </div>

        {/* Activity list */}
        <div className="divide-y divide-slate-100">
          {recent.length === 0 ? (
            <p className="py-4 text-center text-xs text-slate-400">
              No activity yet. Upload documents to get started.
            </p>
          ) : (
            recent.map((doc) => (
              <div key={doc.id} className="flex items-center justify-between gap-2 py-2.5">
                <div className="flex min-w-0 items-center gap-2.5">
                  <DocIcon doc={doc} />
                  <div className="min-w-0">
                    <p className="truncate text-xs font-medium text-slate-700" title={doc.title}>
                      {doc.title}
                    </p>
                    <p className="text-[10px] text-slate-400">{relativeTime(doc.created_at)}</p>
                  </div>
                </div>
                <StatusBadge status={doc.status} />
              </div>
            ))
          )}
        </div>
      </div>

      <div className="pt-2">
        <Link
          href={`/orgs/${orgId}/chat`}
          className="flex w-full items-center justify-center gap-1.5 rounded-xl bg-slate-50 py-2 text-xs font-semibold text-slate-600 transition-colors hover:bg-slate-100"
        >
          Ask AI about your documents
          <ArrowRight className="h-3.5 w-3.5" aria-hidden />
        </Link>
      </div>
    </div>
  );
}
