"use client";

import { useState } from "react";
import type { ApiError, DocumentItem } from "@/lib/api";
import { useDeleteDocument, useDocuments } from "@/lib/documents";
import { StatusBadge } from "@/components/documents/status-badge";

function formatSize(bytes: number | null): string {
  if (!bytes) return "—";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatRelativeTime(dateString: string): string {
  try {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / (1000 * 60));
    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays}d ago`;
  } catch {
    return "Recently";
  }
}

export function DocumentList({ orgId }: { orgId: string }) {
  const documents = useDocuments(orgId);
  const remove = useDeleteDocument(orgId);

  const [activeFilter, setActiveFilter] = useState<"recent" | "starred" | "private">("recent");
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");
  const [starredIds, setStarredIds] = useState<Record<string, boolean>>({});

  const toggleStar = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setStarredIds((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  if (documents.isLoading) {
    return (
      <div className="rounded-2xl border border-slate-200 bg-white p-8 text-center text-sm text-slate-500 shadow-sm">
        <span className="inline-block animate-spin mr-2">⏳</span> Loading documents…
      </div>
    );
  }

  if (documents.error) {
    return (
      <div className="rounded-2xl border border-rose-200 bg-rose-50 p-6 text-sm text-rose-600 shadow-sm">
        {(documents.error as ApiError).message}
      </div>
    );
  }

  const allDocs = documents.data ?? [];
  const docs =
    activeFilter === "starred"
      ? allDocs.filter((d) => !!starredIds[d.id])
      : allDocs;

  return (
    <div className="space-y-4">
      {/* Header bar with Filters */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="text-slate-400 select-none text-base">⠿</span>
            <h2 className="text-base font-bold text-slate-900 tracking-tight">Documents</h2>
          </div>
          <span className="text-xs font-semibold text-indigo-600 hover:text-indigo-700 cursor-pointer">
            View all
          </span>
        </div>

        {/* Filter Pills + View Toggle */}
        <div className="flex items-center justify-between sm:justify-end gap-2">
          <div className="flex items-center gap-1 rounded-xl bg-slate-100 p-1 text-xs font-medium">
            <button
              onClick={() => setActiveFilter("recent")}
              className={`rounded-lg px-3 py-1 transition-all ${
                activeFilter === "recent"
                  ? "bg-white text-indigo-700 font-semibold shadow-2xs"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Recent
            </button>
            <button
              onClick={() => setActiveFilter("starred")}
              className={`rounded-lg px-3 py-1 transition-all ${
                activeFilter === "starred"
                  ? "bg-white text-indigo-700 font-semibold shadow-2xs"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Starred
            </button>
            <button
              onClick={() => setActiveFilter("private")}
              className={`rounded-lg px-3 py-1 transition-all ${
                activeFilter === "private"
                  ? "bg-white text-indigo-700 font-semibold shadow-2xs"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Private space
            </button>
          </div>

          {/* Grid / List switch */}
          <div className="flex items-center rounded-lg border border-slate-200 bg-white p-0.5 text-xs text-slate-500">
            <button
              onClick={() => setViewMode("grid")}
              className={`p-1.5 rounded ${viewMode === "grid" ? "bg-slate-100 text-slate-900 font-bold" : "hover:text-slate-800"}`}
              title="Grid view"
            >
              ⊞
            </button>
            <button
              onClick={() => setViewMode("list")}
              className={`p-1.5 rounded ${viewMode === "list" ? "bg-slate-100 text-slate-900 font-bold" : "hover:text-slate-800"}`}
              title="List view"
            >
              ☰
            </button>
          </div>
        </div>
      </div>

      {/* Empty State */}
      {docs.length === 0 ? (
        <div className="rounded-2xl border-2 border-dashed border-slate-200 bg-white/70 p-10 text-center shadow-xs">
          <span className="text-3xl">📄</span>
          <h3 className="mt-2 text-sm font-semibold text-slate-800">
            {activeFilter === "starred" ? "No starred documents" : "No documents yet"}
          </h3>
          <p className="mt-1 text-xs text-slate-500 max-w-sm mx-auto">
            {activeFilter === "starred"
              ? "Star documents to quickly access them in this view."
              : "Upload a PDF, DOCX, TXT file or add a web URL in the Add Knowledge panel below."}
          </p>
        </div>
      ) : viewMode === "grid" ? (
        /* Zendesk Document Cards Grid */
        <div className="grid gap-3.5 sm:grid-cols-2 lg:grid-cols-3">
          {docs.map((doc: DocumentItem) => (
            <div
              key={doc.id}
              className="group relative flex flex-col justify-between rounded-2xl border border-slate-200/80 bg-white p-4 shadow-sm transition-all hover:border-slate-300 hover:shadow-md min-h-[160px]"
            >
              <div>
                {/* Card Top: Preview icon & Star button */}
                <div className="flex items-start justify-between">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-50 text-slate-600 border border-slate-100 group-hover:bg-indigo-50 group-hover:text-indigo-600 transition-colors">
                    {doc.source_type === "url" ? (
                      <span className="text-base">🌐</span>
                    ) : doc.filename?.endsWith(".pdf") ? (
                      <span className="text-base">📕</span>
                    ) : (
                      <span className="text-base">📄</span>
                    )}
                  </div>
                  <div className="flex items-center gap-1">
                    <button
                      type="button"
                      onClick={(e) => toggleStar(doc.id, e)}
                      className="p-1 text-slate-300 hover:text-amber-400 transition-colors"
                      title="Star document"
                    >
                      {starredIds[doc.id] ? (
                        <span className="text-amber-400">★</span>
                      ) : (
                        <span>☆</span>
                      )}
                    </button>
                    <button
                      onClick={() => remove.mutate(doc.id)}
                      disabled={remove.isPending}
                      className="opacity-0 group-hover:opacity-100 p-1 text-slate-400 hover:text-rose-600 transition-all text-xs"
                      title="Delete document"
                    >
                      ✕
                    </button>
                  </div>
                </div>

                {/* Card Title */}
                <h3
                  className="mt-3 text-sm font-semibold text-slate-800 line-clamp-2 leading-snug group-hover:text-indigo-600 transition-colors"
                  title={doc.title}
                >
                  {doc.title}
                </h3>

                <p className="mt-1 text-[11px] text-slate-500 truncate">
                  {doc.source_type === "url" ? doc.source_url : doc.filename}
                </p>
              </div>

              {/* Card Footer: Timestamp & Status badge */}
              <div className="mt-4 flex items-center justify-between border-t border-slate-100 pt-2.5 text-[11px] text-slate-400">
                <span>{formatRelativeTime(doc.created_at)}</span>
                <div className="flex items-center gap-1.5">
                  {doc.status === "indexed" && (
                    <span className="text-slate-500 font-medium">
                      {doc.chunk_count} chunks
                    </span>
                  )}
                  <StatusBadge status={doc.status} />
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        /* Compact List View */
        <div className="rounded-2xl border border-slate-200/80 bg-white overflow-hidden shadow-sm">
          <ul className="divide-y divide-slate-100">
            {docs.map((doc: DocumentItem) => (
              <li
                key={doc.id}
                className="flex items-center justify-between gap-4 px-4 py-3 hover:bg-slate-50/80 transition-colors"
              >
                <div className="flex items-center gap-3 min-w-0">
                  <span className="text-base select-none">
                    {doc.source_type === "url" ? "🌐" : "📄"}
                  </span>
                  <div className="min-w-0">
                    <p className="truncate text-sm font-semibold text-slate-800">
                      {doc.title}
                    </p>
                    <p className="text-xs text-slate-400 truncate">
                      {doc.source_type === "url" ? doc.source_url : doc.filename} ·{" "}
                      {formatSize(doc.size_bytes)}
                      {doc.status === "indexed" && ` · ${doc.chunk_count} chunks`}
                    </p>
                  </div>
                </div>

                <div className="flex shrink-0 items-center gap-3">
                  <span className="text-xs text-slate-400">
                    {formatRelativeTime(doc.created_at)}
                  </span>
                  <StatusBadge status={doc.status} />
                  <button
                    onClick={() => remove.mutate(doc.id)}
                    disabled={remove.isPending}
                    className="text-xs font-semibold text-slate-400 hover:text-rose-600 disabled:opacity-50"
                  >
                    Delete
                  </button>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
