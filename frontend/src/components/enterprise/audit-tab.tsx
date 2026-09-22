"use client";

import { useCallback, useEffect, useState } from "react";
import { ScrollText, Search } from "lucide-react";

import { useAuth } from "@/lib/auth/context";
import { AuditLogEntry, listAuditLogs } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Badge, type BadgeTone } from "@/components/ui/badge";
import { Modal } from "@/components/ui/modal";
import { Skeleton } from "@/components/ui/skeleton";

interface AuditTabProps {
  orgId: string;
}

const actionMeta: Record<string, { tone: BadgeTone; label: string }> = {
  "document.upload": { tone: "blue", label: "Doc Upload" },
  "document.upload_url": { tone: "blue", label: "URL Ingest" },
  "document.delete": { tone: "rose", label: "Doc Deleted" },
  "member.invite": { tone: "emerald", label: "Member Invite" },
  "member.role_update": { tone: "violet", label: "Role Change" },
  "member.remove": { tone: "rose", label: "Member Removed" },
  "api_key.create": { tone: "amber", label: "API Key Created" },
  "api_key.revoke": { tone: "rose", label: "API Key Revoked" },
  "chat.query": { tone: "indigo", label: "Chat Query" },
  "organization.create": { tone: "emerald", label: "Org Created" },
};

export function AuditTab({ orgId }: AuditTabProps) {
  const { getToken } = useAuth();
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [actionFilter, setActionFilter] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedLog, setSelectedLog] = useState<AuditLogEntry | null>(null);

  const fetchLogs = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const token = await getToken();
      const res = await listAuditLogs(token, orgId, {
        action: actionFilter || undefined,
        page,
        page_size: 25,
      });
      setLogs(res.items);
      setTotal(res.total);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load audit logs");
    } finally {
      setLoading(false);
    }
  }, [actionFilter, getToken, orgId, page]);

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  return (
    <div className="space-y-6">
      {/* Header bar */}
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <h2 className="flex items-center gap-2 text-lg font-bold tracking-tight text-slate-900">
            <ScrollText className="h-5 w-5 text-indigo-500" aria-hidden /> Security &amp; Audit Trail
          </h2>
          <p className="mt-0.5 text-xs text-slate-500">
            Immutable audit trail of administrative events, access changes, document mutations, and
            LLM queries.
          </p>
        </div>

        {/* Filter */}
        <div className="flex items-center gap-2.5">
          <label className="text-xs font-semibold text-slate-600" htmlFor="audit-filter">
            Filter Action:
          </label>
          <div className="relative inline-block">
            <select
              id="audit-filter"
              value={actionFilter}
              onChange={(e) => {
                setActionFilter(e.target.value);
                setPage(1);
              }}
              className="cursor-pointer appearance-none rounded-xl border border-slate-200 bg-slate-50 py-2 pl-3 pr-8 text-xs font-semibold text-slate-800 shadow-2xs transition-all hover:bg-slate-100 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/10"
            >
              <option value="">All Actions ({total})</option>
              <option value="document.upload">Document Upload</option>
              <option value="document.delete">Document Delete</option>
              <option value="member.invite">Member Invite</option>
              <option value="member.role_update">Role Change</option>
              <option value="member.remove">Member Remove</option>
              <option value="api_key.create">API Key Created</option>
              <option value="api_key.revoke">API Key Revoked</option>
              <option value="chat.query">Chat Query</option>
            </select>
            <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-[10px] text-slate-400">
              ▼
            </span>
          </div>
        </div>
      </div>

      {error && (
        <div className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs font-semibold text-rose-800">
          {error}
        </div>
      )}

      {/* Audit Log Table */}
      <div className="overflow-hidden rounded-2xl border border-slate-200/80 bg-white shadow-xs">
        {loading ? (
          <div className="space-y-3 p-6">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-10 w-full" />
            ))}
          </div>
        ) : logs.length === 0 ? (
          <div className="p-12 text-center text-xs text-slate-400">No audit events recorded yet.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[640px] text-left text-sm text-slate-700">
              <thead className="border-b border-slate-100 bg-slate-50/80 text-[11px] font-bold uppercase tracking-wider text-slate-500">
                <tr>
                  <th className="px-6 py-3.5">Action</th>
                  <th className="px-6 py-3.5">Resource</th>
                  <th className="px-6 py-3.5">Timestamp</th>
                  <th className="px-6 py-3.5 text-right">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-xs">
                {logs.map((log) => {
                  const meta = actionMeta[log.action] ?? { tone: "neutral" as BadgeTone, label: log.action };
                  return (
                    <tr key={log.id} className="transition-colors hover:bg-slate-50/70">
                      <td className="px-6 py-3.5">
                        <Badge tone={meta.tone} uppercase>
                          {meta.label}
                        </Badge>
                      </td>
                      <td className="px-6 py-3.5">
                        <div className="font-semibold text-slate-900">{log.resource_type}</div>
                        {log.resource_id && (
                          <div className="max-w-[200px] truncate font-mono text-[11px] text-slate-400">
                            {log.resource_id}
                          </div>
                        )}
                      </td>
                      <td className="px-6 py-3.5 text-xs text-slate-500">
                        {new Date(log.created_at).toLocaleString()}
                      </td>
                      <td className="px-6 py-3.5 text-right">
                        <Button variant="secondary" size="sm" onClick={() => setSelectedLog(log)}>
                          <Search className="h-3.5 w-3.5" aria-hidden /> Inspect
                        </Button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination bar */}
        <div className="flex items-center justify-between border-t border-slate-100 bg-slate-50/80 px-6 py-3 text-xs text-slate-500">
          <div>
            Showing <span className="font-semibold text-slate-700">{logs.length}</span> of{" "}
            <span className="font-semibold text-slate-700">{total}</span> events
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="secondary"
              size="sm"
              disabled={page <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
            >
              Previous
            </Button>
            <span className="px-2 font-semibold text-slate-800">Page {page}</span>
            <Button
              variant="secondary"
              size="sm"
              disabled={page * 25 >= total}
              onClick={() => setPage((p) => p + 1)}
            >
              Next
            </Button>
          </div>
        </div>
      </div>

      {/* JSON Inspector Modal */}
      <Modal
        open={selectedLog !== null}
        onClose={() => setSelectedLog(null)}
        size="max-w-lg"
        title={
          <span className="flex items-center gap-2">
            <Search className="h-4 w-4 text-indigo-500" aria-hidden /> Audit Event Inspector
          </span>
        }
      >
        {selectedLog && (
          <div className="space-y-4">
            <div className="space-y-2 text-xs">
              <div className="flex justify-between border-b border-slate-100 py-1.5">
                <span className="text-slate-500">Event ID:</span>
                <span className="font-mono font-medium text-slate-800">{selectedLog.id}</span>
              </div>
              <div className="flex justify-between border-b border-slate-100 py-1.5">
                <span className="text-slate-500">Action:</span>
                <span className="font-mono font-semibold text-indigo-600">{selectedLog.action}</span>
              </div>
              <div className="flex justify-between border-b border-slate-100 py-1.5">
                <span className="text-slate-500">Resource:</span>
                <span className="font-medium text-slate-800">
                  {selectedLog.resource_type} ({selectedLog.resource_id || "N/A"})
                </span>
              </div>
              <div className="flex justify-between border-b border-slate-100 py-1.5">
                <span className="text-slate-500">Actor User ID:</span>
                <span className="font-mono text-slate-700">
                  {selectedLog.actor_user_id || "System"}
                </span>
              </div>
              <div className="flex justify-between border-b border-slate-100 py-1.5">
                <span className="text-slate-500">Timestamp:</span>
                <span className="text-slate-700">
                  {new Date(selectedLog.created_at).toISOString()}
                </span>
              </div>
            </div>

            <div>
              <div className="mb-2 text-[11px] font-bold uppercase tracking-wider text-slate-700">
                Event Metadata Payload
              </div>
              <pre className="max-h-48 overflow-x-auto rounded-xl border border-slate-800 bg-slate-900 p-3.5 font-mono text-xs leading-relaxed text-emerald-400">
                {JSON.stringify(selectedLog.metadata_, null, 2)}
              </pre>
            </div>

            <div className="flex justify-end pt-1">
              <Button variant="secondary" size="sm" onClick={() => setSelectedLog(null)}>
                Close
              </Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
