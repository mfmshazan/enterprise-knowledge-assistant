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
    <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm space-y-5">
      <div>
        <h3 className="text-sm font-bold text-slate-900 tracking-tight">Add Knowledge</h3>
        <p className="text-xs text-slate-500 mt-0.5">
          Upload document files or link web articles to index into your vector database.
        </p>
      </div>

      {/* File Upload Zone */}
      <form>
        <label className="flex flex-col items-center justify-center rounded-xl border-2 border-dashed border-slate-200 bg-slate-50/70 p-6 text-center cursor-pointer transition-colors hover:border-indigo-400 hover:bg-indigo-50/30">
          <span className="text-2xl mb-1">📤</span>
          <span className="text-xs font-semibold text-slate-800">
            Click to upload document or drag and drop
          </span>
          <span className="mt-1 text-[11px] text-slate-400">
            Supported formats: PDF, DOCX, Markdown, Plain Text (max 25MB)
          </span>
          <input
            ref={fileInput}
            type="file"
            accept=".pdf,.docx,.md,.markdown,.txt"
            onChange={onFile}
            disabled={upload.isPending}
            className="hidden"
          />
        </label>
        {upload.isPending && (
          <p className="mt-2 text-xs text-indigo-600 font-medium animate-pulse">
            ⏳ Processing and indexing chunks into Qdrant…
          </p>
        )}
        {upload.error && (
          <p className="mt-2 text-xs text-rose-500 font-medium">
            {(upload.error as ApiError).message}
          </p>
        )}
      </form>

      {/* URL Ingestion */}
      <form onSubmit={onUrl} className="flex flex-col gap-2 sm:flex-row">
        <div className="relative flex-1">
          <span className="absolute inset-y-0 left-3 flex items-center text-xs text-slate-400">
            🔗
          </span>
          <input
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://docs.example.com/guide to scrape"
            className="w-full rounded-xl border border-slate-200 bg-slate-50 pl-8 pr-3 py-2 text-xs text-slate-800 placeholder:text-slate-400 focus:border-indigo-500 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500/10"
          />
        </div>
        <button
          type="submit"
          disabled={ingest.isPending || !url.trim()}
          className="rounded-xl bg-slate-900 px-4 py-2 text-xs font-semibold text-white shadow-sm hover:bg-slate-800 disabled:opacity-50 transition-colors"
        >
          {ingest.isPending ? "Ingesting…" : "Index URL"}
        </button>
      </form>
      {ingest.error && (
        <p className="text-xs text-rose-500 font-medium">
          {(ingest.error as ApiError).message}
        </p>
      )}
    </div>
  );
}
