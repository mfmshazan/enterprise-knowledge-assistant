"use client";

import { useQuery } from "@tanstack/react-query";
import { getHealth } from "@/lib/api";

export function HealthStatus() {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["health"],
    queryFn: getHealth,
  });

  const dot = isLoading
    ? "bg-amber-400 animate-pulse"
    : isError
      ? "bg-rose-500"
      : "bg-emerald-500";

  return (
    <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-xs">
      <div className="flex items-center gap-2.5">
        <span className={`inline-block h-2.5 w-2.5 rounded-full ${dot}`} />
        <span className="text-sm font-bold text-slate-900 tracking-tight">Backend Status</span>
        <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-semibold text-slate-600">
          {isLoading ? "Connecting" : isError ? "Offline" : "Online"}
        </span>
      </div>

      <div className="mt-2 text-xs text-slate-500">
        {isLoading && <p>Checking backend connection…</p>}
        {isError && <p className="text-rose-600 font-medium">Unreachable: {(error as Error).message}</p>}
        {data && (
          <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-slate-600 font-medium">
            <span>Status: <strong className="text-emerald-600 font-semibold">{data.status}</strong></span>
            <span>•</span>
            <span>Version: <strong className="text-slate-800">{data.version}</strong></span>
            <span>•</span>
            <span>Environment: <strong className="text-slate-800">{data.environment}</strong></span>
          </div>
        )}
      </div>
    </div>
  );
}
