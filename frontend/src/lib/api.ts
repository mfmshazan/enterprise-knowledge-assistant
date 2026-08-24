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
