"use client";

import React, { useState } from "react";
import type { Citation } from "@/lib/api";

interface MarkdownRendererProps {
  content: string;
  citations?: Citation[];
  onCitationClick?: (rank: number) => void;
}

export function MarkdownRenderer({
  content,
  citations = [],
  onCitationClick,
}: MarkdownRendererProps) {
  const parts = content.split(/(```[\s\S]*?```)/g);

  return (
    <div className="space-y-3 leading-relaxed text-sm text-slate-800 selection:bg-indigo-500/20">
      {parts.map((part, index) => {
        if (part.startsWith("```") && part.endsWith("```")) {
          return <CodeBlock key={index} raw={part} />;
        }
        return (
          <TextBlock
            key={index}
            text={part}
            citations={citations}
            onCitationClick={onCitationClick}
          />
        );
      })}
    </div>
  );
}

function CodeBlock({ raw }: { raw: string }) {
  const [copied, setCopied] = useState(false);
  const lines = raw.slice(3, -3).trim().split("\n");
  const language = lines[0]?.match(/^[a-zA-Z0-9_-]+$/) ? lines[0] : "";
  const code = language ? lines.slice(1).join("\n") : lines.join("\n");

  const handleCopy = async () => {
    await navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="group relative my-3 overflow-hidden rounded-xl border border-slate-200 bg-slate-900 shadow-sm font-mono text-xs">
      <div className="flex items-center justify-between border-b border-slate-800 bg-slate-950 px-3 py-1.5 text-[11px] text-slate-400">
        <span className="font-semibold uppercase text-indigo-400">{language || "code"}</span>
        <button
          type="button"
          onClick={handleCopy}
          className="rounded px-2 py-0.5 text-slate-300 transition-colors hover:bg-slate-800 hover:text-white"
        >
          {copied ? "✓ Copied" : "Copy"}
        </button>
      </div>
      <pre className="overflow-x-auto p-3.5 text-slate-100 leading-normal">
        <code>{code}</code>
      </pre>
    </div>
  );
}

function TextBlock({
  text,
  citations,
  onCitationClick,
}: {
  text: string;
  citations: Citation[];
  onCitationClick?: (rank: number) => void;
}) {
  const lines = text.split("\n");
  const elements: React.ReactNode[] = [];
  let currentList: { type: "ul" | "ol"; items: string[] } | null = null;

  const flushList = () => {
    if (!currentList) return;
    if (currentList.type === "ul") {
      elements.push(
        <ul key={`ul-${elements.length}`} className="my-2 space-y-1.5 pl-1">
          {currentList.items.map((item, idx) => (
            <li key={idx} className="flex items-start gap-2.5 text-slate-800">
              <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-slate-400" />
              <div className="flex-1 leading-relaxed">
                <InlineFormatter
                  text={item}
                  citations={citations}
                  onCitationClick={onCitationClick}
                />
              </div>
            </li>
          ))}
        </ul>
      );
    } else {
      elements.push(
        <ol key={`ol-${elements.length}`} className="my-2 space-y-1.5 pl-1">
          {currentList.items.map((item, idx) => (
            <li key={idx} className="flex items-start gap-2.5 text-slate-800">
              <span className="text-xs font-bold text-slate-500 select-none">{idx + 1}.</span>
              <div className="flex-1 leading-relaxed">
                <InlineFormatter
                  text={item}
                  citations={citations}
                  onCitationClick={onCitationClick}
                />
              </div>
            </li>
          ))}
        </ol>
      );
    }
    currentList = null;
  };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const trimmed = line.trim();

    if (!trimmed) {
      flushList();
      continue;
    }

    if (trimmed.startsWith("### ")) {
      flushList();
      elements.push(
        <h3 key={i} className="mt-3.5 mb-1 text-xs font-bold text-indigo-700 tracking-wider uppercase">
          <InlineFormatter text={trimmed.slice(4)} citations={citations} onCitationClick={onCitationClick} />
        </h3>
      );
      continue;
    }
    if (trimmed.startsWith("## ")) {
      flushList();
      elements.push(
        <h2 key={i} className="mt-4 mb-2 text-sm font-bold text-slate-900 border-b border-slate-100 pb-1">
          <InlineFormatter text={trimmed.slice(3)} citations={citations} onCitationClick={onCitationClick} />
        </h2>
      );
      continue;
    }
    if (trimmed.startsWith("# ")) {
      flushList();
      elements.push(
        <h1 key={i} className="mt-4 mb-2 text-base font-extrabold text-slate-900">
          <InlineFormatter text={trimmed.slice(2)} citations={citations} onCitationClick={onCitationClick} />
        </h1>
      );
      continue;
    }

    const ulMatch = trimmed.match(/^[\*\-\+]\s+(.*)$/);
    if (ulMatch) {
      if (!currentList || currentList.type !== "ul") {
        flushList();
        currentList = { type: "ul", items: [] };
      }
      currentList.items.push(ulMatch[1]);
      continue;
    }

    const olMatch = trimmed.match(/^\d+\.\s+(.*)$/);
    if (olMatch) {
      if (!currentList || currentList.type !== "ol") {
        flushList();
        currentList = { type: "ol", items: [] };
      }
      currentList.items.push(olMatch[1]);
      continue;
    }

    if (trimmed.startsWith("> ")) {
      flushList();
      elements.push(
        <blockquote
          key={i}
          className="my-2 border-l-3 border-indigo-500 bg-indigo-50/50 px-3.5 py-2 rounded-r-xl text-xs italic text-slate-700"
        >
          <InlineFormatter text={trimmed.slice(2)} citations={citations} onCitationClick={onCitationClick} />
        </blockquote>
      );
      continue;
    }

    flushList();
    elements.push(
      <p key={i} className="my-1.5 leading-relaxed text-slate-800">
        <InlineFormatter text={trimmed} citations={citations} onCitationClick={onCitationClick} />
      </p>
    );
  }

  flushList();

  return <>{elements}</>;
}

function InlineFormatter({
  text,
  citations,
  onCitationClick,
}: {
  text: string;
  citations: Citation[];
  onCitationClick?: (rank: number) => void;
}) {
  const pattern = /(\[\s*\d+(?:\s*,\s*\d+)*\s*\]|`[^`]+`|\*\*[^*]+\*\*|\*[^*]+\*)/g;
  const tokens = text.split(pattern);

  return (
    <>
      {tokens.map((token, i) => {
        if (!token) return null;

        const citationMatch = token.match(/^\[\s*([\d\s,]+)\s*\]$/);
        if (citationMatch) {
          const ranks = citationMatch[1]
            .split(",")
            .map((s) => parseInt(s.trim(), 10))
            .filter((n) => !isNaN(n));

          return (
            <span key={i} className="inline-flex items-center gap-1 mx-1 align-baseline">
              {ranks.map((rank) => {
                const citedDoc = citations.find((c) => c.rank === rank);
                return (
                  <button
                    key={rank}
                    type="button"
                    onClick={() => onCitationClick?.(rank)}
                    title={citedDoc ? `Source: ${citedDoc.document_title}` : `Citation [${rank}]`}
                    className="inline-flex h-4 min-w-4 items-center justify-center rounded-md bg-indigo-100 border border-indigo-300 px-1 text-[10px] font-bold text-indigo-700 shadow-2xs transition-all hover:scale-110 hover:bg-indigo-600 hover:text-white"
                  >
                    {rank}
                  </button>
                );
              })}
            </span>
          );
        }

        if (token.startsWith("`") && token.endsWith("`") && token.length > 2) {
          return (
            <code
              key={i}
              className="mx-0.5 rounded-md border border-slate-200 bg-slate-100 px-1.5 py-0.5 font-mono text-[11px] font-medium text-indigo-700"
            >
              {token.slice(1, -1)}
            </code>
          );
        }

        if (token.startsWith("**") && token.endsWith("**") && token.length > 4) {
          return (
            <strong key={i} className="font-bold text-slate-900">
              {token.slice(2, -2)}
            </strong>
          );
        }

        if (token.startsWith("*") && token.endsWith("*") && token.length > 2) {
          return (
            <em key={i} className="italic text-slate-600">
              {token.slice(1, -1)}
            </em>
          );
        }

        return <span key={i}>{token}</span>;
      })}
    </>
  );
}
