"use client";

/**
 * React Query hooks that bind API calls to the current auth session.
 *
 * Each hook pulls a token from `useAuth()` and is disabled until the user is
 * signed in, so no unauthenticated requests fire. Mutations invalidate the
 * relevant caches so the UI refreshes automatically.
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { createOrg, getMe, type MeResponse } from "@/lib/api";
import { useAuth } from "@/lib/auth/context";

export function useMe() {
  const { getToken, isSignedIn, isLoaded } = useAuth();

  return useQuery<MeResponse>({
    queryKey: ["me"],
    enabled: isLoaded && isSignedIn,
    queryFn: async () => getMe(await getToken()),
  });
}

export function useCreateOrg() {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (input: { name: string; slug?: string }) =>
      createOrg(await getToken(), input),
    onSuccess: () => {
      // "me" carries the membership list, so refetch it after creating an org.
      void queryClient.invalidateQueries({ queryKey: ["me"] });
    },
  });
}
