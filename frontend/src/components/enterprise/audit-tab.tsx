"use client";

import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@/lib/auth/context";
import { AuditLogEntry, listAuditLogs } from "@/lib/api";

interface AuditTabProps {
  orgId: string;
}

const actionColors: Record<string, { bg: string; text: string; label: string }> = {
  "document.upload": { bg: "bg-blue-500/10 border-blue-500/30", text: "text-blue-400", label: "Doc Upload" },
  "document.upload_url": { bg: "bg-cyan-500/10 border-cyan-500/30", text: "text-cyan-400", label: "URL Ingest" },
  "document.delete": { bg: "bg-rose-500/10 border-rose-500/30", text: "text-rose-400", label: "Doc Deleted" },
  "member.invite": { bg: "bg-emerald-500/10 border-emerald-500/30", text: "text-emerald-400", label: "Member Invite" },
  "member.role_update": { bg: "bg-purple-500/10 border-purple-500/30", text: "text-purple-400", label: "Role Change" },
  "member.remove": { bg: "bg-rose-500/10 border-rose-500/30", text: "text-rose-400", label: "Member Removed" },
  "api_key.create": { bg: "bg-amber-500/10 border-amber-500/30", text: "text-amber-400", label: "API Key Created" },
  "api_key.revoke": { bg: "bg-orange-500/10 border-orange-500/30", text: "text-orange-400", label: "API Key Revoked" },
  "chat.query": { bg: "bg-indigo-500/10 border-indigo-500/30", text: "text-indigo-400", label: "Chat Query" },
  "organization.create": { bg: "bg-emerald-500/10 border-emerald-500/30", text: "text-emerald-400", label: "Org Created" },
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
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <span>📜</span> Security & Audit Trail
          </h2>
          <p className="text-sm text-zinc-400 mt-1">
            Immutable audit trail of administrative events, access changes, document mutations, and LLM queries.
          </p>
        </div>

        {/* Filter */}
        <div className="flex items-center gap-3">
          <label className="text-xs text-zinc-400 font-medium">Filter Action:</label>
          <select
            value={actionFilter}
            onChange={(e) => {
              setActionFilter(e.target.value);
              setPage(1);
            }}
            className="bg-zinc-950 border border-zinc-700 text-zinc-200 text-xs rounded-lg px-3 py-2 focus:outline-none focus:ring-1 focus:ring-blue-500"
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
        </div>
      </div>

      {error && (
        <div className="p-3 bg-rose-500/10 border border-rose-500/30 text-rose-300 rounded-lg text-sm">
          ⚠ {error}
        </div>
      )}

      {/* Audit Log Table */}
      <div className="border border-zinc-800 rounded-xl overflow-hidden bg-zinc-900/60 shadow-lg backdrop-blur-sm">
        {loading ? (
          <div className="p-12 text-center text-zinc-400">Loading audit trail...</div>
        ) : logs.length === 0 ? (
          <div className="p-12 text-center text-zinc-400">No audit events recorded yet.</div>
        ) : (
          <table className="w-full text-left text-sm text-zinc-300">
            <thead className="bg-zinc-950/80 text-xs uppercase font-semibold text-zinc-400 border-b border-zinc-800">
              <tr>
                <th className="px-6 py-4">Action</th>
                <th className="px-6 py-4">Resource</th>
                <th className="px-6 py-4">Timestamp</th>
                <th className="px-6 py-4 text-right">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/60 font-mono text-xs">
              {logs.map((log) => {
                const conf = actionColors[log.action] || {
                  bg: "bg-zinc-800 text-zinc-300 border-zinc-700",
                  text: "text-zinc-300",
                  label: log.action,
                };
                return (
                  <tr key={log.id} className="hover:bg-zinc-800/40 transition-colors">
                    <td className="px-6 py-4 font-sans">
                      <span
                        className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold border ${conf.bg} ${conf.text}`}
                      >
                        {conf.label}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-zinc-200 font-medium">{log.resource_type}</div>
                      {log.resource_id && (
                        <div className="text-[11px] text-zinc-500 truncate max-w-[200px]">
                          {log.resource_id}
                        </div>
                      )}
                    </td>
                    <td className="px-6 py-4 text-zinc-400 font-sans">
                      {new Date(log.created_at).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 text-right font-sans">
                      <button
                        onClick={() => setSelectedLog(log)}
                        className="px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-200 text-xs font-medium transition-colors"
                      >
                        Inspect
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}

        {/* Pagination bar */}
        <div className="flex items-center justify-between px-6 py-3 bg-zinc-950/60 border-t border-zinc-800 text-xs text-zinc-400">
          <div>
            Showing {logs.length} of {total} events
          </div>
          <div className="flex items-center gap-2">
            <button
              disabled={page <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              className="px-3 py-1 rounded-lg bg-zinc-800 hover:bg-zinc-700 disabled:opacity-40 disabled:cursor-not-allowed text-white"
            >
              Previous
            </button>
            <span className="px-2 font-medium text-zinc-300">Page {page}</span>
            <button
              disabled={page * 25 >= total}
              onClick={() => setPage((p) => p + 1)}
              className="px-3 py-1 rounded-lg bg-zinc-800 hover:bg-zinc-700 disabled:opacity-40 disabled:cursor-not-allowed text-white"
            >
              Next
            </button>
          </div>
        </div>
      </div>

      {/* JSON Inspector Modal */}
      {selectedLog && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-zinc-900 border border-zinc-700 rounded-2xl p-6 max-w-lg w-full shadow-2xl space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-bold text-white flex items-center gap-2 font-mono text-sm">
                <span>🔍</span> Audit Event Inspector
              </h3>
              <button
                onClick={() => setSelectedLog(null)}
                className="text-zinc-400 hover:text-zinc-200 text-sm"
              >
                ✕
              </button>
            </div>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between border-b border-zinc-800 py-1.5">
                <span className="text-zinc-400">Event ID:</span>
                <span className="font-mono text-zinc-200">{selectedLog.id}</span>
              </div>
              <div className="flex justify-between border-b border-zinc-800 py-1.5">
                <span className="text-zinc-400">Action:</span>
                <span className="font-mono text-blue-400">{selectedLog.action}</span>
              </div>
              <div className="flex justify-between border-b border-zinc-800 py-1.5">
                <span className="text-zinc-400">Resource:</span>
                <span className="text-zinc-200">
                  {selectedLog.resource_type} ({selectedLog.resource_id || "N/A"})
                </span>
              </div>
              <div className="flex justify-between border-b border-zinc-800 py-1.5">
                <span className="text-zinc-400">Actor User ID:</span>
                <span className="font-mono text-zinc-300">{selectedLog.actor_user_id || "System"}</span>
              </div>
              <div className="flex justify-between border-b border-zinc-800 py-1.5">
                <span className="text-zinc-400">Timestamp:</span>
                <span className="text-zinc-300">{new Date(selectedLog.created_at).toISOString()}</span>
              </div>
            </div>

            <div>
              <div className="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2">
                Event Metadata Payload
              </div>
              <pre className="p-3.5 bg-zinc-950 border border-zinc-800 rounded-xl text-[11px] font-mono text-emerald-400 overflow-x-auto max-h-48">
                {JSON.stringify(selectedLog.metadata_, null, 2)}
              </pre>
            </div>

            <div className="flex justify-end pt-2">
              <button
                onClick={() => setSelectedLog(null)}
                className="px-4 py-2 rounded-xl bg-zinc-800 hover:bg-zinc-700 text-white text-xs font-medium"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
