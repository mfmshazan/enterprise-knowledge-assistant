"use client";

import { useState } from "react";
import { Globe, FileText, File, Star, Trash2, LayoutGrid, List } from "lucide-react";

import type { ApiError, DocumentItem } from "@/lib/api";
import { useDeleteDocument, useDocuments } from "@/lib/documents";
import { StatusBadge } from "@/components/documents/status-badge";
import { Skeleton } from "@/components/ui/skeleton";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { useToast } from "@/components/ui/toast";

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

function DocIcon({ doc, className = "h-4 w-4" }: { doc: DocumentItem; className?: string }) {
  if (doc.source_type === "url") return <Globe className={className} aria-hidden />;
  if (doc.filename?.endsWith(".pdf")) return <FileText className={className} aria-hidden />;
  return <File className={className} aria-hidden />;
}

export function DocumentList({ orgId }: { orgId: string }) {
  const documents = useDocuments(orgId);
  const remove = useDeleteDocument(orgId);
  const { toast } = useToast();

  const [activeFilter, setActiveFilter] = useState<"recent" | "starred" | "private">("recent");
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");
  const [starredIds, setStarredIds] = useState<Record<string, boolean>>({});
  const [deleteTarget, setDeleteTarget] = useState<DocumentItem | null>(null);

  const toggleStar = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setStarredIds((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const confirmDelete = () => {
    if (!deleteTarget) return;
    const title = deleteTarget.title;
    remove.mutate(deleteTarget.id, {
      onSuccess: () => toast(`Deleted "${title}".`, "success"),
      onError: (err) => toast((err as ApiError).message, "error"),
    });
    setDeleteTarget(null);
  };

  if (documents.isLoading) {
    return (
      <div className="grid gap-3.5 sm:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <div
            key={i}
            className="flex min-h-[160px] flex-col justify-between rounded-2xl border border-slate-200/80 bg-white p-4 shadow-sm"
          >
            <div className="flex items-start justify-between">
              <Skeleton className="h-10 w-10 rounded-xl" />
            </div>
            <div className="space-y-2">
              <Skeleton className="h-3.5 w-3/4" />
              <Skeleton className="h-2.5 w-1/2" />
            </div>
          </div>
        ))}
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
  const docs = activeFilter === "starred" ? allDocs.filter((d) => !!starredIds[d.id]) : allDocs;

  return (
    <div className="space-y-4">
      {/* Header bar with Filters */}
      <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
        <div className="flex items-center gap-3">
          <h2 className="text-base font-bold tracking-tight text-slate-900">Documents</h2>
          <span className="text-xs font-medium text-slate-400">{allDocs.length} total</span>
        </div>

        {/* Filter Pills + View Toggle */}
        <div className="flex items-center justify-between gap-2 sm:justify-end">
          <div className="flex items-center gap-1 rounded-xl bg-slate-100 p-1 text-xs font-medium">
            {(["recent", "starred", "private"] as const).map((f) => (
              <button
                key={f}
                onClick={() => setActiveFilter(f)}
                className={`rounded-lg px-3 py-1 capitalize transition-all ${
                  activeFilter === f
                    ? "bg-white font-semibold text-indigo-700 shadow-2xs"
                    : "text-slate-600 hover:text-slate-900"
                }`}
              >
                {f === "private" ? "Private space" : f}
              </button>
            ))}
          </div>

          {/* Grid / List switch */}
          <div className="flex items-center rounded-lg border border-slate-200 bg-white p-0.5 text-slate-500">
            <button
              onClick={() => setViewMode("grid")}
              aria-label="Grid view"
              className={`rounded p-1.5 ${viewMode === "grid" ? "bg-slate-100 text-slate-900" : "hover:text-slate-800"}`}
            >
              <LayoutGrid className="h-3.5 w-3.5" aria-hidden />
            </button>
            <button
              onClick={() => setViewMode("list")}
              aria-label="List view"
              className={`rounded p-1.5 ${viewMode === "list" ? "bg-slate-100 text-slate-900" : "hover:text-slate-800"}`}
            >
              <List className="h-3.5 w-3.5" aria-hidden />
            </button>
          </div>
        </div>
      </div>

      {/* Empty State */}
      {docs.length === 0 ? (
        <div className="rounded-2xl border-2 border-dashed border-slate-200 bg-white/70 p-10 text-center shadow-xs">
          <FileText className="mx-auto h-8 w-8 text-slate-300" aria-hidden />
          <h3 className="mt-2 text-sm font-semibold text-slate-800">
            {activeFilter === "starred" ? "No starred documents" : "No documents yet"}
          </h3>
          <p className="mx-auto mt-1 max-w-sm text-xs text-slate-500">
            {activeFilter === "starred"
              ? "Star documents to quickly access them in this view."
              : "Upload a PDF, DOCX, TXT file or add a web URL in the Add Knowledge panel below."}
          </p>
        </div>
      ) : viewMode === "grid" ? (
        /* Document Cards Grid */
        <div className="grid gap-3.5 sm:grid-cols-2 lg:grid-cols-3">
          {docs.map((doc: DocumentItem) => (
            <div
              key={doc.id}
              className="group relative flex min-h-[160px] flex-col justify-between rounded-2xl border border-slate-200/80 bg-white p-4 shadow-sm transition-all hover:-translate-y-0.5 hover:border-slate-300 hover:shadow-md"
            >
              <div>
                {/* Card Top: Preview icon & Star button */}
                <div className="flex items-start justify-between">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-slate-100 bg-slate-50 text-slate-600 transition-colors group-hover:bg-indigo-50 group-hover:text-indigo-600">
                    <DocIcon doc={doc} className="h-5 w-5" />
                  </div>
                  <div className="flex items-center gap-1">
                    <button
                      type="button"
                      onClick={(e) => toggleStar(doc.id, e)}
                      aria-label={starredIds[doc.id] ? "Unstar document" : "Star document"}
                      className="p-1 text-slate-300 transition-colors hover:text-amber-400"
                    >
                      <Star
                        className={`h-4 w-4 ${starredIds[doc.id] ? "fill-amber-400 text-amber-400" : ""}`}
                        aria-hidden
                      />
                    </button>
                    <button
                      onClick={() => setDeleteTarget(doc)}
                      disabled={remove.isPending}
                      aria-label="Delete document"
                      className="p-1 text-slate-400 opacity-0 transition-all hover:text-rose-600 group-hover:opacity-100"
                    >
                      <Trash2 className="h-3.5 w-3.5" aria-hidden />
                    </button>
                  </div>
                </div>

                {/* Card Title */}
                <h3
                  className="mt-3 line-clamp-2 text-sm font-semibold leading-snug text-slate-800 transition-colors group-hover:text-indigo-600"
                  title={doc.title}
                >
                  {doc.title}
                </h3>

                <p className="mt-1 truncate text-[11px] text-slate-500">
                  {doc.source_type === "url" ? doc.source_url : doc.filename}
                </p>
              </div>

              {/* Card Footer: Timestamp & Status badge */}
              <div className="mt-4 flex items-center justify-between border-t border-slate-100 pt-2.5 text-[11px] text-slate-400">
                <span>{formatRelativeTime(doc.created_at)}</span>
                <div className="flex items-center gap-1.5">
                  {doc.status === "indexed" && (
                    <span className="font-medium text-slate-500">{doc.chunk_count} chunks</span>
                  )}
                  <StatusBadge status={doc.status} />
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        /* Compact List View */
        <div className="overflow-hidden rounded-2xl border border-slate-200/80 bg-white shadow-sm">
          <ul className="divide-y divide-slate-100">
            {docs.map((doc: DocumentItem) => (
              <li
                key={doc.id}
                className="flex items-center justify-between gap-4 px-4 py-3 transition-colors hover:bg-slate-50/80"
              >
                <div className="flex min-w-0 items-center gap-3">
                  <span className="text-slate-500">
                    <DocIcon doc={doc} />
                  </span>
                  <div className="min-w-0">
                    <p className="truncate text-sm font-semibold text-slate-800">{doc.title}</p>
                    <p className="truncate text-xs text-slate-400">
                      {doc.source_type === "url" ? doc.source_url : doc.filename} ·{" "}
                      {formatSize(doc.size_bytes)}
                      {doc.status === "indexed" && ` · ${doc.chunk_count} chunks`}
                    </p>
                  </div>
                </div>

                <div className="flex shrink-0 items-center gap-3">
                  <span className="hidden text-xs text-slate-400 sm:inline">
                    {formatRelativeTime(doc.created_at)}
                  </span>
                  <StatusBadge status={doc.status} />
                  <button
                    onClick={() => setDeleteTarget(doc)}
                    disabled={remove.isPending}
                    aria-label="Delete document"
                    className="text-slate-400 transition-colors hover:text-rose-600 disabled:opacity-50"
                  >
                    <Trash2 className="h-4 w-4" aria-hidden />
                  </button>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}

      <ConfirmDialog
        open={deleteTarget !== null}
        title="Delete document"
        description={`Delete "${deleteTarget?.title}"? Its indexed chunks will be removed from the knowledge base. This cannot be undone.`}
        confirmLabel="Delete"
        danger
        loading={remove.isPending}
        onConfirm={confirmDelete}
        onCancel={() => setDeleteTarget(null)}
      />
    </div>
  );
}
