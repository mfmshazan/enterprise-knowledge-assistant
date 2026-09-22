"use client";

import Link from "next/link";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Plus, X, MessageSquare, Brain, Zap, Sparkles, Send, Menu } from "lucide-react";

import { MessageBubble } from "@/components/chat/message-bubble";
import {
  deleteConversation,
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
  const searchParams = useSearchParams();
  const initialQuery = searchParams.get("q") || "";
  const orgId = useParams<{ orgId: string }>().orgId;
  const queryClient = useQueryClient();

  const [conversationId, setConversationId] = useState<string | null>(null);
  const [input, setInput] = useState(initialQuery);
  const [chatMode, setChatMode] = useState<ChatMode>("agentic");
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamSteps, setStreamSteps] = useState<AgentStepTrace[]>([]);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [localTracesMap, setLocalTracesMap] = useState<Record<string, AgentStepTrace[]>>({});
  const [sidebarOpen, setSidebarOpen] = useState(false);
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
      <main className="ambient-canvas flex min-h-screen items-center justify-center">
        <p className="text-sm font-medium text-slate-500">Loading chat…</p>
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
        }
      );

      if (!conversationId) {
        setConversationId(result.conversation_id);
        await queryClient.invalidateQueries({ queryKey: ["conversations", orgId] });
      }

      if (result.message?.id && collectedSteps.length > 0) {
        setLocalTracesMap((prev) => ({
          ...prev,
          [result.message.id]: collectedSteps,
        }));
      }

      await queryClient.invalidateQueries({
        queryKey: ["conversation", orgId, result.conversation_id],
      });
    } catch (err) {
      setErrorMessage((err as ApiError).message ?? "Failed to stream message");
    } finally {
      setIsStreaming(false);
      setStreamSteps([]);
    }
  };

  const handleDeleteConversation = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      const token = await getToken();
      await deleteConversation(token, orgId, id);
      if (conversationId === id) {
        setConversationId(null);
      }
      await queryClient.invalidateQueries({ queryKey: ["conversations", orgId] });
    } catch (err) {
      setErrorMessage((err as ApiError).message ?? "Failed to delete conversation");
    }
  };

  const messages: ChatMessageItem[] = (conversation.data?.messages ?? []).map((m) => {
    if (m.role === "assistant" && (!m.traces || m.traces.length === 0) && localTracesMap[m.id]) {
      return { ...m, traces: localTracesMap[m.id] };
    }
    return m;
  });

  return (
    <div className="h-screen ambient-canvas flex flex-col p-4 sm:p-6">
      <main className="mx-auto flex w-full max-w-7xl flex-1 gap-5 overflow-hidden">
        {/* Mobile drawer backdrop */}
        {sidebarOpen && (
          <div
            className="fixed inset-0 z-30 bg-slate-900/40 backdrop-blur-xs md:hidden"
            onClick={() => setSidebarOpen(false)}
            role="presentation"
          />
        )}

        {/* Left Rail: Conversations (static on desktop, slide-in drawer on mobile) */}
        <aside
          className={`fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r border-slate-200/90 bg-white p-4 shadow-xl transition-transform md:static md:z-auto md:translate-x-0 md:rounded-2xl md:border md:shadow-sm ${
            sidebarOpen ? "translate-x-0" : "-translate-x-full"
          }`}
        >
          <div className="mb-4 flex items-center justify-between">
            <Link
              href={`/orgs/${orgId}`}
              className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 transition-colors hover:text-slate-900"
            >
              <ArrowLeft className="h-3.5 w-3.5" aria-hidden /> Knowledge Base
            </Link>
            <button
              type="button"
              onClick={() => setSidebarOpen(false)}
              aria-label="Close conversations"
              className="rounded-lg p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-700 md:hidden"
            >
              <X className="h-4 w-4" aria-hidden />
            </button>
          </div>

          <button
            onClick={() => {
              setConversationId(null);
              setErrorMessage(null);
              setSidebarOpen(false);
            }}
            className="flex items-center justify-center gap-2 rounded-xl bg-indigo-600 px-3 py-2.5 text-xs font-semibold text-white shadow-sm transition-colors hover:bg-indigo-700"
          >
            <Plus className="h-4 w-4" aria-hidden /> New Chat
          </button>

          <div className="mt-5 min-h-0 flex-1 overflow-y-auto">
            <div className="mb-2.5 px-2 text-[11px] font-bold uppercase tracking-wider text-slate-400">
              Past Conversations
            </div>
            <ul className="space-y-1">
              {(conversations.data ?? []).map((c) => (
                <li
                  key={c.id}
                  className={`group flex items-center justify-between rounded-xl px-2.5 py-1.5 text-xs transition-colors ${
                    c.id === conversationId
                      ? "border border-indigo-200/80 bg-indigo-50 font-semibold text-indigo-900"
                      : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                  }`}
                >
                  <button
                    onClick={() => {
                      setConversationId(c.id);
                      setErrorMessage(null);
                      setSidebarOpen(false);
                    }}
                    className="flex-1 truncate py-1 text-left"
                    title={c.title}
                  >
                    {c.title}
                  </button>
                  <button
                    type="button"
                    onClick={(e) => handleDeleteConversation(c.id, e)}
                    aria-label="Delete conversation"
                    className="ml-1 rounded p-1 text-slate-400 opacity-0 transition-all hover:text-rose-600 group-hover:opacity-100"
                  >
                    <X className="h-3.5 w-3.5" aria-hidden />
                  </button>
                </li>
              ))}
            </ul>
          </div>
        </aside>

        {/* Main Chat Pane */}
        <section className="flex min-w-0 flex-1 flex-col rounded-2xl border border-slate-200/90 bg-white p-5 shadow-sm">
          {/* Header */}
          <div className="mb-3 flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 pb-3">
            <div className="flex items-center gap-2.5">
              <button
                type="button"
                onClick={() => setSidebarOpen(true)}
                aria-label="Open conversations"
                className="rounded-lg p-1.5 text-slate-500 hover:bg-slate-100 hover:text-slate-800 md:hidden"
              >
                <Menu className="h-5 w-5" aria-hidden />
              </button>
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-50 text-indigo-600">
                <MessageSquare className="h-4 w-4" aria-hidden />
              </div>
              <div>
                <h2 className="text-sm font-bold tracking-tight text-slate-900">
                  Knowledge Assistant
                </h2>
                <p className="text-[11px] text-slate-400">
                  Grounded in your enterprise indexed documents
                </p>
              </div>
            </div>

            {/* Mode Switcher */}
            <div className="flex items-center gap-1 rounded-xl border border-slate-200 bg-slate-50 p-1 text-xs font-semibold">
              <button
                type="button"
                onClick={() => setChatMode("agentic")}
                className={`flex items-center gap-1.5 rounded-lg px-3 py-1 transition-all ${
                  chatMode === "agentic"
                    ? "bg-white text-indigo-700 shadow-2xs"
                    : "text-slate-500 hover:text-slate-800"
                }`}
              >
                <Brain className="h-3.5 w-3.5" aria-hidden /> Agentic AI
              </button>
              <button
                type="button"
                onClick={() => setChatMode("linear")}
                className={`flex items-center gap-1.5 rounded-lg px-3 py-1 transition-all ${
                  chatMode === "linear"
                    ? "bg-white text-indigo-700 shadow-2xs"
                    : "text-slate-500 hover:text-slate-800"
                }`}
              >
                <Zap className="h-3.5 w-3.5" aria-hidden /> Fast Linear
              </button>
            </div>
          </div>

          {/* Message Thread */}
          <div className="min-h-0 flex-1 space-y-4 overflow-y-auto px-1 py-2">
            {messages.length === 0 && !isStreaming && (
              <div className="flex h-full flex-col items-center justify-center gap-2 text-center text-slate-400">
                <Sparkles className="h-9 w-9 text-indigo-300" aria-hidden />
                <p className="text-sm font-semibold text-slate-800">
                  Ask anything about your documents
                </p>
                <p className="max-w-md text-xs text-slate-500">
                  Answers are synthesized strictly from your uploaded files and web sources with verified citations.
                </p>
              </div>
            )}

            {messages.map((m) => (
              <MessageBubble key={m.id} message={m} />
            ))}

            {/* In-flight streaming status */}
            {isStreaming && (
              <div className="rounded-2xl border border-indigo-200 bg-indigo-50/50 p-4 text-xs text-indigo-900 space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 font-bold">
                    <span className="relative flex h-2 w-2">
                      <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-indigo-400 opacity-75"></span>
                      <span className="relative inline-flex h-2 w-2 rounded-full bg-indigo-600"></span>
                    </span>
                    <span>Agent Executing ({chatMode === "agentic" ? "LangGraph Multi-Agent" : "Linear RAG"})</span>
                  </div>
                  <span className="text-[10px] font-mono text-indigo-600">Active</span>
                </div>

                <div className="space-y-1">
                  {streamSteps.map((step, idx) => (
                    <div key={idx} className="flex items-start gap-2 rounded-lg bg-white/80 p-1.5 font-mono text-[11px] border border-indigo-100">
                      <span className="rounded bg-indigo-100 px-1 py-0.5 text-[10px] font-bold uppercase text-indigo-800">
                        {step.step}
                      </span>
                      <span className="text-slate-700">{step.status || "Processing..."}</span>
                    </div>
                  ))}
                  {streamSteps.length === 0 && (
                    <p className="text-[11px] text-slate-500">Connecting to reasoning stream…</p>
                  )}
                </div>
              </div>
            )}

            {errorMessage && (
              <div className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs font-semibold text-rose-600">
                {errorMessage}
              </div>
            )}
            <div ref={threadEndRef} />
          </div>

          {/* Prompt Form */}
          <form onSubmit={onSend} className="mt-3 flex gap-2">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={
                chatMode === "agentic"
                  ? "Ask a question (agent will plan, retrieve, and fact-check verify)…"
                  : "Ask a question (fast linear search & answer)…"
              }
              className="flex-1 rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-xs sm:text-sm text-slate-800 placeholder:text-slate-400 focus:border-indigo-500 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500/10"
            />
            <button
              type="submit"
              disabled={isStreaming || !input.trim()}
              className="flex items-center gap-1.5 rounded-xl bg-indigo-600 px-5 py-3 text-xs font-semibold text-white shadow-sm transition-colors hover:bg-indigo-700 disabled:opacity-50 sm:text-sm"
            >
              <span className="hidden sm:inline">Send</span>
              <Send className="h-4 w-4" aria-hidden />
            </button>
          </form>
        </section>
      </main>
    </div>
  );
}
