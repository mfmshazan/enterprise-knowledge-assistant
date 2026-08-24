"use client";

/**
 * React Query hooks for documents.
 *
 * `useDocuments` polls while any document is still being processed (pending or
 * processing) and stops once everything is settled — cheap "live status" without
 * websockets. Mutations invalidate the list so the UI updates immediately.
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  deleteDocument,
  ingestUrl,
  listDocuments,
  uploadDocument,
  type DocumentItem,
} from "@/lib/api";
import { useAuth } from "@/lib/auth/context";

const IN_PROGRESS: DocumentItem["status"][] = ["pending", "processing"];

export function useDocuments(orgId: string) {
  const { getToken, isSignedIn, isLoaded } = useAuth();

  return useQuery<DocumentItem[]>({
    queryKey: ["documents", orgId],
    enabled: isLoaded && isSignedIn && Boolean(orgId),
    queryFn: async () => listDocuments(await getToken(), orgId),
    refetchInterval: (query) => {
      const docs = query.state.data ?? [];
      return docs.some((d) => IN_PROGRESS.includes(d.status)) ? 2000 : false;
    },
  });
}

export function useUploadDocument(orgId: string) {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (file: File) => uploadDocument(await getToken(), orgId, file),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["documents", orgId] });
    },
  });
}

export function useIngestUrl(orgId: string) {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (input: { url: string; title?: string }) =>
      ingestUrl(await getToken(), orgId, input),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["documents", orgId] });
    },
  });
}

export function useDeleteDocument(orgId: string) {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (documentId: string) => deleteDocument(await getToken(), orgId, documentId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["documents", orgId] });
    },
  });
}
