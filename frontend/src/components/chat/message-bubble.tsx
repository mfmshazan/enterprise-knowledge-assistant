import type { ChatMessageItem } from "@/lib/api";

export function MessageBubble({ message }: { message: ChatMessageItem }) {
  const isUser = message.role === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[85%] space-y-2 rounded-2xl px-4 py-2.5 text-sm ${
          isUser ? "bg-[color:var(--color-accent)] text-white" : "bg-white/5 border border-white/10"
        }`}
      >
        <p className="whitespace-pre-wrap">{message.content}</p>

        {message.citations.length > 0 && (
          <div className="space-y-1 border-t border-white/10 pt-2">
            <p className="text-xs font-medium text-[color:var(--color-muted)]">Sources</p>
            <ol className="space-y-1">
              {message.citations.map((c) => (
                <li key={c.rank} className="text-xs text-[color:var(--color-muted)]">
                  <span className="mr-1 font-semibold">[{c.rank}]</span>
                  <span className="font-medium text-[color:var(--color-foreground)]">
                    {c.document_title}
                  </span>
                  {c.snippet && <span className="ml-1 line-clamp-2">— {c.snippet}</span>}
                </li>
              ))}
            </ol>
          </div>
        )}
      </div>
    </div>
  );
}
