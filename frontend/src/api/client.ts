import axios from "axios";

export const api = axios.create({
  baseURL: (() => {
    const raw = (import.meta.env.VITE_API_URL as string | undefined) ?? "http://localhost:8000";
    return raw.endsWith("/api/v1") ? raw : `${raw.replace(/\/+$/, "")}/api/v1`;
  })(),
  headers: { "content-type": "application/json" },
});

export type QueryResponse = {
  answer: string;
  sources: Array<{
    id?: string | null;
    text?: string | null;
    score?: number | null;
    metadata?: Record<string, unknown>;
  }>;
};

export async function queryKb(body: { query: string; user_id?: string; top_k?: number }) {
  const { data } = await api.post<QueryResponse>("/query", body);
  return data;
}

export async function ingestText(body: {
  text: string;
  source: string;
  domain: string;
  language?: string;
}) {
  const { data } = await api.post<{ chunks_ingested: number }>("/ingest/text", body);
  return data;
}

export async function ingestSeed() {
  const { data } = await api.post<{ total_chunks_ingested: number; documents_processed: number }>(
    "/ingest/seed",
    {}
  );
  return data;
}

export type SessionRow = {
  timestamp: string;
  query: string;
  language: string;
  domain: string;
  latency_ms: number;
  answered?: boolean;
  user_id?: string;
};

export type DashboardStats = {
  total_queries_today: number;
  avg_response_time_ms: number;
  languages_detected: number;
  domains_served: number;
  recent: SessionRow[];
};

export async function fetchDashboard(): Promise<DashboardStats> {
  const { data } = await api.get<DashboardStats>("/sessions/all");
  return data;
}

export type KnowledgeSource = {
  source: string;
  domain: string;
  language: string;
  chunk_count: number;
};

export type KnowledgeSources = {
  sources: KnowledgeSource[];
  total_chunks: number;
};

export async function fetchKnowledgeSources(): Promise<KnowledgeSources> {
  const { data } = await api.get<KnowledgeSources>("/knowledge/sources");
  return data;
}

export async function ingestUrl(body: { url: string; domain: string }) {
  const { data } = await api.post<{ chunks_ingested: number; language_detected: string }>(
    "/ingest/url",
    body
  );
  return data;
}

