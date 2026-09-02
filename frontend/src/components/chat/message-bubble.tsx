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
      className={`rounded-xl border p-2.5 text-xs transition-all duration-300 ${
        highlighted
          ? "border-indigo-400/80 bg-indigo-950/40 ring-2 ring-indigo-400/30"
          : "border-white/10 bg-white/[0.03] hover:border-white/20 hover:bg-white/[0.05]"
      }`}
    >
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 truncate">
          <span className="flex h-4 w-4 shrink-0 items-center justify-center rounded-md bg-gradient-to-r from-indigo-500 to-purple-500 text-[10px] font-bold text-white shadow-sm">
            {citation.rank}
          </span>
          <span className="truncate font-medium text-gray-200">
            {citation.document_title}
          </span>
        </div>
        {citation.snippet && (
          <button
            type="button"
            onClick={() => setExpanded(!expanded)}
            className="text-[11px] font-medium text-indigo-400 hover:text-indigo-300"
          >
            {expanded ? "Hide snippet" : "View snippet"}
          </button>
        )}
      </div>
      {expanded && citation.snippet && (
        <p className="mt-2 rounded-lg border border-white/5 bg-black/50 p-2 text-[11px] leading-relaxed text-gray-300">
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
            ? "bg-[color:var(--color-accent)] text-white shadow-lg shadow-[color:var(--color-accent)]/15"
            : "border border-white/10 bg-gradient-to-b from-white/[0.05] to-white/[0.02] text-[color:var(--color-foreground)] shadow-lg shadow-black/20 backdrop-blur-md"
        }`}
      >
        {!isUser && message.traces && message.traces.length > 0 && (
          <AgentTraceAccordion traces={message.traces} />
        )}

        {isUser ? (
          <div className="whitespace-pre-wrap leading-relaxed font-normal">{message.content}</div>
        ) : (
          <MarkdownRenderer
            content={message.content}
            citations={message.citations}
            onCitationClick={handleCitationClick}
          />
        )}

        {!isUser && message.citations.length > 0 && (
          <div className="space-y-2.5 border-t border-white/10 pt-3">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-gray-400">
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

