"use client";

import { useCallback, useEffect, useState } from "react";
import { KeyRound, Plus, AlertTriangle } from "lucide-react";

import { useAuth } from "@/lib/auth/context";
import {
  ApiKeyItem,
  ApiKeyCreatedResponse,
  createApiKey,
  listApiKeys,
  revokeApiKey,
} from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Modal } from "@/components/ui/modal";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/toast";

interface ApiKeysTabProps {
  orgId: string;
}

export function ApiKeysTab({ orgId }: ApiKeysTabProps) {
  const { getToken } = useAuth();
  const { toast } = useToast();
  const [keys, setKeys] = useState<ApiKeyItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Creation modal state
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [keyName, setKeyName] = useState("");
  const [expiresInDays, setExpiresInDays] = useState<number | undefined>(undefined);
  const [creating, setCreating] = useState(false);

  // Key revelation modal
  const [newKeyData, setNewKeyData] = useState<ApiKeyCreatedResponse | null>(null);
  const [copied, setCopied] = useState(false);

  // Revoke confirmation
  const [revokeTarget, setRevokeTarget] = useState<{ id: string; name: string } | null>(null);
  const [revoking, setRevoking] = useState(false);

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
      setExpiresInDays(undefined);
      setNewKeyData(res);
      fetchKeys();
    } catch (err: unknown) {
      toast(err instanceof Error ? err.message : "Failed to create API key", "error");
    } finally {
      setCreating(false);
    }
  };

  const confirmRevoke = async () => {
    if (!revokeTarget) return;
    try {
      setRevoking(true);
      const token = await getToken();
      await revokeApiKey(token, orgId, revokeTarget.id);
      toast(`Revoked "${revokeTarget.name}".`, "success");
      setRevokeTarget(null);
      fetchKeys();
    } catch (err: unknown) {
      toast(err instanceof Error ? err.message : "Failed to revoke API key", "error");
    } finally {
      setRevoking(false);
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
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <h2 className="flex items-center gap-2 text-lg font-bold tracking-tight text-slate-900">
            <KeyRound className="h-5 w-5 text-indigo-500" aria-hidden /> Developer API Keys
          </h2>
          <p className="mt-0.5 text-xs text-slate-500">
            Machine-to-machine authentication keys for integrating external pipelines, CLI tools,
            and automation bots.
          </p>
        </div>
        <Button size="sm" onClick={() => setShowCreateModal(true)}>
          <Plus className="h-4 w-4" aria-hidden /> Generate New API Key
        </Button>
      </div>

      {error && (
        <div className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs font-semibold text-rose-800">
          {error}
        </div>
      )}

      {/* Keys Table */}
      <div className="overflow-hidden rounded-2xl border border-slate-200/80 bg-white shadow-xs">
        {loading ? (
          <div className="space-y-3 p-6">
            {Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-10 w-full" />
            ))}
          </div>
        ) : keys.length === 0 ? (
          <div className="p-12 text-center text-xs text-slate-400">
            No API keys created yet. Click Generate New API Key to create your first machine key.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[640px] text-left text-sm text-slate-700">
              <thead className="border-b border-slate-100 bg-slate-50/80 text-[11px] font-bold uppercase tracking-wider text-slate-500">
                <tr>
                  <th className="px-6 py-3.5">Key Name</th>
                  <th className="px-6 py-3.5">Key Prefix</th>
                  <th className="px-6 py-3.5">Created</th>
                  <th className="px-6 py-3.5">Status</th>
                  <th className="px-6 py-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-xs">
                {keys.map((k) => (
                  <tr key={k.id} className="transition-colors hover:bg-slate-50/70">
                    <td className="px-6 py-4">
                      <div className="font-semibold text-slate-900">{k.name}</div>
                      {k.expires_at && (
                        <div className="mt-0.5 text-[11px] text-slate-400">
                          Expires: {new Date(k.expires_at).toLocaleDateString()}
                        </div>
                      )}
                    </td>
                    <td className="px-6 py-4 font-mono text-xs">
                      <span className="rounded-md border border-slate-200 bg-slate-100 px-2 py-0.5 font-semibold text-slate-700">
                        {k.key_prefix}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-slate-500">
                      {new Date(k.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4">
                      {k.is_active ? (
                        <Badge tone="emerald" dot uppercase>
                          Active
                        </Badge>
                      ) : (
                        <Badge tone="rose" dot uppercase>
                          Revoked
                        </Badge>
                      )}
                    </td>
                    <td className="px-6 py-4 text-right">
                      {k.is_active && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setRevokeTarget({ id: k.id, name: k.name })}
                          className="text-slate-400 hover:bg-rose-50 hover:text-rose-600"
                        >
                          Revoke
                        </Button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Generate API Key Modal */}
      <Modal
        open={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title={
          <span className="flex items-center gap-2">
            <KeyRound className="h-4 w-4 text-indigo-500" aria-hidden /> Generate API Key
          </span>
        }
      >
        <form onSubmit={handleCreate} className="space-y-4">
          <div>
            <label className="mb-1.5 block text-xs font-bold uppercase tracking-wider text-slate-700">
              Key Name
            </label>
            <input
              type="text"
              required
              value={keyName}
              onChange={(e) => setKeyName(e.target.value)}
              placeholder="e.g. CI/CD Ingestion Worker"
              className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-xs text-slate-900 placeholder:text-slate-400 transition-all focus:border-indigo-500 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500/10 sm:text-sm"
            />
          </div>

          <div>
            <label className="mb-1.5 block text-xs font-bold uppercase tracking-wider text-slate-700">
              Expiration
            </label>
            <div className="relative">
              <select
                value={expiresInDays ?? 0}
                onChange={(e) => {
                  const val = Number(e.target.value);
                  setExpiresInDays(val === 0 ? undefined : val);
                }}
                className="w-full cursor-pointer appearance-none rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 pr-9 text-xs font-medium text-slate-800 transition-all focus:border-indigo-500 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500/10 sm:text-sm"
              >
                <option value={30}>30 days</option>
                <option value={90}>90 days</option>
                <option value={365}>1 year</option>
                <option value={0}>Never expires</option>
              </select>
              <span className="pointer-events-none absolute right-3.5 top-1/2 -translate-y-1/2 text-xs text-slate-400">
                ▼
              </span>
            </div>
          </div>

          <div className="flex items-center justify-end gap-3 pt-2">
            <Button variant="ghost" size="sm" onClick={() => setShowCreateModal(false)}>
              Cancel
            </Button>
            <Button type="submit" size="sm" disabled={creating}>
              {creating ? "Generating…" : "Generate Key"}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Secret Key Revealed Modal */}
      <Modal
        open={newKeyData !== null}
        onClose={() => setNewKeyData(null)}
        size="max-w-lg"
        title={
          <span className="flex items-center gap-2 text-amber-700">
            <AlertTriangle className="h-4 w-4" aria-hidden /> Save Your API Secret Key
          </span>
        }
      >
        {newKeyData && (
          <div className="space-y-4">
            <p className="text-xs font-medium text-amber-700">
              Copy this key now. You will never be able to view it again.
            </p>

            <div className="relative">
              <input
                type="text"
                readOnly
                value={newKeyData.secret_key}
                className="w-full select-all rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 pr-24 font-mono text-xs font-bold text-slate-900 focus:outline-none"
              />
              <Button
                size="sm"
                onClick={() => copyToClipboard(newKeyData.secret_key)}
                className="absolute right-2 top-1/2 -translate-y-1/2"
              >
                {copied ? "Copied!" : "Copy"}
              </Button>
            </div>

            <div className="space-y-1 rounded-xl border border-slate-200 bg-slate-50 p-3 text-[11px] text-slate-600">
              <div>
                <strong className="text-slate-800">Key Name:</strong> {newKeyData.name}
              </div>
              <div>
                <strong className="text-slate-800">Prefix:</strong>{" "}
                <span className="font-mono">{newKeyData.key_prefix}</span>
              </div>
            </div>

            <div className="flex justify-end pt-1">
              <Button size="sm" onClick={() => setNewKeyData(null)}>
                Done
              </Button>
            </div>
          </div>
        )}
      </Modal>

      <ConfirmDialog
        open={revokeTarget !== null}
        title="Revoke API key"
        description={`Revoke "${revokeTarget?.name}"? Any integration using this key will immediately stop working. This cannot be undone.`}
        confirmLabel="Revoke"
        danger
        loading={revoking}
        onConfirm={confirmRevoke}
        onCancel={() => setRevokeTarget(null)}
      />
    </div>
  );
}
