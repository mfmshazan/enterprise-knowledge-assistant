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
