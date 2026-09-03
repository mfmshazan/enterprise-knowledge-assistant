import { useState } from "react";
import type { AgentStepTrace, ChatMessageItem, Citation } from "@/lib/api";
import { MarkdownRenderer } from "@/components/chat/markdown-renderer";

function CitationCard({
  citation,
  highlighted,
}: {
  citation: Citation;
  highlighted?: boolean;
}) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div
      id={`citation-${citation.rank}`}
      className={`rounded-xl border p-3 text-xs transition-all duration-300 ${
        highlighted
          ? "border-indigo-400 bg-indigo-50/70 ring-2 ring-indigo-400/20"
          : "border-slate-200/80 bg-slate-50/60 hover:border-slate-300 hover:bg-slate-50"
      }`}
    >
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 truncate">
          <span className="flex h-4 w-4 shrink-0 items-center justify-center rounded-md bg-indigo-600 text-[10px] font-bold text-white shadow-2xs">
            {citation.rank}
          </span>
          <span className="truncate font-semibold text-slate-800">
            {citation.document_title}
          </span>
        </div>
        {citation.snippet && (
          <button
            type="button"
            onClick={() => setExpanded(!expanded)}
            className="text-[11px] font-semibold text-indigo-600 hover:text-indigo-800"
          >
            {expanded ? "Hide snippet" : "View snippet"}
          </button>
        )}
      </div>
      {expanded && citation.snippet && (
        <p className="mt-2 rounded-lg border border-slate-200 bg-white p-2.5 text-[11px] leading-relaxed text-slate-700">
          {citation.snippet}
        </p>
      )}
    </div>
  );
}

function AgentTraceAccordion({ traces }: { traces: AgentStepTrace[] }) {
  const [open, setOpen] = useState(false);

  if (!traces || traces.length === 0) return null;

  return (
    <div className="rounded-xl border border-indigo-200/80 bg-indigo-50/50 p-2.5 text-xs">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between text-indigo-900 hover:text-indigo-950 font-medium"
      >
        <span className="flex items-center gap-1.5 font-bold">
          <span>🧠</span> Agent Reasoning &amp; Verification Trace ({traces.length} steps)
        </span>
        <span className="text-[11px] font-semibold text-indigo-600">
          {open ? "▲ Hide" : "▼ Show"}
        </span>
      </button>

      {open && (
        <div className="mt-2.5 space-y-1.5 border-t border-indigo-200/60 pt-2">
          {traces.map((trace, i) => (
            <div key={i} className="flex items-start gap-2 rounded-lg bg-white/80 p-2 text-[11px] border border-indigo-100 shadow-2xs">
              <span className="rounded-md bg-indigo-100 px-1.5 py-0.5 font-mono text-[10px] font-bold uppercase text-indigo-800">
                {trace.step}
              </span>
              <div className="flex-1 text-slate-700">
                {trace.status && <p className="font-semibold text-slate-900">{trace.status}</p>}
                {trace.search_query && (
                  <p className="font-mono text-[10px] text-indigo-600">Query: {trace.search_query}</p>
                )}
                {trace.sources && trace.sources.length > 0 && (
                  <p className="text-[10px] text-slate-500">
                    Sources: {trace.sources.join(", ")}
                  </p>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export function MessageBubble({ message }: { message: ChatMessageItem }) {
  const isUser = message.role === "user";
  const [activeCitationRank, setActiveCitationRank] = useState<number | null>(null);

  const handleCitationClick = (rank: number) => {
    setActiveCitationRank(rank);
    const el = document.getElementById(`citation-${rank}`);
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
  };

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[85%] space-y-3.5 rounded-2xl px-5 py-4 text-sm ${
          isUser
            ? "bg-indigo-600 text-white shadow-sm font-medium"
            : "border border-slate-200/90 bg-white text-slate-800 shadow-sm"
        }`}
      >
        {!isUser && message.traces && message.traces.length > 0 && (
          <AgentTraceAccordion traces={message.traces} />
        )}

        {isUser ? (
          <div className="whitespace-pre-wrap leading-relaxed">{message.content}</div>
        ) : (
          <MarkdownRenderer
            content={message.content}
            citations={message.citations}
            onCitationClick={handleCitationClick}
          />
        )}

        {!isUser && message.citations.length > 0 && (
          <div className="space-y-2.5 border-t border-slate-100 pt-3">
            <div className="flex items-center gap-1.5 text-xs font-bold text-slate-700">
              <span>📚</span> Verified Source Citations ({message.citations.length})
            </div>
            <div className="grid gap-2 sm:grid-cols-2">
              {message.citations.map((c) => (
                <CitationCard
                  key={c.rank}
                  citation={c}
                  highlighted={activeCitationRank === c.rank}
                />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
