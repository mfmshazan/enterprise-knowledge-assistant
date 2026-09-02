import { useState } from "react";
import type { AgentStepTrace, ChatMessageItem, Citation } from "@/lib/api";

function CitationCard({ citation }: { citation: Citation }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="rounded-lg border border-white/10 bg-white/[0.03] p-2 text-xs transition-colors hover:border-white/20">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-1.5 truncate">
          <span className="flex h-4 w-4 items-center justify-center rounded bg-[color:var(--color-accent)] text-[10px] font-bold text-white">
            {citation.rank}
          </span>
          <span className="truncate font-medium text-[color:var(--color-foreground)]">
            {citation.document_title}
          </span>
        </div>
        {citation.snippet && (
          <button
            type="button"
            onClick={() => setExpanded(!expanded)}
            className="text-[10px] text-[color:var(--color-muted)] hover:text-white"
          >
            {expanded ? "Hide snippet" : "View snippet"}
          </button>
        )}
      </div>
      {expanded && citation.snippet && (
        <p className="mt-1.5 rounded bg-black/40 p-1.5 text-[11px] leading-relaxed text-[color:var(--color-muted)]">
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
    <div className="rounded-xl border border-cyan-500/20 bg-cyan-950/20 p-2.5 text-xs">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between text-cyan-300 hover:text-cyan-200"
      >
        <span className="flex items-center gap-1.5 font-medium">
          <span>🧠</span> Agent Reasoning &amp; Verification Trace ({traces.length} steps)
        </span>
        <span className="text-[11px]">{open ? "▲ Hide" : "▼ Show"}</span>
      </button>

      {open && (
        <div className="mt-2.5 space-y-1.5 border-t border-cyan-500/20 pt-2">
          {traces.map((trace, i) => (
            <div key={i} className="flex items-start gap-2 rounded bg-black/30 p-1.5 text-[11px]">
              <span className="rounded bg-cyan-500/20 px-1.5 py-0.5 font-mono text-[10px] uppercase text-cyan-300">
                {trace.step}
              </span>
              <div className="flex-1 text-[color:var(--color-muted)]">
                {trace.status && <p className="text-gray-200">{trace.status}</p>}
                {trace.search_query && (
                  <p className="font-mono text-[10px] text-cyan-400">Query: {trace.search_query}</p>
                )}
                {trace.sources && trace.sources.length > 0 && (
                  <p className="text-[10px] text-gray-400">
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

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[85%] space-y-3 rounded-2xl px-4 py-3 text-sm ${
          isUser
            ? "bg-[color:var(--color-accent)] text-white shadow-md shadow-[color:var(--color-accent)]/10"
            : "border border-white/10 bg-white/[0.04] text-[color:var(--color-foreground)] backdrop-blur-sm"
        }`}
      >
        {!isUser && message.traces && message.traces.length > 0 && (
          <AgentTraceAccordion traces={message.traces} />
        )}

        <div className="whitespace-pre-wrap leading-relaxed">{message.content}</div>

        {!isUser && message.citations.length > 0 && (
          <div className="space-y-2 border-t border-white/10 pt-2.5">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-[color:var(--color-muted)]">
              <span>📚</span> Verified Sources ({message.citations.length})
            </div>
            <div className="grid gap-1.5 sm:grid-cols-2">
              {message.citations.map((c) => (
                <CitationCard key={c.rank} citation={c} />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

