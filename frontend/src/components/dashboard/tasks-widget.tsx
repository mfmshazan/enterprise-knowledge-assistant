"use client";

import Link from "next/link";
import { useState } from "react";
import type { DocumentItem } from "@/lib/api";

interface TasksWidgetProps {
  documents: DocumentItem[];
  orgId: string;
}

export function TasksWidget({ documents, orgId }: TasksWidgetProps) {
  const [checkedIds, setCheckedIds] = useState<Record<string, boolean>>({});
  const [starredIds, setStarredIds] = useState<Record<string, boolean>>({});

  const toggleCheck = (id: string) => {
    setCheckedIds((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const toggleStar = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setStarredIds((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const displayDocs = documents.slice(0, 5);

  return (
    <div className="h-full flex flex-col justify-between rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm space-y-3.5">
      <div className="space-y-3.5">
        {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-bold text-slate-800 tracking-tight">Knowledge Tasks</h2>
        <span className="text-xs font-semibold text-indigo-600 hover:text-indigo-700 cursor-pointer">
          View all
        </span>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-xs">
        <div className="inline-flex items-center gap-1 rounded-lg border border-slate-200 bg-slate-50 px-2.5 py-1 font-medium text-slate-700">
          <span>Assign to me</span>
          <span className="text-[9px] text-slate-400">▼</span>
        </div>
        <span className="rounded-lg bg-indigo-50 px-2.5 py-1 font-medium text-indigo-600">
          Workflow
        </span>
        <span className="rounded-lg px-2.5 py-1 font-medium text-slate-500 hover:bg-slate-50 cursor-pointer">
          Feedback
        </span>
      </div>

      {/* Checklist List */}
      <div className="divide-y divide-slate-100">
        {displayDocs.length === 0 ? (
          <p className="py-4 text-center text-xs text-slate-400">
            No knowledge tasks yet. Upload documents to populate.
          </p>
        ) : (
          displayDocs.map((doc) => (
            <div
              key={doc.id}
              onClick={() => toggleCheck(doc.id)}
              className="group flex items-center justify-between py-2.5 cursor-pointer hover:bg-slate-50/80 px-1 rounded-lg transition-colors"
            >
              <div className="flex items-center gap-2.5 min-w-0 pr-2">
                <input
                  type="checkbox"
                  checked={!!checkedIds[doc.id]}
                  onChange={() => toggleCheck(doc.id)}
                  onClick={(e) => e.stopPropagation()}
                  className="h-3.5 w-3.5 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                />
                <span className="text-amber-500 text-xs select-none">📁</span>
                <span
                  className={`text-xs font-medium truncate ${
                    checkedIds[doc.id]
                      ? "line-through text-slate-400"
                      : "text-slate-700 group-hover:text-slate-900"
                  }`}
                  title={doc.title}
                >
                  {doc.title}
                </span>
              </div>
              <button
                type="button"
                onClick={(e) => toggleStar(doc.id, e)}
                className="text-xs transition-colors p-0.5"
                title="Star task"
              >
                {starredIds[doc.id] ? (
                  <span className="text-amber-400">★</span>
                ) : (
                  <span className="text-slate-300 group-hover:text-slate-400">☆</span>
                )}
              </button>
            </div>
          ))
        )}
      </div>
      </div>

      <div className="pt-2">
        <Link
          href={`/orgs/${orgId}/chat`}
          className="block w-full text-center rounded-xl bg-slate-50 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 transition-colors"
        >
          Ask AI about these tasks →
        </Link>
      </div>
    </div>
  );
}
