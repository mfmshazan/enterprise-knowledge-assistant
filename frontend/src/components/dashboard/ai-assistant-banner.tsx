"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

interface AiAssistantBannerProps {
  userName?: string | null;
  orgId: string;
}

export function AiAssistantBanner({ userName, orgId }: AiAssistantBannerProps) {
  const router = useRouter();
  const [query, setQuery] = useState("");

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return "Good morning";
    if (hour < 17) return "Good afternoon";
    return "Good evening";
  };

  const displayName = userName ? userName.split("@")[0].split(" ")[0] : "there";
  // Capitalize first letter
  const formattedName = displayName.charAt(0).toUpperCase() + displayName.slice(1);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    router.push(`/orgs/${orgId}/chat?q=${encodeURIComponent(query.trim())}`);
  };

  return (
    <div className="space-y-4">
      {/* Greeting with sunrise icon */}
      <div className="flex items-center gap-2">
        <span className="text-2xl" role="img" aria-label="sunrise">
          🌅
        </span>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">
          {getGreeting()}! {formattedName}
        </h1>
      </div>

      {/* AI Assistant Search & Prompt Bar */}
      <form
        onSubmit={handleSubmit}
        className="group relative flex items-center rounded-2xl border border-slate-200/80 bg-white/95 px-4 py-3.5 shadow-sm transition-all focus-within:border-indigo-500 focus-within:ring-4 focus-within:ring-indigo-500/10 hover:border-slate-300 hover:shadow"
      >
        <span className="mr-3 text-lg text-indigo-500 font-semibold select-none">
          ✦
        </span>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Hi, I'm your Knowledge Assistant. How can I assist you today?"
          className="w-full bg-transparent text-sm sm:text-base text-slate-800 placeholder:text-slate-400 focus:outline-none"
        />
        <button
          type="submit"
          className="ml-2 flex shrink-0 items-center justify-center rounded-xl bg-indigo-600 px-4 py-2 text-xs font-semibold text-white shadow-sm transition-all hover:bg-indigo-700 active:scale-95"
        >
          Ask AI →
        </button>
      </form>
    </div>
  );
}
