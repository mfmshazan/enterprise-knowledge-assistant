"use client";

import type { DocumentItem } from "@/lib/api";

interface AnalyticsWidgetProps {
  documents: DocumentItem[];
}

export function AnalyticsWidget({ documents }: AnalyticsWidgetProps) {
  const totalDocs = documents.length;
  const indexedCount = documents.filter((d) => d.status === "indexed").length;
  const pendingCount = documents.filter(
    (d) => d.status === "pending" || d.status === "processing"
  ).length;
  const failedCount = documents.filter((d) => d.status === "failed").length;

  const totalChunks = documents.reduce((sum, d) => sum + (d.chunk_count || 0), 0);

  const indexedPercent = totalDocs > 0 ? (indexedCount / totalDocs) * 100 : 0;
  const pendingPercent = totalDocs > 0 ? (pendingCount / totalDocs) * 100 : 0;

  return (
    <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-slate-400 select-none text-base">⠿</span>
          <h2 className="text-sm font-bold text-slate-800 tracking-tight">Analytics</h2>
        </div>
        <span className="text-xs font-semibold text-indigo-600 hover:text-indigo-700 cursor-pointer">
          View all
        </span>
      </div>

      {/* Filter Dropdown */}
      <div className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-slate-50 px-2.5 py-1 text-xs font-medium text-slate-700 shadow-2xs">
        <span>Last 30 days</span>
        <span className="text-[10px] text-slate-400">▼</span>
      </div>

      {/* Counter */}
      <div className="pt-1">
        <div className="flex items-baseline justify-between">
          <span className="text-xs font-medium text-slate-500">Total documents</span>
          <span className="text-xl font-bold text-slate-900">{totalDocs}</span>
        </div>

        {/* Multi-segment Progress Bar */}
        <div className="mt-2.5 h-2 w-full overflow-hidden rounded-full bg-slate-100 flex">
          <div
            style={{ width: `${indexedPercent}%` }}
            className="h-full bg-emerald-500 transition-all duration-500"
            title={`Indexed: ${indexedCount}`}
          />
          <div
            style={{ width: `${pendingPercent}%` }}
            className="h-full bg-amber-400 transition-all duration-500"
            title={`Processing: ${pendingCount}`}
          />
          {failedCount > 0 && (
            <div
              style={{ width: `${(failedCount / totalDocs) * 100}%` }}
              className="h-full bg-rose-400 transition-all duration-500"
              title={`Failed: ${failedCount}`}
            />
          )}
        </div>

        {/* Status Legend */}
        <div className="mt-3 flex items-center justify-between text-[11px] font-medium text-slate-600">
          <div className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-emerald-500" />
            <span>Indexed ({indexedCount})</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-amber-400" />
            <span>Processing ({pendingCount})</span>
          </div>
          {failedCount > 0 && (
            <div className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-rose-400" />
              <span>Failed ({failedCount})</span>
            </div>
          )}
        </div>
      </div>

      <hr className="border-slate-100" />

      {/* Additional Metrics */}
      <div className="space-y-2 pt-1 text-xs">
        <div className="flex items-center justify-between">
          <span className="text-slate-500">Total Vector Chunks</span>
          <span className="font-semibold text-slate-800">{totalChunks}</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-slate-500">Vector Embeddings</span>
          <span className="font-semibold text-emerald-600">3072 dims (Qdrant)</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-slate-500">Verification Model</span>
          <span className="font-semibold text-slate-800">Gemini 3.5 Lite</span>
        </div>
      </div>
    </div>
  );
}
