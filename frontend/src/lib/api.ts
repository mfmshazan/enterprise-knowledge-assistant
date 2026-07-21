/**
 * Typed API client for the FastAPI backend.
 *
 * A single, thin fetch wrapper keeps base-URL, headers, and error handling in
 * one place. Feature code calls `apiFetch<T>(path)` and gets parsed, typed data
 * or a thrown `ApiError` — it never touches `fetch` or URLs directly.
 */

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export async function apiFetch<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });

  if (!res.ok) {
    let message = res.statusText;
    try {
      const body = await res.json();
      message = body?.error?.message ?? message;
    } catch {
      /* non-JSON error body; fall back to statusText */
    }
    throw new ApiError(res.status, message);
  }

  return (await res.json()) as T;
}

// ---------- Endpoint types & functions ----------

export interface HealthResponse {
  status: string;
  version: string;
  environment: string;
}

export function getHealth(): Promise<HealthResponse> {
  return apiFetch<HealthResponse>("/health");
}
