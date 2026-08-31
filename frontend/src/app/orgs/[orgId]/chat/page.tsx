"use client";

/**
 * Chat workspace: ask questions over the org's documents and get grounded,
 * cited answers. Left rail lists conversations; the main pane is the thread.
 */

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { MessageBubble } from "@/components/chat/message-bubble";
import type { ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth/context";
import { useConversation, useConversations, useSendMessage } from "@/lib/chat";

export default function ChatPage() {
  const { isLoaded, isSignedIn } = useAuth();
  const router = useRouter();
  const orgId = useParams<{ orgId: string }>().orgId;

  const [conversationId, setConversationId] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const threadEndRef = useRef<HTMLDivElement>(null);

  const conversations = useConversations(orgId);
  const conversation = useConversation(orgId, conversationId);
  const send = useSendMessage(orgId);

  useEffect(() => {
    if (isLoaded && !isSignedIn) router.replace("/sign-in");
  }, [isLoaded, isSignedIn, router]);

  useEffect(() => {
    threadEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [conversation.data?.messages.length, send.isPending]);

  if (!isLoaded || !isSignedIn) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <p className="text-[color:var(--color-muted)]">Loading…</p>
      </main>
    );
  }

  const onSend = (e: React.FormEvent) => {
    e.preventDefault();
    const message = input.trim();
    if (!message || send.isPending) return;
    setInput("");
    send.mutate(
      { message, conversation_id: conversationId ?? undefined },
      { onSuccess: (data) => setConversationId(data.conversation_id) },
    );
  };

  const messages = conversation.data?.messages ?? [];

  return (
    <main className="mx-auto flex h-screen max-w-5xl gap-4 px-4 py-6">
      {/* Sidebar */}
      <aside className="hidden w-64 shrink-0 flex-col gap-3 sm:flex">
        <Link href={`/orgs/${orgId}`} className="text-sm text-[color:var(--color-muted)] hover:underline">
          ← Knowledge base
        </Link>
        <button
          onClick={() => setConversationId(null)}
          className="rounded-md bg-[color:var(--color-accent)] px-3 py-2 text-sm font-medium text-white hover:opacity-90"
        >
          + New chat
        </button>
        <div className="min-h-0 flex-1 overflow-y-auto">
          <ul className="space-y-1">
            {(conversations.data ?? []).map((c) => (
              <li key={c.id}>
                <button
                  onClick={() => setConversationId(c.id)}
                  className={`w-full truncate rounded-md px-2 py-1.5 text-left text-sm hover:bg-white/5 ${
                    c.id === conversationId ? "bg-white/10" : ""
                  }`}
                >
                  {c.title}
                </button>
              </li>
            ))}
          </ul>
        </div>
      </aside>

      {/* Thread */}
      <section className="flex min-w-0 flex-1 flex-col">
        <div className="min-h-0 flex-1 space-y-4 overflow-y-auto rounded-xl border border-white/10 bg-white/[0.02] p-4">
          {messages.length === 0 && !send.isPending && (
            <div className="flex h-full items-center justify-center text-center text-sm text-[color:var(--color-muted)]">
              Ask a question about your documents to get a cited answer.
            </div>
          )}
          {messages.map((m) => (
            <MessageBubble key={m.id} message={m} />
          ))}
          {send.isPending && (
            <p className="text-sm text-[color:var(--color-muted)]">Thinking…</p>
          )}
          {send.error && (
            <p className="text-sm text-red-400">{(send.error as ApiError).message}</p>
          )}
          <div ref={threadEndRef} />
        </div>

        <form onSubmit={onSend} className="mt-3 flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question…"
            className="flex-1 rounded-md border border-white/10 bg-black/30 px-3 py-2.5 text-sm"
          />
          <button
            type="submit"
            disabled={send.isPending || !input.trim()}
            className="rounded-md bg-[color:var(--color-accent)] px-5 py-2.5 text-sm font-medium text-white hover:opacity-90 disabled:opacity-50"
          >
            Send
          </button>
        </form>
      </section>
    </main>
  );
}
