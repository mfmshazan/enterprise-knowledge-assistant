"use client";

import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@/lib/auth/context";
import {
  ApiKeyCreatedResponse,
  ApiKeyItem,
  createApiKey,
  listApiKeys,
  revokeApiKey,
} from "@/lib/api";

interface ApiKeysTabProps {
  orgId: string;
}

export function ApiKeysTab({ orgId }: ApiKeysTabProps) {
  const { getToken } = useAuth();
  const [keys, setKeys] = useState<ApiKeyItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Create Key Modal
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [keyName, setKeyName] = useState("");
  const [expiresInDays, setExpiresInDays] = useState<number | undefined>(30);
  const [creating, setCreating] = useState(false);

  // One-time Secret Key Revealed Modal
  const [newKeyData, setNewKeyData] = useState<ApiKeyCreatedResponse | null>(null);
  const [copied, setCopied] = useState(false);

  const fetchKeys = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const token = await getToken();
      const res = await listApiKeys(token, orgId);
      setKeys(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load API keys");
    } finally {
      setLoading(false);
    }
  }, [getToken, orgId]);

  useEffect(() => {
    fetchKeys();
  }, [fetchKeys]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!keyName.trim()) return;
    try {
      setCreating(true);
      const token = await getToken();
      const res = await createApiKey(token, orgId, {
        name: keyName.trim(),
        expires_in_days: expiresInDays,
      });
      setShowCreateModal(false);
      setKeyName("");
      setNewKeyData(res);
      fetchKeys();
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to create API key");
    } finally {
      setCreating(false);
    }
  };

  const handleRevoke = async (keyId: string, name: string) => {
    if (!confirm(`Are you sure you want to revoke the API key "${name}"? Any applications using this key will immediately lose access.`)) {
      return;
    }
    try {
      const token = await getToken();
      await revokeApiKey(token, orgId, keyId);
      fetchKeys();
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to revoke API key");
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 3000);
  };

  return (
    <div className="space-y-6">
      {/* Header bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <span>🔑</span> Developer API Keys
          </h2>
          <p className="text-sm text-zinc-400 mt-1">
            Machine-to-machine authentication keys for integrating external pipelines, CLI tools, and automation bots.
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium text-sm transition-colors shadow-sm"
        >
          <span>➕</span> Generate New API Key
        </button>
      </div>

      {error && (
        <div className="p-3 bg-rose-500/10 border border-rose-500/30 text-rose-300 rounded-lg text-sm">
          ⚠ {error}
        </div>
      )}

      {/* Keys Table */}
      <div className="border border-zinc-800 rounded-xl overflow-hidden bg-zinc-900/60 shadow-lg backdrop-blur-sm">
        {loading ? (
          <div className="p-12 text-center text-zinc-400">Loading API keys...</div>
        ) : keys.length === 0 ? (
          <div className="p-12 text-center text-zinc-400">
            No API keys created yet. Click Generate New API Key to create your first machine key.
          </div>
        ) : (
          <table className="w-full text-left text-sm text-zinc-300">
            <thead className="bg-zinc-950/80 text-xs uppercase font-semibold text-zinc-400 border-b border-zinc-800">
              <tr>
                <th className="px-6 py-4">Key Name</th>
                <th className="px-6 py-4">Key Prefix</th>
                <th className="px-6 py-4">Created</th>
                <th className="px-6 py-4">Status</th>
                <th className="px-6 py-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/60">
              {keys.map((k) => (
                <tr key={k.id} className="hover:bg-zinc-800/40 transition-colors">
                  <td className="px-6 py-4">
                    <div className="font-medium text-white">{k.name}</div>
                    {k.expires_at && (
                      <div className="text-xs text-zinc-400">
                        Expires: {new Date(k.expires_at).toLocaleDateString()}
                      </div>
                    )}
                  </td>
                  <td className="px-6 py-4 font-mono text-xs text-zinc-300">
                    <span className="px-2 py-1 bg-zinc-950 rounded border border-zinc-800">
                      {k.key_prefix}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-xs text-zinc-400">
                    {new Date(k.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4">
                    {k.is_active ? (
                      <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        ● Active
                      </span>
                    ) : (
                      <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-rose-500/10 text-rose-400 border border-rose-500/20">
                        Revoked
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4 text-right">
                    {k.is_active && (
                      <button
                        onClick={() => handleRevoke(k.id, k.name)}
                        className="px-2.5 py-1.5 text-xs text-rose-400 hover:text-rose-300 hover:bg-rose-500/10 rounded-lg transition-colors font-medium"
                      >
                        Revoke
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Generate API Key Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-zinc-900 border border-zinc-700 rounded-2xl p-6 max-w-md w-full shadow-2xl space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <span>🔑</span> Generate API Key
              </h3>
              <button
                onClick={() => setShowCreateModal(false)}
                className="text-zinc-400 hover:text-zinc-200 text-sm"
              >
                ✕
              </button>
            </div>
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-zinc-300 uppercase tracking-wider mb-1.5">
                  Key Name
                </label>
                <input
                  type="text"
                  required
                  value={keyName}
                  onChange={(e) => setKeyName(e.target.value)}
                  placeholder="e.g. CI/CD Ingestion Worker"
                  className="w-full px-3.5 py-2.5 bg-zinc-950 border border-zinc-700 rounded-xl text-white placeholder-zinc-500 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-zinc-300 uppercase tracking-wider mb-1.5">
                  Expiration
                </label>
                <select
                  value={expiresInDays ?? 0}
                  onChange={(e) => {
                    const val = Number(e.target.value);
                    setExpiresInDays(val === 0 ? undefined : val);
                  }}
                  className="w-full px-3.5 py-2.5 bg-zinc-950 border border-zinc-700 rounded-xl text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value={30}>30 days</option>
                  <option value={90}>90 days</option>
                  <option value={365}>1 year</option>
                  <option value={0}>Never expires</option>
                </select>
              </div>

              <div className="flex items-center justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 rounded-xl text-zinc-400 hover:text-zinc-200 text-sm"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creating}
                  className="px-5 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-medium text-sm transition-colors disabled:opacity-50"
                >
                  {creating ? "Generating..." : "Generate Key"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Secret Key Revealed Modal */}
      {newKeyData && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-zinc-900 border border-amber-500/40 rounded-2xl p-6 max-w-lg w-full shadow-2xl space-y-4">
            <div className="flex items-center gap-3 text-amber-400">
              <span className="text-2xl">⚠️</span>
              <h3 className="text-lg font-bold text-white">Save Your API Secret Key</h3>
            </div>

            <p className="text-xs text-zinc-300 leading-relaxed">
              Please copy your API key now. <strong className="text-amber-300">For security reasons, you will never be able to view this key again.</strong>
            </p>

            <div className="relative">
              <input
                type="text"
                readOnly
                value={newKeyData.secret_key}
                className="w-full px-4 py-3 bg-zinc-950 border border-zinc-700 rounded-xl font-mono text-sm text-emerald-400 focus:outline-none pr-24"
              />
              <button
                onClick={() => copyToClipboard(newKeyData.secret_key)}
                className="absolute right-2 top-2 px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold rounded-lg transition-colors"
              >
                {copied ? "Copied! ✓" : "Copy"}
              </button>
            </div>

            <div className="p-3 bg-zinc-950/60 rounded-xl border border-zinc-800 text-[11px] text-zinc-400 space-y-1">
              <div><strong>Key Name:</strong> {newKeyData.name}</div>
              <div><strong>Prefix:</strong> {newKeyData.key_prefix}</div>
            </div>

            <div className="flex justify-end pt-2">
              <button
                onClick={() => setNewKeyData(null)}
                className="px-5 py-2 bg-zinc-800 hover:bg-zinc-700 text-white rounded-xl text-sm font-medium"
              >
                Done
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
