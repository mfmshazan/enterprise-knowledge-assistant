"use client";

import { useRef, useState } from "react";

import type { ApiError } from "@/lib/api";
import { useIngestUrl, useUploadDocument } from "@/lib/documents";

export function UploadPanel({ orgId }: { orgId: string }) {
  const upload = useUploadDocument(orgId);
  const ingest = useIngestUrl(orgId);
  const fileInput = useRef<HTMLInputElement>(null);
  const [url, setUrl] = useState("");

  const onFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) upload.mutate(file, { onSettled: () => fileInput.current?.form?.reset() });
  };

  const onUrl = (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;
    ingest.mutate({ url: url.trim() }, { onSuccess: () => setUrl("") });
  };

  return (
    <div className="space-y-4">
      <form>
        <label className="flex cursor-pointer flex-col gap-2">
          <span className="text-sm font-medium">Upload a file</span>
          <input
            ref={fileInput}
            type="file"
            accept=".pdf,.docx,.md,.markdown,.txt"
            onChange={onFile}
            disabled={upload.isPending}
            className="block w-full text-sm text-[color:var(--color-muted)] file:mr-3 file:rounded-md file:border-0 file:bg-[color:var(--color-accent)] file:px-3 file:py-1.5 file:text-sm file:font-medium file:text-white hover:file:opacity-90"
          />
        </label>
        {upload.isPending && (
          <p className="mt-1 text-xs text-[color:var(--color-muted)]">Uploading…</p>
        )}
        {upload.error && (
          <p className="mt-1 text-xs text-red-400">{(upload.error as ApiError).message}</p>
        )}
      </form>

      <form onSubmit={onUrl} className="flex flex-col gap-2 sm:flex-row">
        <input
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://example.com/page to ingest"
          className="flex-1 rounded-md border border-white/10 bg-black/30 px-3 py-2 text-sm"
        />
        <button
          type="submit"
          disabled={ingest.isPending}
          className="rounded-md border border-white/10 px-4 py-2 text-sm hover:bg-white/5 disabled:opacity-50"
        >
          {ingest.isPending ? "Adding…" : "Add URL"}
        </button>
      </form>
      {ingest.error && (
        <p className="text-xs text-red-400">{(ingest.error as ApiError).message}</p>
      )}
    </div>
  );
}
