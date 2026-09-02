"use client";

/**
 * Chat workspace: ask questions over the org's documents and get grounded,
 * cited answers. Left rail lists conversations; the main pane is the thread.
 */

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { MessageBubble } from "@/components/chat/message-bubble";
import {
  streamChatMessage,
  type AgentStepTrace,
  type ApiError,
  type ChatMessageItem,
  type ChatMode,
} from "@/lib/api";
import { useAuth } from "@/lib/auth/context";
import { useConversation, useConversations } from "@/lib/chat";

export default function ChatPage() {
  const { isLoaded, isSignedIn, getToken } = useAuth();
  const router = useRouter();
  const orgId = useParams<{ orgId: string }>().orgId;
  const queryClient = useQueryClient();

  const [conversationId, setConversationId] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const [chatMode, setChatMode] = useState<ChatMode>("agentic");
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamSteps, setStreamSteps] = useState<AgentStepTrace[]>([]);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [localTracesMap, setLocalTracesMap] = useState<Record<string, AgentStepTrace[]>>({});
  const threadEndRef = useRef<HTMLDivElement>(null);

  const conversations = useConversations(orgId);
  const conversation = useConversation(orgId, conversationId);

  useEffect(() => {
    if (isLoaded && !isSignedIn) router.replace("/sign-in");
  }, [isLoaded, isSignedIn, router]);

  useEffect(() => {
    threadEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [conversation.data?.messages.length, isStreaming, streamSteps.length]);

  if (!isLoaded || !isSignedIn) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <p className="text-[color:var(--color-muted)]">Loading…</p>
      </main>
    );
  }

  const onSend = async (e: React.FormEvent) => {
    e.preventDefault();
    const message = input.trim();
    if (!message || isStreaming) return;

    setInput("");
    setErrorMessage(null);
    setIsStreaming(true);
    setStreamSteps([]);

    try {
      const token = await getToken();
      const collectedSteps: AgentStepTrace[] = [];

      const result = await streamChatMessage(
        token,
        orgId,
        {
          message,
          conversation_id: conversationId ?? undefined,
          mode: chatMode,
        },
        (step) => {
          collectedSteps.push(step);
          setStreamSteps([...collectedSteps]);
        },
      );

      if (result.message?.id && collectedSteps.length > 0) {
        setLocalTracesMap((prev) => ({
          ...prev,
          [result.message.id]: collectedSteps,
        }));
      }

      setConversationId(result.conversation_id);
      void queryClient.invalidateQueries({ queryKey: ["conversations", orgId] });
      void queryClient.invalidateQueries({
        queryKey: ["conversation", orgId, result.conversation_id],
      });
    } catch (err) {
      setErrorMessage((err as ApiError).message || "An unexpected error occurred.");
    } finally {
      setIsStreaming(false);
      setStreamSteps([]);
    }
  };

  const messages: ChatMessageItem[] = (conversation.data?.messages ?? []).map((m) => ({
    ...m,
    traces: localTracesMap[m.id] ?? m.traces,
  }));

  return (
    <main className="mx-auto flex h-screen max-w-6xl gap-4 px-4 py-6">
      {/* Sidebar */}
      <aside className="hidden w-72 shrink-0 flex-col gap-3 sm:flex">
        <Link
          href={`/orgs/${orgId}`}
          className="flex items-center gap-1.5 text-sm font-medium text-[color:var(--color-muted)] hover:text-white"
        >
          <span>←</span> Knowledge base
        </Link>
        <button
          onClick={() => {
            setConversationId(null);
            setErrorMessage(null);
          }}
          className="flex items-center justify-center gap-2 rounded-lg bg-[color:var(--color-accent)] px-3 py-2.5 text-sm font-medium text-white shadow-sm hover:opacity-90"
        >
          <span>+</span> New chat
        </button>

        <div className="min-h-0 flex-1 overflow-y-auto">
          <div className="mb-2 px-2 text-xs font-semibold uppercase tracking-wider text-[color:var(--color-muted)]">
            Past Conversations
          </div>
          <ul className="space-y-1">
            {(conversations.data ?? []).map((c) => (
              <li key={c.id}>
                <button
                  onClick={() => {
                    setConversationId(c.id);
                    setErrorMessage(null);
                  }}
                  className={`w-full truncate rounded-lg px-3 py-2 text-left text-sm transition-colors hover:bg-white/5 ${
                    c.id === conversationId ? "bg-white/10 font-medium text-white" : "text-gray-300"
                  }`}
                >
                  {c.title}
                </button>
              </li>
            ))}
          </ul>
        </div>
      </aside>

      {/* Main chat section */}
      <section className="flex min-w-0 flex-1 flex-col rounded-2xl border border-white/10 bg-white/[0.02] p-4 backdrop-blur-md">
        {/* Header with Mode Toggle */}
        <div className="mb-3 flex items-center justify-between border-b border-white/10 pb-3">
          <div className="flex items-center gap-2">
            <span className="text-lg">💬</span>
            <div>
              <h2 className="text-sm font-semibold">Knowledge Assistant</h2>
              <p className="text-[11px] text-[color:var(--color-muted)]">
                Org-scoped retrieval &amp; grounded citations
              </p>
            </div>
          </div>

          <div className="flex items-center gap-1 rounded-lg border border-white/10 bg-black/40 p-1 text-xs">
            <button
              type="button"
              onClick={() => setChatMode("agentic")}
              className={`flex items-center gap-1.5 rounded-md px-2.5 py-1 font-medium transition-colors ${
                chatMode === "agentic"
                  ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/30"
                  : "text-[color:var(--color-muted)] hover:text-white"
              }`}
            >
              <span>🧠</span> Agentic AI (LangGraph)
            </button>
            <button
              type="button"
              onClick={() => setChatMode("linear")}
              className={`flex items-center gap-1.5 rounded-md px-2.5 py-1 font-medium transition-colors ${
                chatMode === "linear"
                  ? "bg-[color:var(--color-accent)]/20 text-[color:var(--color-accent)] border border-[color:var(--color-accent)]/30"
                  : "text-[color:var(--color-muted)] hover:text-white"
              }`}
            >
              <span>⚡</span> Fast Linear RAG
            </button>
          </div>
        </div>

        {/* Message Thread */}
        <div className="min-h-0 flex-1 space-y-4 overflow-y-auto px-1 py-2">
          {messages.length === 0 && !isStreaming && (
            <div className="flex h-full flex-col items-center justify-center gap-2 text-center text-sm text-[color:var(--color-muted)]">
              <span className="text-3xl">✨</span>
              <p className="font-medium text-white">Ask anything about your documents</p>
              <p className="max-w-md text-xs">
                Answers are synthesized strictly from your uploaded files and web pages with
                verifiable citations.
              </p>
            </div>
          )}

          {messages.map((m) => (
            <MessageBubble key={m.id} message={m} />
          ))}

          {/* Real-time Agent Reasoning Step Progression */}
          {isStreaming && (
            <div className="rounded-xl border border-cyan-500/30 bg-cyan-950/20 p-3.5 text-xs text-cyan-200">
              <div className="mb-2 flex items-center justify-between">
                <div className="flex items-center gap-2 font-medium">
                  <span className="relative flex h-2 w-2">
                    <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-cyan-400 opacity-75"></span>
                    <span className="relative inline-flex h-2 w-2 rounded-full bg-cyan-500"></span>
                  </span>
                  <span>Agent Executing ({chatMode === "agentic" ? "LangGraph Multi-Agent" : "Linear RAG"})</span>
                </div>
                <span className="text-[11px] text-cyan-400 font-mono">In Progress</span>
              </div>

              <div className="space-y-1.5">
                {streamSteps.map((step, idx) => (
                  <div key={idx} className="flex items-start gap-2 rounded bg-black/40 p-1.5 font-mono text-[11px]">
                    <span className="rounded bg-cyan-500/20 px-1 py-0.5 text-[10px] uppercase text-cyan-300">
                      {step.step}
                    </span>
                    <span className="text-gray-300">{step.status || "Processing..."}</span>
                  </div>
                ))}
                {streamSteps.length === 0 && (
                  <p className="text-[11px] text-[color:var(--color-muted)]">Connecting to reasoning stream…</p>
                )}
              </div>
            </div>
          )}

          {errorMessage && (
            <div className="rounded-lg border border-red-500/30 bg-red-950/20 p-3 text-xs text-red-400">
              {errorMessage}
            </div>
          )}
          <div ref={threadEndRef} />
        </div>

        {/* Input Form */}
        <form onSubmit={onSend} className="mt-3 flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={
              chatMode === "agentic"
                ? "Ask a question (agent will plan, retrieve, and fact-check verify)…"
                : "Ask a question (fast linear search & answer)…"
            }
            className="flex-1 rounded-xl border border-white/10 bg-black/40 px-4 py-3 text-sm focus:border-cyan-500/50 focus:outline-none"
          />
          <button
            type="submit"
            disabled={isStreaming || !input.trim()}
            className="flex items-center gap-1.5 rounded-xl bg-[color:var(--color-accent)] px-5 py-3 text-sm font-medium text-white shadow-sm hover:opacity-90 disabled:opacity-50"
          >
            <span>Send</span>
            <span>↵</span>
          </button>
        </form>
      </section>
    </main>
  );
}

