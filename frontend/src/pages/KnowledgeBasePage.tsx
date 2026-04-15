import { useCallback, useEffect, useMemo, useState } from "react";
import Badge from "../components/ui/Badge";
import Button from "../components/ui/Button";
import Card from "../components/ui/Card";
import { fetchKnowledgeSources, ingestSeed, ingestText, ingestUrl, type KnowledgeSource } from "../api/client";
import { useToast } from "../components/toast/ToastProvider";

type Domain = "all" | "healthcare" | "government" | "finance" | "education";

function domainTone(domain: string) {
  switch (domain) {
    case "healthcare": return "green";
    case "government": return "blue";
    case "finance": return "amber";
    case "education": return "purple";
    default: return "slate";
  }
}

function Tab({ active, label, onClick }: { active: boolean; label: string; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className={[
        "rounded-xl px-3 py-2 text-sm font-semibold transition",
        active ? "bg-slate-800 text-white" : "text-slate-300 hover:bg-slate-800/60",
      ].join(" ")}
    >
      {label}
    </button>
  );
}

export default function KnowledgeBasePage() {
  const { pushToast } = useToast();

  const [domain, setDomain] = useState<Domain>("all");
  const [sources, setSources] = useState<KnowledgeSource[]>([]);
  const [totalChunks, setTotalChunks] = useState(0);
  const [loadingDocs, setLoadingDocs] = useState(false);

  const [text, setText] = useState("");
  const [source, setSource] = useState("admin-ui");
  const [textDomain, setTextDomain] = useState<Exclude<Domain, "all">>("healthcare");
  const [language, setLanguage] = useState("en");
  const [submitting, setSubmitting] = useState(false);
  const [seeding, setSeeding] = useState(false);

  const [url, setUrl] = useState("");
  const [urlDomain, setUrlDomain] = useState<Exclude<Domain, "all">>("healthcare");
  const [fetchingUrl, setFetchingUrl] = useState(false);

  const loadSources = useCallback(async () => {
    setLoadingDocs(true);
    try {
      const res = await fetchKnowledgeSources();
      setSources(res.sources);
      setTotalChunks(res.total_chunks);
    } catch (e: any) {
      pushToast(e?.message ?? "Failed to load knowledge base");
    } finally {
      setLoadingDocs(false);
    }
  }, [pushToast]);

  useEffect(() => {
    loadSources();
  }, [loadSources]);

  const filtered = useMemo(
    () => (domain === "all" ? sources : sources.filter((s) => s.domain === domain)),
    [sources, domain]
  );

  return (
    <div className="space-y-6">
      <Card className="p-4">
        <div className="flex items-center justify-between">
          <div className="text-base font-semibold text-white">Domain filter</div>
          <div className="text-sm text-slate-400">
            {totalChunks} total chunks in knowledge base
          </div>
        </div>
        <div className="mt-3 flex flex-wrap gap-2">
          <Tab active={domain === "all"} label="All" onClick={() => setDomain("all")} />
          <Tab active={domain === "healthcare"} label="Healthcare" onClick={() => setDomain("healthcare")} />
          <Tab active={domain === "government"} label="Government" onClick={() => setDomain("government")} />
          <Tab active={domain === "finance"} label="Finance" onClick={() => setDomain("finance")} />
          <Tab active={domain === "education"} label="Education" onClick={() => setDomain("education")} />
        </div>
      </Card>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-base font-semibold text-white">Documents</div>
              <div className="text-sm text-slate-400">
                {loadingDocs ? "Loading..." : `${filtered.length} source${filtered.length !== 1 ? "s" : ""}`}
              </div>
            </div>
            <Button variant="secondary" onClick={loadSources} disabled={loadingDocs}>
              Refresh
            </Button>
          </div>

          <div className="mt-4 space-y-3">
            {!loadingDocs && filtered.length === 0 && (
              <div className="text-sm text-slate-400">
                No documents found. Seed demo data or add text to get started.
              </div>
            )}
            {filtered.map((d) => (
              <div
                key={d.source}
                className="flex items-center justify-between rounded-xl border border-slate-800 bg-slate-950/40 p-3"
              >
                <div className="min-w-0">
                  <div className="truncate font-medium text-slate-100">{d.source}</div>
                  <div className="mt-1 flex items-center gap-2 text-xs text-slate-400">
                    <Badge tone={domainTone(d.domain) as any}>
                      {d.domain.charAt(0).toUpperCase() + d.domain.slice(1)}
                    </Badge>
                    <Badge tone="slate">{d.language.toUpperCase()}</Badge>
                    <span>{d.chunk_count} chunks</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>

        <div className="space-y-6">
          <Card className="p-4">
            <div className="text-base font-semibold text-white">Add Text</div>
            <div className="mt-4 space-y-3">
              <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                <label className="block">
                  <div className="text-xs font-semibold text-slate-400">Domain</div>
                  <select
                    value={textDomain}
                    onChange={(e) => setTextDomain(e.target.value as any)}
                    className="mt-1 w-full rounded-xl border border-slate-800 bg-slate-950/40 px-3 py-2 text-sm text-slate-100"
                  >
                    <option value="healthcare">Healthcare</option>
                    <option value="government">Government</option>
                    <option value="finance">Finance</option>
                    <option value="education">Education</option>
                  </select>
                </label>
                <label className="block">
                  <div className="text-xs font-semibold text-slate-400">Language</div>
                  <select
                    value={language}
                    onChange={(e) => setLanguage(e.target.value)}
                    className="mt-1 w-full rounded-xl border border-slate-800 bg-slate-950/40 px-3 py-2 text-sm text-slate-100"
                  >
                    <option value="en">English</option>
                    <option value="hi">Hindi</option>
                    <option value="te">Telugu</option>
                    <option value="ta">Tamil</option>
                  </select>
                </label>
              </div>

              <label className="block">
                <div className="text-xs font-semibold text-slate-400">Source</div>
                <input
                  value={source}
                  onChange={(e) => setSource(e.target.value)}
                  className="mt-1 w-full rounded-xl border border-slate-800 bg-slate-950/40 px-3 py-2 text-sm text-slate-100"
                  placeholder="admin-ui"
                />
              </label>

              <label className="block">
                <div className="text-xs font-semibold text-slate-400">Text</div>
                <textarea
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  className="mt-1 min-h-[140px] w-full rounded-xl border border-slate-800 bg-slate-950/40 px-3 py-2 text-sm text-slate-100"
                  placeholder="Paste a paragraph to ingest..."
                />
              </label>

              <div className="flex items-center justify-end">
                <Button
                  variant="primary"
                  disabled={submitting || text.trim().length === 0}
                  onClick={async () => {
                    setSubmitting(true);
                    try {
                      const res = await ingestText({ text, source, domain: textDomain, language });
                      pushToast(`${res.chunks_ingested} chunks ingested`);
                      setText("");
                      await loadSources();
                    } catch (e: any) {
                      pushToast(e?.message ?? "Failed to ingest text");
                    } finally {
                      setSubmitting(false);
                    }
                  }}
                >
                  Submit
                </Button>
              </div>
            </div>
          </Card>

          <Card className="p-4">
            <div className="text-base font-semibold text-white">Demo seed data</div>
            <div className="mt-2 text-sm text-slate-400">
              Seeds your knowledge base from{" "}
              <span className="font-mono">data/knowledge_base/seed_data.json</span>.
            </div>
            <div className="mt-4">
              <Button
                variant="secondary"
                className="w-full"
                disabled={seeding}
                onClick={async () => {
                  setSeeding(true);
                  try {
                    await ingestSeed();
                    pushToast("20 documents ingested successfully!");
                    await loadSources();
                  } catch (e: any) {
                    pushToast(e?.message ?? "Failed to seed demo data");
                  } finally {
                    setSeeding(false);
                  }
                }}
              >
                Seed Demo Data
              </Button>
            </div>
          </Card>

          <Card className="p-4">
            <div className="text-base font-semibold text-white">Ingest from URL</div>
            <div className="mt-2 text-sm text-slate-400">
              Fetches a webpage, strips HTML, and ingests the text into the knowledge base.
            </div>
            <div className="mt-4 space-y-3">
              <label className="block">
                <div className="text-xs font-semibold text-slate-400">Domain</div>
                <select
                  value={urlDomain}
                  onChange={(e) => setUrlDomain(e.target.value as any)}
                  className="mt-1 w-full rounded-xl border border-slate-800 bg-slate-950/40 px-3 py-2 text-sm text-slate-100"
                >
                  <option value="healthcare">Healthcare</option>
                  <option value="government">Government</option>
                  <option value="finance">Finance</option>
                  <option value="education">Education</option>
                </select>
              </label>
              <label className="block">
                <div className="text-xs font-semibold text-slate-400">URL</div>
                <input
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  className="mt-1 w-full rounded-xl border border-slate-800 bg-slate-950/40 px-3 py-2 text-sm text-slate-100"
                  placeholder="https://example.gov.in/scheme"
                />
              </label>
              <div className="flex items-center justify-end">
                <Button
                  variant="primary"
                  disabled={fetchingUrl || url.trim().length === 0}
                  onClick={async () => {
                    setFetchingUrl(true);
                    try {
                      const res = await ingestUrl({ url: url.trim(), domain: urlDomain });
                      pushToast(`${res.chunks_ingested} chunks ingested (${res.language_detected})`);
                      setUrl("");
                      await loadSources();
                    } catch (e: any) {
                      pushToast(e?.message ?? "Failed to ingest URL");
                    } finally {
                      setFetchingUrl(false);
                    }
                  }}
                >
                  {fetchingUrl ? "Fetching..." : "Fetch & Ingest"}
                </Button>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
