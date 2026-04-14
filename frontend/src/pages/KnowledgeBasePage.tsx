import { useMemo, useState } from "react";
import Badge from "../components/ui/Badge";
import Button from "../components/ui/Button";
import Card from "../components/ui/Card";
import { ingestSeed, ingestText } from "../api/client";
import { useToast } from "../components/toast/ToastProvider";

type Domain = "all" | "healthcare" | "government" | "finance" | "education";

type DocRow = {
  source: string;
  domain: Exclude<Domain, "all">;
  language: string;
  chunkCount: number;
};

const mockDocs: DocRow[] = [
  { source: "pmjay.gov.in", domain: "healthcare", language: "en", chunkCount: 6 },
  { source: "pmkisan.gov.in", domain: "government", language: "en", chunkCount: 5 },
  { source: "pmjdy.gov.in", domain: "finance", language: "en", chunkCount: 4 },
  { source: "scholarships.gov.in", domain: "education", language: "en", chunkCount: 4 },
];

function domainTone(domain: string) {
  switch (domain) {
    case "healthcare":
      return "green";
    case "government":
      return "blue";
    case "finance":
      return "amber";
    case "education":
      return "purple";
    default:
      return "slate";
  }
}

function Tab({
  active,
  label,
  onClick,
}: {
  active: boolean;
  label: string;
  onClick: () => void;
}) {
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

  const [text, setText] = useState("");
  const [source, setSource] = useState("admin-ui");
  const [textDomain, setTextDomain] = useState<Exclude<Domain, "all">>("healthcare");
  const [language, setLanguage] = useState("en");
  const [submitting, setSubmitting] = useState(false);
  const [seeding, setSeeding] = useState(false);

  const docs = useMemo(() => {
    if (domain === "all") return mockDocs;
    return mockDocs.filter((d) => d.domain === domain);
  }, [domain]);

  return (
    <div className="space-y-6">
      <Card className="p-4">
        <div className="text-base font-semibold text-white">Domain filter</div>
        <div className="mt-3 flex flex-wrap gap-2">
          <Tab active={domain === "all"} label="All" onClick={() => setDomain("all")} />
          <Tab
            active={domain === "healthcare"}
            label="Healthcare"
            onClick={() => setDomain("healthcare")}
          />
          <Tab
            active={domain === "government"}
            label="Government"
            onClick={() => setDomain("government")}
          />
          <Tab
            active={domain === "finance"}
            label="Finance"
            onClick={() => setDomain("finance")}
          />
          <Tab
            active={domain === "education"}
            label="Education"
            onClick={() => setDomain("education")}
          />
        </div>
      </Card>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-base font-semibold text-white">Documents</div>
              <div className="text-sm text-slate-400">Mock list for now.</div>
            </div>
          </div>

          <div className="mt-4 space-y-3">
            {docs.map((d) => (
              <div
                key={`${d.source}-${d.domain}`}
                className="flex items-center justify-between rounded-xl border border-slate-800 bg-slate-950/40 p-3"
              >
                <div className="min-w-0">
                  <div className="truncate font-medium text-slate-100">{d.source}</div>
                  <div className="mt-1 flex items-center gap-2 text-xs text-slate-400">
                    <Badge tone={domainTone(d.domain) as any}>
                      {d.domain.charAt(0).toUpperCase() + d.domain.slice(1)}
                    </Badge>
                    <Badge tone="slate">{d.language.toUpperCase()}</Badge>
                    <span>{d.chunkCount} chunks</span>
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
                      const res = await ingestText({
                        text,
                        source,
                        domain: textDomain,
                        language,
                      });
                      pushToast(`${res.chunks_ingested} chunks ingested`);
                      setText("");
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
              Seeds your knowledge base from <span className="font-mono">data/knowledge_base/seed_data.json</span>.
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
                  } catch (e: any) {
                    pushToast(e?.message ?? "Failed to seed demo data");
                  } finally {
                    setSeeding(false);
                  }
                }}
              >
                ■ Seed Demo Data
              </Button>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
