"use client";

/**
 * Live backend connectivity indicator.
 *
 * This is the Phase 1 proof that the frontend can reach the backend through the
 * typed API client + React Query. In later phases it becomes a small piece of
 * the admin/system-status UI.
 */

import { useQuery } from "@tanstack/react-query";
import { getHealth } from "@/lib/api";

export function HealthStatus() {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["health"],
    queryFn: getHealth,
  });

  const dot = isLoading
    ? "bg-yellow-400"
    : isError
      ? "bg-red-500"
      : "bg-green-500";

  return (
    <div className="rounded-xl border border-white/10 bg-white/5 p-5">
      <div className="flex items-center gap-3">
        <span className={`inline-block h-3 w-3 rounded-full ${dot}`} />
        <span className="font-medium">Backend status</span>
      </div>

      <div className="mt-3 text-sm text-[color:var(--color-muted)]">
        {isLoading && <p>Checking connection…</p>}
        {isError && <p>Unreachable: {(error as Error).message}</p>}
        {data && (
          <ul className="space-y-1">
            <li>Status: {data.status}</li>
            <li>Version: {data.version}</li>
            <li>Environment: {data.environment}</li>
          </ul>
        )}
      </div>
    </div>
  );
}
