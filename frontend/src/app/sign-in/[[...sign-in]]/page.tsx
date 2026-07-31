"use client";

/**
 * Sign-in route (catch-all so it works for both the dev form and Clerk's flow).
 *
 * - dev mode:   a small form that mints a `dev:` token and redirects to /dashboard.
 * - clerk mode: Clerk's hosted <SignIn /> widget.
 */

import { SignIn } from "@clerk/nextjs";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { useDevSignIn } from "@/lib/auth/dev-auth";
import { AUTH_MODE } from "@/lib/config";

function DevSignInForm() {
  const { signIn } = useDevSignIn();
  const router = useRouter();
  const [email, setEmail] = useState("alice@acme.com");
  const [orgSlug, setOrgSlug] = useState("acme");
  const [role, setRole] = useState<"owner" | "admin" | "member">("owner");

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.includes("@")) return;
    signIn({ email, orgSlug: orgSlug || undefined, role });
    router.push("/dashboard");
  };

  return (
    <form
      onSubmit={onSubmit}
      className="w-full max-w-sm space-y-4 rounded-xl border border-white/10 bg-white/5 p-6"
    >
      <div className="space-y-1">
        <h1 className="text-xl font-semibold">Dev sign-in</h1>
        <p className="text-sm text-[color:var(--color-muted)]">
          No account needed — this mints a <code>dev:</code> token for the local backend.
        </p>
      </div>

      <label className="block space-y-1">
        <span className="text-sm">Email</span>
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full rounded-md border border-white/10 bg-black/30 px-3 py-2 text-sm"
          required
        />
      </label>

      <label className="block space-y-1">
        <span className="text-sm">Organization slug (optional)</span>
        <input
          type="text"
          value={orgSlug}
          onChange={(e) => setOrgSlug(e.target.value)}
          placeholder="acme"
          className="w-full rounded-md border border-white/10 bg-black/30 px-3 py-2 text-sm"
        />
      </label>

      <label className="block space-y-1">
        <span className="text-sm">Role in org</span>
        <select
          value={role}
          onChange={(e) => setRole(e.target.value as "owner" | "admin" | "member")}
          className="w-full rounded-md border border-white/10 bg-black/30 px-3 py-2 text-sm"
        >
          <option value="owner">owner</option>
          <option value="admin">admin</option>
          <option value="member">member</option>
        </select>
      </label>

      <button
        type="submit"
        className="w-full rounded-md bg-[color:var(--color-accent)] px-3 py-2 text-sm font-medium text-white hover:opacity-90"
      >
        Continue
      </button>
    </form>
  );
}

export default function SignInPage() {
  return (
    <main className="flex min-h-screen items-center justify-center px-6 py-16">
      {AUTH_MODE === "clerk" ? <SignIn /> : <DevSignInForm />}
    </main>
  );
}
