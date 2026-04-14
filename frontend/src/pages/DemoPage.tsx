import { useMemo, useState } from "react";
import Card from "../components/ui/Card";
import Button from "../components/ui/Button";
import Badge from "../components/ui/Badge";
import { queryKb } from "../api/client";
import { useToast } from "../components/toast/ToastProvider";
import Vapi from "@vapi-ai/web";

function domainTone(domain: string) {
  switch ((domain || "").toLowerCase()) {
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

export default function DemoPage() {
  const { pushToast } = useToast();
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);

  const [language, setLanguage] = useState<string | null>(null);
  const [domain, setDomain] = useState<string | null>(null);
  const [chunks, setChunks] = useState<string[]>([]);
  const [answer, setAnswer] = useState<string>("");

  const vapiPublicKey = (import.meta.env.VITE_VAPI_PUBLIC_KEY as string | undefined) ?? "";
  const vapiAssistantId = (import.meta.env.VITE_VAPI_ASSISTANT_ID as string | undefined) ?? "";

  const vapi = useMemo(() => {
    if (!vapiPublicKey) return null;
    return new Vapi(vapiPublicKey);
  }, [vapiPublicKey]);

  const runQuery = async (q: string) => {
    setLoading(true);
    try {
      const res = await queryKb({ query: q });
      setAnswer(res.answer);
      const texts = (res.sources ?? []).map((s) => s.text).filter(Boolean) as string[];
      setChunks(texts);
      // Until backend returns these explicitly, use simple heuristics.
      setLanguage(/[\u0900-\u097F]/.test(q) ? "Hindi" : "English");
      setDomain(texts.length ? "Knowledge Base" : "General");
    } catch (e: any) {
      pushToast(e?.message ?? "Query failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-[70vh] items-center justify-center">
      <Card className="w-full max-w-5xl p-6">
        <div className="text-center">
          <div className="text-2xl font-semibold text-white">Try VoiceReach</div>
          <div className="mt-2 text-sm text-slate-400">
            Judges view — voice call via Vapi, or type a question to test the backend.
          </div>
        </div>

        <div className="mt-6 flex flex-col items-center gap-4">
          <Button
            variant="primary"
            disabled={!vapi || !vapiAssistantId}
            onClick={() => {
              if (!vapi) return;
              if (!vapiAssistantId) return;
              pushToast("Starting voice…");
              vapi.start(vapiAssistantId);
            }}
            className="h-12 w-56"
          >
            Microphone
          </Button>
          <div className="text-xs text-slate-400">
            Set <span className="font-mono">VITE_VAPI_PUBLIC_KEY</span> and{" "}
            <span className="font-mono">VITE_VAPI_ASSISTANT_ID</span> to enable browser voice.
          </div>

          <div className="w-full">
            <div className="text-sm font-semibold text-slate-200">Or type your question here</div>
            <div className="mt-2 flex gap-2">
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="w-full rounded-xl border border-slate-800 bg-slate-950/40 px-3 py-2 text-sm text-slate-100"
                placeholder="Ask about PM-JAY, PM Kisan, CSC, Jan Dhan, UPI safety..."
              />
              <Button
                variant="secondary"
                disabled={loading || query.trim().length === 0}
                onClick={() => runQuery(query)}
              >
                Ask
              </Button>
            </div>
          </div>
        </div>

        {(answer || chunks.length > 0) && (
          <div className="mt-6">
            <div className="mb-3 flex flex-wrap items-center gap-2">
              {language && <Badge tone="slate">■ {language}</Badge>}
              {domain && <Badge tone={domainTone(domain) as any}>■ {domain}</Badge>}
            </div>

            <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
              <Card className="p-4">
                <div className="text-sm font-semibold text-white">■ Knowledge Retrieved</div>
                <div className="mt-2 space-y-2">
                  {chunks.length === 0 ? (
                    <div className="text-sm text-slate-400">
                      No chunks returned yet (backend will populate this from Qdrant).
                    </div>
                  ) : (
                    chunks.slice(0, 6).map((c, idx) => (
                      <div
                        key={idx}
                        className="rounded-xl border border-slate-800 bg-slate-950/40 p-3 text-sm text-slate-200"
                      >
                        {c}
                      </div>
                    ))
                  )}
                </div>
              </Card>

              <Card className="p-4">
                <div className="text-sm font-semibold text-white">■ Agent Response</div>
                <div className="mt-2 whitespace-pre-wrap text-sm text-slate-200">{answer}</div>
              </Card>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}
