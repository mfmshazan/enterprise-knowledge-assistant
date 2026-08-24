"use client";

import type { ApiError, DocumentItem } from "@/lib/api";
import { useDeleteDocument, useDocuments } from "@/lib/documents";
import { StatusBadge } from "@/components/documents/status-badge";

function formatSize(bytes: number | null): string {
  if (!bytes) return "—";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function DocumentList({ orgId }: { orgId: string }) {
  const documents = useDocuments(orgId);
  const remove = useDeleteDocument(orgId);

  if (documents.isLoading) {
    return <p className="text-sm text-[color:var(--color-muted)]">Loading documents…</p>;
  }
  if (documents.error) {
    return (
      <p className="text-sm text-red-400">{(documents.error as ApiError).message}</p>
    );
  }
  const docs = documents.data ?? [];
  if (docs.length === 0) {
    return (
      <p className="text-sm text-[color:var(--color-muted)]">
        No documents yet. Upload a file or add a URL to get started.
      </p>
    );
  }

  return (
    <ul className="divide-y divide-white/10">
      {docs.map((doc: DocumentItem) => (
        <li key={doc.id} className="flex items-center justify-between gap-4 py-3">
          <div className="min-w-0">
            <p className="truncate font-medium">{doc.title}</p>
            <p className="text-xs text-[color:var(--color-muted)]">
              {doc.source_type === "url" ? doc.source_url : doc.filename} · {formatSize(doc.size_bytes)}
              {doc.status === "indexed" && ` · ${doc.chunk_count} chunks`}
            </p>
            {doc.status === "failed" && doc.error && (
              <p className="mt-1 truncate text-xs text-red-400" title={doc.error}>
                {doc.error}
              </p>
            )}
          </div>
          <div className="flex shrink-0 items-center gap-3">
            <StatusBadge status={doc.status} />
            <button
              onClick={() => remove.mutate(doc.id)}
              disabled={remove.isPending}
              className="text-xs text-[color:var(--color-muted)] hover:text-red-400 disabled:opacity-50"
            >
              Delete
            </button>
          </div>
        </li>
      ))}
    </ul>
  );
}
