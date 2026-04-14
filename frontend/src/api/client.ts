export type HttpMethod = "GET" | "POST" | "PUT" | "PATCH" | "DELETE";

export interface ApiClientOptions {
  baseUrl?: string;
}

export class ApiClient {
  private readonly baseUrl: string;

  constructor(opts: ApiClientOptions = {}) {
    this.baseUrl = opts.baseUrl ?? "";
  }

  async request<TResponse>(
    path: string,
    method: HttpMethod,
    body?: unknown
  ): Promise<TResponse> {
    const res = await fetch(`${this.baseUrl}${path}`, {
      method,
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(`API ${method} ${path} failed: ${res.status} ${text}`);
    }

    return (await res.json()) as TResponse;
  }

  post<TResponse>(path: string, body?: unknown) {
    return this.request<TResponse>(path, "POST", body);
  }

  get<TResponse>(path: string) {
    return this.request<TResponse>(path, "GET");
  }
}

import axios from "axios";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? "http://localhost:8000/api/v1",
  headers: { "content-type": "application/json" },
});

export type QueryResponse = {
  query: string;
  answer: string;
  matches: Array<{ id?: string; score?: number; payload?: Record<string, unknown> }>;
};

export async function queryKb(body: { query: string; limit?: number }) {
  const { data } = await api.post<QueryResponse>("/query/", body);
  return data;
}

export async function ingestText(body: {
  text: string;
  source: string;
  domain: string;
  language?: string;
}) {
  const { data } = await api.post<{ chunks_ingested: number; collection: string }>("/ingest/text", body);
  return data;
}

export async function ingestSeed() {
  const { data } = await api.post<{ chunks_ingested: number; collection: string }>("/ingest/seed", {});
  return data;
}

