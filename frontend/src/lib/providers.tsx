"use client";

/**
 * Client-side providers tree.
 *
 * React Query manages server state (caching, refetching, loading/error states)
 * so components never hand-roll `useEffect` + `useState` data fetching. We
 * create the QueryClient inside `useState` so it is instantiated once per
 * browser session and never shared across users on the server.
 */

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState, type ReactNode } from "react";

export function Providers({ children }: { children: ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 30_000,
            retry: 1,
            refetchOnWindowFocus: false,
          },
        },
      }),
  );

  return (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}
