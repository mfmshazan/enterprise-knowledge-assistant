"use client";

import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@/lib/auth/context";
import { AuditLogEntry, listAuditLogs } from "@/lib/api";

interface AuditTabProps {
  orgId: string;
}

const actionColors: Record<string, { bg: string; text: string; label: string }> = {
  "document.upload": { bg: "bg-blue-50 border-blue-200", text: "text-blue-700", label: "Doc Upload" },
  "document.upload_url": { bg: "bg-cyan-50 border-cyan-200", text: "text-cyan-700", label: "URL Ingest" },
  "document.delete": { bg: "bg-rose-50 border-rose-200", text: "text-rose-700", label: "Doc Deleted" },
  "member.invite": { bg: "bg-emerald-50 border-emerald-200", text: "text-emerald-700", label: "Member Invite" },
  "member.role_update": { bg: "bg-purple-50 border-purple-200", text: "text-purple-700", label: "Role Change" },
  "member.remove": { bg: "bg-rose-50 border-rose-200", text: "text-rose-700", label: "Member Removed" },
  "api_key.create": { bg: "bg-amber-50 border-amber-200", text: "text-amber-700", label: "API Key Created" },
  "api_key.revoke": { bg: "bg-orange-50 border-orange-200", text: "text-orange-700", label: "API Key Revoked" },
  "chat.query": { bg: "bg-indigo-50 border-indigo-200", text: "text-indigo-700", label: "Chat Query" },
  "organization.create": { bg: "bg-emerald-50 border-emerald-200", text: "text-emerald-700", label: "Org Created" },
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
          <h2 className="text-lg font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <span>📜</span> Security &amp; Audit Trail
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Immutable audit trail of administrative events, access changes, document mutations, and LLM queries.
          </p>
        </div>

        {/* Filter */}
        <div className="flex items-center gap-2.5">
          <label className="text-xs font-semibold text-slate-600">Filter Action:</label>
          <div className="relative inline-block">
            <select
              value={actionFilter}
              onChange={(e) => {
                setActionFilter(e.target.value);
                setPage(1);
              }}
              className="appearance-none bg-slate-50 hover:bg-slate-100 border border-slate-200 text-slate-800 text-xs font-semibold rounded-xl pl-3 pr-8 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500/10 focus:border-indigo-500 transition-all cursor-pointer shadow-2xs"
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
        <div className="p-3 bg-rose-50 border border-rose-200 text-rose-800 rounded-xl text-xs font-semibold">
          ⚠ {error}
        </div>
      )}

      {/* Audit Log Table */}
      <div className="border border-slate-200/80 rounded-2xl overflow-hidden bg-white shadow-xs">
        {loading ? (
          <div className="p-12 text-center text-xs text-slate-400">Loading audit trail...</div>
        ) : logs.length === 0 ? (
          <div className="p-12 text-center text-xs text-slate-400">No audit events recorded yet.</div>
        ) : (
          <table className="w-full text-left text-sm text-slate-700">
            <thead className="bg-slate-50/80 text-[11px] uppercase font-bold tracking-wider text-slate-500 border-b border-slate-100">
              <tr>
                <th className="px-6 py-3.5">Action</th>
                <th className="px-6 py-3.5">Resource</th>
                <th className="px-6 py-3.5">Timestamp</th>
                <th className="px-6 py-3.5 text-right">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-mono text-xs">
              {logs.map((log) => {
                const conf = actionColors[log.action] || {
                  bg: "bg-slate-100 border-slate-200",
                  text: "text-slate-700",
                  label: log.action,
                };
                return (
                  <tr key={log.id} className="hover:bg-slate-50/70 transition-colors">
                    <td className="px-6 py-3.5 font-sans">
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider border ${conf.bg} ${conf.text}`}
                      >
                        {conf.label}
                      </span>
                    </td>
                    <td className="px-6 py-3.5">
                      <div className="text-slate-900 font-semibold">{log.resource_type}</div>
                      {log.resource_id && (
                        <div className="text-[11px] text-slate-400 truncate max-w-[200px]">
                          {log.resource_id}
                        </div>
                      )}
                    </td>
                    <td className="px-6 py-3.5 text-slate-500 font-sans text-xs">
                      {new Date(log.created_at).toLocaleString()}
                    </td>
                    <td className="px-6 py-3.5 text-right font-sans">
                      <button
                        onClick={() => setSelectedLog(log)}
                        className="px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold transition-colors shadow-2xs"
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
        <div className="flex items-center justify-between px-6 py-3 bg-slate-50/80 border-t border-slate-100 text-xs text-slate-500 font-sans">
          <div>
            Showing <span className="font-semibold text-slate-700">{logs.length}</span> of{" "}
            <span className="font-semibold text-slate-700">{total}</span> events
          </div>
          <div className="flex items-center gap-2">
            <button
              disabled={page <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              className="px-3 py-1.5 rounded-lg bg-white border border-slate-200 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed text-slate-700 text-xs font-semibold shadow-2xs transition-colors"
            >
              Previous
            </button>
            <span className="px-2 font-semibold text-slate-800">Page {page}</span>
            <button
              disabled={page * 25 >= total}
              onClick={() => setPage((p) => p + 1)}
              className="px-3 py-1.5 rounded-lg bg-white border border-slate-200 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed text-slate-700 text-xs font-semibold shadow-2xs transition-colors"
            >
              Next
            </button>
          </div>
        </div>
      </div>

      {/* JSON Inspector Modal */}
      {selectedLog && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 animate-in fade-in duration-200">
          <div className="bg-white border border-slate-200 rounded-2xl p-6 max-w-lg w-full shadow-xl space-y-4 font-sans">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2 font-mono">
                <span>🔍</span> Audit Event Inspector
              </h3>
              <button
                onClick={() => setSelectedLog(null)}
                className="text-slate-400 hover:text-slate-700 text-sm font-semibold p-1 rounded-lg hover:bg-slate-100 transition-colors"
              >
                ✕
              </button>
            </div>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between border-b border-slate-100 py-1.5">
                <span className="text-slate-500">Event ID:</span>
                <span className="font-mono text-slate-800 font-medium">{selectedLog.id}</span>
              </div>
              <div className="flex justify-between border-b border-slate-100 py-1.5">
                <span className="text-slate-500">Action:</span>
                <span className="font-mono font-semibold text-indigo-600">{selectedLog.action}</span>
              </div>
              <div className="flex justify-between border-b border-slate-100 py-1.5">
                <span className="text-slate-500">Resource:</span>
                <span className="text-slate-800 font-medium">
                  {selectedLog.resource_type} ({selectedLog.resource_id || "N/A"})
                </span>
              </div>
              <div className="flex justify-between border-b border-slate-100 py-1.5">
                <span className="text-slate-500">Actor User ID:</span>
                <span className="font-mono text-slate-700">{selectedLog.actor_user_id || "System"}</span>
              </div>
              <div className="flex justify-between border-b border-slate-100 py-1.5">
                <span className="text-slate-500">Timestamp:</span>
                <span className="text-slate-700">{new Date(selectedLog.created_at).toISOString()}</span>
              </div>
            </div>

            <div>
              <div className="text-[11px] font-bold text-slate-700 uppercase tracking-wider mb-2">
                Event Metadata Payload
              </div>
              <pre className="p-3.5 bg-slate-900 border border-slate-800 rounded-xl text-[11px] font-mono text-emerald-400 overflow-x-auto max-h-48">
                {JSON.stringify(selectedLog.metadata_, null, 2)}
              </pre>
            </div>

            <div className="flex justify-end pt-2">
              <button
                onClick={() => setSelectedLog(null)}
                className="px-4 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs font-semibold transition-colors"
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
