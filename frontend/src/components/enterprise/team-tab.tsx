"use client";

import { useCallback, useEffect, useState } from "react";
import { Users, UserPlus, Mail } from "lucide-react";

import { useAuth } from "@/lib/auth/context";
import {
  OrgMember,
  Role,
  inviteOrgMember,
  listOrgMembers,
  removeOrgMember,
  updateOrgMemberRole,
} from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Badge, type BadgeTone } from "@/components/ui/badge";
import { Modal } from "@/components/ui/modal";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/toast";

interface TeamTabProps {
  orgId: string;
}

const roleTones: Record<Role, BadgeTone> = {
  owner: "amber",
  admin: "violet",
  member: "blue",
};

export function TeamTab({ orgId }: TeamTabProps) {
  const { getToken } = useAuth();
  const { toast } = useToast();
  const [members, setMembers] = useState<OrgMember[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Invite modal state
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState<Role>("member");
  const [inviting, setInviting] = useState(false);

  // Remove confirmation state
  const [removeTarget, setRemoveTarget] = useState<{ id: string; name: string } | null>(null);
  const [removing, setRemoving] = useState(false);

  const fetchMembers = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const token = await getToken();
      const res = await listOrgMembers(token, orgId);
      setMembers(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load team members");
    } finally {
      setLoading(false);
    }
  }, [getToken, orgId]);

  useEffect(() => {
    fetchMembers();
  }, [fetchMembers]);

  const handleRoleChange = async (userId: string, newRole: Role) => {
    try {
      const token = await getToken();
      await updateOrgMemberRole(token, orgId, userId, { role: newRole });
      toast("Member role updated.", "success");
      fetchMembers();
    } catch (err: unknown) {
      toast(err instanceof Error ? err.message : "Failed to update role", "error");
    }
  };

  const confirmRemove = async () => {
    if (!removeTarget) return;
    try {
      setRemoving(true);
      const token = await getToken();
      await removeOrgMember(token, orgId, removeTarget.id);
      toast(`Removed ${removeTarget.name}.`, "success");
      setRemoveTarget(null);
      fetchMembers();
    } catch (err: unknown) {
      toast(err instanceof Error ? err.message : "Failed to remove member", "error");
    } finally {
      setRemoving(false);
    }
  };

  const handleInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inviteEmail.trim()) return;
    try {
      setInviting(true);
      const token = await getToken();
      await inviteOrgMember(token, orgId, { email: inviteEmail.trim(), role: inviteRole });
      setShowInviteModal(false);
      toast(`Invited ${inviteEmail} as ${inviteRole}.`, "success");
      setInviteEmail("");
      fetchMembers();
    } catch (err: unknown) {
      toast(err instanceof Error ? err.message : "Failed to invite member", "error");
    } finally {
      setInviting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header bar */}
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <h2 className="flex items-center gap-2 text-lg font-bold tracking-tight text-slate-900">
            <Users className="h-5 w-5 text-indigo-500" aria-hidden /> Team &amp; Access Control
          </h2>
          <p className="mt-0.5 text-xs text-slate-500">
            Manage organization members, invite teammates, and assign role-based access permissions.
          </p>
        </div>
        <Button size="sm" onClick={() => setShowInviteModal(true)}>
          <UserPlus className="h-4 w-4" aria-hidden /> Invite Member
        </Button>
      </div>

      {error && (
        <div className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs font-semibold text-rose-800">
          {error}
        </div>
      )}

      {/* Members table */}
      <div className="overflow-hidden rounded-2xl border border-slate-200/80 bg-white shadow-xs">
        {loading ? (
          <div className="space-y-3 p-6">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="flex items-center gap-3">
                <Skeleton className="h-9 w-9 rounded-xl" />
                <div className="flex-1 space-y-1.5">
                  <Skeleton className="h-3 w-40" />
                  <Skeleton className="h-2.5 w-56" />
                </div>
              </div>
            ))}
          </div>
        ) : members.length === 0 ? (
          <div className="p-12 text-center text-xs text-slate-400">No members found.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[560px] text-left text-sm text-slate-700">
              <thead className="border-b border-slate-100 bg-slate-50/80 text-[11px] font-bold uppercase tracking-wider text-slate-500">
                <tr>
                  <th className="px-6 py-3.5">User</th>
                  <th className="px-6 py-3.5">Role</th>
                  <th className="px-6 py-3.5">Joined</th>
                  <th className="px-6 py-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-xs">
                {members.map((m) => {
                  const displayName = m.user.full_name || m.user.email.split("@")[0];
                  const initials = displayName.slice(0, 2).toUpperCase();
                  return (
                    <tr key={m.id} className="transition-colors hover:bg-slate-50/70">
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <div className="flex h-9 w-9 items-center justify-center rounded-xl border border-indigo-100 bg-indigo-50 text-xs font-bold text-indigo-700 shadow-2xs">
                            {initials}
                          </div>
                          <div>
                            <div className="font-semibold text-slate-900">{displayName}</div>
                            <div className="text-[11px] text-slate-400">{m.user.email}</div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <Badge tone={roleTones[m.role] ?? "blue"} uppercase>
                          {m.role}
                        </Badge>
                      </td>
                      <td className="px-6 py-4 text-xs text-slate-400">
                        {new Date(m.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <div className="relative inline-block">
                            <select
                              value={m.role}
                              onChange={(e) => handleRoleChange(m.user.id, e.target.value as Role)}
                              aria-label={`Change role for ${displayName}`}
                              className="cursor-pointer appearance-none rounded-lg border border-slate-200 bg-slate-50 py-1.5 pl-3 pr-7 text-xs font-semibold text-slate-700 transition-all hover:bg-slate-100 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/10"
                            >
                              <option value="owner">Owner</option>
                              <option value="admin">Admin</option>
                              <option value="member">Member</option>
                            </select>
                            <span className="pointer-events-none absolute right-2 top-1/2 -translate-y-1/2 text-[9px] text-slate-400">
                              ▼
                            </span>
                          </div>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setRemoveTarget({ id: m.user.id, name: displayName })}
                            className="text-slate-400 hover:bg-rose-50 hover:text-rose-600"
                          >
                            Remove
                          </Button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Invite Modal */}
      <Modal
        open={showInviteModal}
        onClose={() => setShowInviteModal(false)}
        title={
          <span className="flex items-center gap-2">
            <Mail className="h-4 w-4 text-indigo-500" aria-hidden /> Invite Teammate
          </span>
        }
      >
        <form onSubmit={handleInvite} className="space-y-4">
          <div>
            <label className="mb-1.5 block text-xs font-bold uppercase tracking-wider text-slate-700">
              Email Address
            </label>
            <input
              type="email"
              required
              value={inviteEmail}
              onChange={(e) => setInviteEmail(e.target.value)}
              placeholder="colleague@company.com"
              className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-xs text-slate-900 placeholder:text-slate-400 transition-all focus:border-indigo-500 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500/10 sm:text-sm"
            />
          </div>

          <div>
            <label className="mb-1.5 block text-xs font-bold uppercase tracking-wider text-slate-700">
              Initial Role
            </label>
            <div className="relative">
              <select
                value={inviteRole}
                onChange={(e) => setInviteRole(e.target.value as Role)}
                className="w-full cursor-pointer appearance-none rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 pr-9 text-xs font-medium text-slate-800 transition-all focus:border-indigo-500 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500/10 sm:text-sm"
              >
                <option value="member">Member (Can chat and view documents)</option>
                <option value="admin">Admin (Can manage docs, keys, and members)</option>
                <option value="owner">Owner (Full administrative ownership)</option>
              </select>
              <span className="pointer-events-none absolute right-3.5 top-1/2 -translate-y-1/2 text-xs text-slate-400">
                ▼
              </span>
            </div>
          </div>

          <div className="flex items-center justify-end gap-3 pt-2">
            <Button variant="ghost" size="sm" onClick={() => setShowInviteModal(false)}>
              Cancel
            </Button>
            <Button type="submit" size="sm" disabled={inviting}>
              {inviting ? "Inviting…" : "Send Invite"}
            </Button>
          </div>
        </form>
      </Modal>

      <ConfirmDialog
        open={removeTarget !== null}
        title="Remove member"
        description={`Are you sure you want to remove ${removeTarget?.name} from this organization? They will lose all access.`}
        confirmLabel="Remove"
        danger
        loading={removing}
        onConfirm={confirmRemove}
        onCancel={() => setRemoveTarget(null)}
      />
    </div>
  );
}
