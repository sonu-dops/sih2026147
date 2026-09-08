/**
 * Centralized Fetch API client with loading, error states, and retry logic.
 */

import { APIErrorResponse } from "./types";

export class ApiError extends Error {
  code: string;
  statusCode: number;
  details?: Record<string, any>;

  constructor(code: string, message: string, statusCode: number, details?: Record<string, any>) {
    super(`[${code}] ${message}`);
    this.code = code;
    this.statusCode = statusCode;
    this.details = details;
  }
}

export class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = "http://127.0.0.1:8000") {
    this.baseUrl = baseUrl.replace(/\/$/, "");
  }

  async request<T>(
    endpoint: string,
    options: RequestInit = {},
    retries: number = 2
  ): Promise<T> {
    const url = `${this.baseUrl}/${endpoint.replace(/^\//, "")}`;
    const headers = new Headers(options.headers || {});
    headers.set("Accept", "application/json");

    if (options.body && !(options.body instanceof FormData) && !headers.has("Content-Type")) {
      headers.set("Content-Type", "application/json");
    }

    let lastError: any = null;
    for (let attempt = 0; attempt <= retries; attempt++) {
      try {
        const response = await fetch(url, {
          ...options,
          headers,
        });

        if (!response.ok) {
          let errorData: APIErrorResponse | null = null;
          try {
            errorData = await response.json();
          } catch {
            // fallback if not JSON
          }

          const code = errorData?.error?.code || `HTTP_${response.status}`;
          const message = errorData?.error?.message || response.statusText;
          const details = errorData?.error?.details;

          throw new ApiError(code, message, response.status, details);
        }

        if (response.status === 204) {
          return null as unknown as T;
        }

        return (await response.json()) as T;
      } catch (err: any) {
        lastError = err;
        if (err instanceof ApiError && err.statusCode < 500) {
          // Do not retry 4xx errors
          throw err;
        }
        if (attempt < retries) {
          await new Promise((res) => setTimeout(res, 500 * Math.pow(2, attempt)));
          continue;
        }
      }
    }

    throw lastError || new ApiError("NETWORK_ERROR", "Failed to reach server.", 503);
  }
}

export const defaultApiClient = new ApiClient();
