/**
 * Typed API client for the FastAPI backend.
 *
 * `apiFetch` centralizes base URL, auth header, JSON handling, and error
 * normalization. Pass a bearer `token` (from `useAuth().getToken()`) to call
 * protected endpoints. Errors are thrown as `ApiError` carrying the backend's
 * uniform `{ error: { code, message } }` envelope.
 */

import { API_BASE_URL } from "@/lib/config";

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
    public readonly code?: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

interface FetchOptions extends Omit<RequestInit, "body"> {
  token?: string | null;
  body?: unknown;
}

export async function apiFetch<T>(path: string, options: FetchOptions = {}): Promise<T> {
  const { token, body, headers, ...init } = options;

  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...headers,
    },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (res.status === 204) {
    return undefined as T;
  }

  const data = await res.json().catch(() => null);

  if (!res.ok) {
    const code = data?.error?.code as string | undefined;
    const message = (data?.error?.message as string | undefined) ?? res.statusText;
    throw new ApiError(res.status, message, code);
  }

  return data as T;
}

// ---------- Domain types (mirror backend schemas) ----------

export interface HealthResponse {
  status: string;
  version: string;
  environment: string;
}

export type Role = "owner" | "admin" | "member";

export interface Organization {
  id: string;
  name: string;
  slug: string;
  created_at: string;
}

export interface Membership {
  id: string;
  role: Role;
  created_at: string;
  organization: Organization;
}

export interface UserProfile {
  id: string;
  email: string;
  full_name: string | null;
  created_at: string;
}

export interface MeResponse {
  user: UserProfile;
  memberships: Membership[];
}

// ---------- Endpoint functions ----------

export const getHealth = () => apiFetch<HealthResponse>("/health");

export const getMe = (token: string | null) =>
  apiFetch<MeResponse>("/api/v1/users/me", { token });

export const listMyOrgs = (token: string | null) =>
  apiFetch<Membership[]>("/api/v1/orgs", { token });

export const createOrg = (token: string | null, input: { name: string; slug?: string }) =>
  apiFetch<Organization>("/api/v1/orgs", { method: "POST", token, body: input });

// ---------- Documents ----------

export type DocumentStatus = "pending" | "processing" | "indexed" | "failed";

export interface DocumentItem {
  id: string;
  source_type: "file" | "url";
  title: string;
  filename: string | null;
  content_type: string | null;
  source_url: string | null;
  size_bytes: number | null;
  status: DocumentStatus;
  error: string | null;
  chunk_count: number;
  created_at: string;
  updated_at: string;
}

const docsPath = (orgId: string) => `/api/v1/orgs/${orgId}/documents`;

export const listDocuments = (token: string | null, orgId: string) =>
  apiFetch<DocumentItem[]>(docsPath(orgId), { token });

export const ingestUrl = (
  token: string | null,
  orgId: string,
  input: { url: string; title?: string },
) => apiFetch<DocumentItem>(`${docsPath(orgId)}/url`, { method: "POST", token, body: input });

export const deleteDocument = (token: string | null, orgId: string, documentId: string) =>
  apiFetch<void>(`${docsPath(orgId)}/${documentId}`, { method: "DELETE", token });

/**
 * File upload is multipart/form-data, so it bypasses the JSON `apiFetch`: we let
 * the browser set the `Content-Type` (with boundary) by passing a FormData body.
 */
export async function uploadDocument(
  token: string | null,
  orgId: string,
  file: File,
): Promise<DocumentItem> {
  const form = new FormData();
  form.append("file", file);

  const res = await fetch(`${API_BASE_URL}${docsPath(orgId)}`, {
    method: "POST",
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: form,
  });

  const data = await res.json().catch(() => null);
  if (!res.ok) {
    const message = (data?.error?.message as string | undefined) ?? res.statusText;
    throw new ApiError(res.status, message, data?.error?.code);
  }
  return data as DocumentItem;
}

// ---------- Chat ----------

export type ChatMode = "linear" | "agentic";

export interface Citation {
  rank: number;
  document_id: string | null;
  chunk_id: string | null;
  document_title: string;
  snippet: string;
}

export interface AgentStepTrace {
  step: string;
  status?: string;
  search_query?: string;
  chunks_count?: number;
  sources?: string[];
  grounded?: boolean;
  attempt?: number;
  max_attempts?: number;
  [key: string]: unknown;
}

export interface ChatMessageItem {
  id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
  citations: Citation[];
  traces?: AgentStepTrace[];
}

export interface ChatSendResponse {
  conversation_id: string;
  message: ChatMessageItem;
}

export interface ConversationSummary {
  id: string;
  title: string;
  created_at: string;
}

export interface ConversationDetail {
  id: string;
  title: string;
  created_at: string;
  messages: ChatMessageItem[];
}

const chatPath = (orgId: string) => `/api/v1/orgs/${orgId}/chat`;

export const sendChatMessage = (
  token: string | null,
  orgId: string,
  input: { message: string; conversation_id?: string; top_k?: number; mode?: ChatMode },
) => apiFetch<ChatSendResponse>(chatPath(orgId), { method: "POST", token, body: input });

export async function streamChatMessage(
  token: string | null,
  orgId: string,
  input: { message: string; conversation_id?: string; top_k?: number; mode?: ChatMode },
  onStep?: (step: AgentStepTrace) => void,
): Promise<ChatSendResponse> {
  const res = await fetch(`${API_BASE_URL}${chatPath(orgId)}/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(input),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => null);
    const message = (errorData?.error?.message as string | undefined) ?? res.statusText;
    throw new ApiError(res.status, message, errorData?.error?.code);
  }

  if (!res.body) {
    throw new ApiError(500, "Readable stream not supported or empty body.");
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let finalResult: ChatSendResponse | null = null;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n\n");
    buffer = lines.pop() ?? "";

    for (const block of lines) {
      const line = block.trim();
      if (!line.startsWith("data: ")) continue;
      const jsonStr = line.slice(6);
      try {
        const payload = JSON.parse(jsonStr);
        if (payload.event === "step") {
          onStep?.({ step: payload.step, ...(payload.data ?? {}) });
        } else if (payload.event === "done") {
          finalResult = {
            conversation_id: payload.conversation_id,
            message: payload.message,
          };
        } else if (payload.event === "error") {
          throw new ApiError(500, payload.error ?? "Streaming error");
        }
      } catch (err) {
        if (err instanceof ApiError) throw err;
      }
    }
  }

  if (!finalResult) {
    throw new ApiError(500, "Stream concluded without final message payload.");
  }

  return finalResult;
}

export const listConversations = (token: string | null, orgId: string) =>
  apiFetch<ConversationSummary[]>(`${chatPath(orgId)}/conversations`, { token });

export const getConversation = (token: string | null, orgId: string, conversationId: string) =>
  apiFetch<ConversationDetail>(`${chatPath(orgId)}/conversations/${conversationId}`, { token });

export const deleteConversation = (token: string | null, orgId: string, conversationId: string) =>
  apiFetch<void>(`${chatPath(orgId)}/conversations/${conversationId}`, { method: "DELETE", token });

// ---------------------------------------------------------------------------
// Phase 7: Enterprise Features (Members, Audit Logs, API Keys)
// ---------------------------------------------------------------------------

export interface OrgMember {
  id: string;
  role: Role;
  created_at: string;
  user: UserProfile;
}

export const listOrgMembers = (token: string | null, orgId: string) =>
  apiFetch<OrgMember[]>(`/api/v1/orgs/${orgId}/members`, { token });

export const inviteOrgMember = (
  token: string | null,
  orgId: string,
  input: { email: string; role?: Role }
) =>
  apiFetch<OrgMember>(`/api/v1/orgs/${orgId}/members`, {
    method: "POST",
    token,
    body: input,
  });

export const updateOrgMemberRole = (
  token: string | null,
  orgId: string,
  userId: string,
  input: { role: Role }
) =>
  apiFetch<OrgMember>(`/api/v1/orgs/${orgId}/members/${userId}`, {
    method: "PATCH",
    token,
    body: input,
  });

export const removeOrgMember = (token: string | null, orgId: string, userId: string) =>
  apiFetch<void>(`/api/v1/orgs/${orgId}/members/${userId}`, {
    method: "DELETE",
    token,
  });

export interface AuditLogEntry {
  id: string;
  org_id: string;
  actor_user_id: string | null;
  action: string;
  resource_type: string;
  resource_id: string | null;
  metadata_: Record<string, unknown>;
  ip_address: string | null;
  created_at: string;
}

export interface AuditLogsResponse {
  items: AuditLogEntry[];
  total: number;
  page: number;
  page_size: number;
}

export const listAuditLogs = (
  token: string | null,
  orgId: string,
  params?: { action?: string; page?: number; page_size?: number }
) => {
  const query = new URLSearchParams();
  if (params?.action) query.set("action", params.action);
  if (params?.page) query.set("page", String(params.page));
  if (params?.page_size) query.set("page_size", String(params.page_size));
  const queryString = query.toString();
  return apiFetch<AuditLogsResponse>(
    `/api/v1/orgs/${orgId}/audit-logs${queryString ? `?${queryString}` : ""}`,
    { token }
  );
};

export interface ApiKeyItem {
  id: string;
  org_id: string;
  name: string;
  key_prefix: string;
  created_by_user_id: string | null;
  expires_at: string | null;
  revoked_at: string | null;
  created_at: string;
  is_active: boolean;
}

export interface ApiKeyCreatedResponse extends ApiKeyItem {
  secret_key: string;
}

export const listApiKeys = (token: string | null, orgId: string) =>
  apiFetch<ApiKeyItem[]>(`/api/v1/orgs/${orgId}/api-keys`, { token });

export const createApiKey = (
  token: string | null,
  orgId: string,
  input: { name: string; expires_in_days?: number }
) =>
  apiFetch<ApiKeyCreatedResponse>(`/api/v1/orgs/${orgId}/api-keys`, {
    method: "POST",
    token,
    body: input,
  });

export const revokeApiKey = (token: string | null, orgId: string, keyId: string) =>
  apiFetch<ApiKeyItem>(`/api/v1/orgs/${orgId}/api-keys/${keyId}`, {
    method: "DELETE",
    token,
  });


