"use client";

/**
 * Organization workspace: manage the documents that power this org's knowledge
 * base. Upload files or add URLs, then watch each document's status move from
 * pending → processing → indexed (the list live-polls while work is in flight).
 */

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect } from "react";

import { DocumentList } from "@/components/documents/document-list";
import { UploadPanel } from "@/components/documents/upload-panel";
import { useAuth } from "@/lib/auth/context";

export default function OrgWorkspacePage() {
  const { isLoaded, isSignedIn } = useAuth();
  const router = useRouter();
  const params = useParams<{ orgId: string }>();
  const orgId = params.orgId;

  useEffect(() => {
    if (isLoaded && !isSignedIn) router.replace("/sign-in");
  }, [isLoaded, isSignedIn, router]);

  if (!isLoaded || !isSignedIn) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <p className="text-[color:var(--color-muted)]">Loading…</p>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-2xl space-y-8 px-6 py-12">
      <header className="space-y-1">
        <Link href="/dashboard" className="text-sm text-[color:var(--color-muted)] hover:underline">
          ← Back to dashboard
        </Link>
        <h1 className="text-2xl font-semibold">Knowledge base</h1>
        <p className="text-sm text-[color:var(--color-muted)]">
          Documents uploaded here are chunked and embedded so they can be searched
          and (soon) answered over.
        </p>
      </header>

      <section className="space-y-3 rounded-xl border border-white/10 bg-white/5 p-5">
        <h2 className="font-medium">Add documents</h2>
        <UploadPanel orgId={orgId} />
      </section>

      <section className="space-y-3 rounded-xl border border-white/10 bg-white/5 p-5">
        <h2 className="font-medium">Documents</h2>
        <DocumentList orgId={orgId} />
      </section>
    </main>
  );
}
