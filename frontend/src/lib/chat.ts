"use client";

/**
 * React Query hooks for chat. The send mutation invalidates the conversation
 * list and the active conversation so the thread refreshes with the new turn.
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  getConversation,
  listConversations,
  sendChatMessage,
  type ConversationDetail,
  type ConversationSummary,
} from "@/lib/api";
import { useAuth } from "@/lib/auth/context";

export function useConversations(orgId: string) {
  const { getToken, isSignedIn, isLoaded } = useAuth();
  return useQuery<ConversationSummary[]>({
    queryKey: ["conversations", orgId],
    enabled: isLoaded && isSignedIn && Boolean(orgId),
    queryFn: async () => listConversations(await getToken(), orgId),
  });
}

export function useConversation(orgId: string, conversationId: string | null) {
  const { getToken, isSignedIn } = useAuth();
  return useQuery<ConversationDetail>({
    queryKey: ["conversation", orgId, conversationId],
    enabled: isSignedIn && Boolean(conversationId),
    queryFn: async () => getConversation(await getToken(), orgId, conversationId as string),
  });
}

export function useSendMessage(orgId: string) {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (input: { message: string; conversation_id?: string }) =>
      sendChatMessage(await getToken(), orgId, input),
    onSuccess: (data) => {
      void queryClient.invalidateQueries({ queryKey: ["conversations", orgId] });
      void queryClient.invalidateQueries({
        queryKey: ["conversation", orgId, data.conversation_id],
      });
    },
  });
}
