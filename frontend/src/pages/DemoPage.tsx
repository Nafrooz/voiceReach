import { useEffect, useMemo, useState } from "react";
import Card from "../components/ui/Card";
import Button from "../components/ui/Button";
import Badge from "../components/ui/Badge";
import { queryKb } from "../api/client";
import { useToast } from "../components/toast/ToastProvider";
import Vapi from "@vapi-ai/web";

function domainTone(domain: string) {
  switch ((domain || "").toLowerCase()) {
    case "healthcare": return "green";
    case "government": return "blue";
    case "finance": return "amber";
    case "education": return "purple";
    default: return "slate";
  }
}

function languageLabel(code: string | null) {
  switch ((code || "").toLowerCase()) {
    case "hi": return "Hindi";
    case "te": return "Telugu";
    case "ta": return "Tamil";
    default: return "English";
  }
}

export default function DemoPage() {
  const { pushToast } = useToast();
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [callActive, setCallActive] = useState(false);
  const [callStarting, setCallStarting] = useState(false);

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

  useEffect(() => {
    if (!vapi) return;

    const onCallStart = () => {
      setCallStarting(false);
      setCallActive(true);
      pushToast("Voice connected. Start speaking.");
    };
    const onCallEnd = () => {
      setCallActive(false);
      setCallStarting(false);
      pushToast("Voice call ended.");
    };
    const onError = (evt: any) => {
      setCallActive(false);
      setCallStarting(false);
      const msg =
        evt?.error?.message ?? evt?.message ?? evt?.error ?? "Unknown voice error";
      pushToast(`Voice error: ${msg}`);
    };

    vapi.on("call-start", onCallStart);
    vapi.on("call-end", onCallEnd);
    vapi.on("error", onError);

    return () => {
      vapi.removeAllListeners("call-start");
      vapi.removeAllListeners("call-end");
      vapi.removeAllListeners("error");
    };
  }, [vapi, pushToast]);

  const handleMicClick = async () => {
    if (callActive) {
      vapi?.stop();
      return;
    }

    if (!vapi || !vapiAssistantId) {
      pushToast("Vapi keys not configured.");
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      stream.getTracks().forEach((t) => t.stop());
    } catch {
      pushToast("Microphone permission denied.");
      return;
    }

    setCallStarting(true);
    try {
      await vapi.start(vapiAssistantId);
    } catch (e: any) {
      setCallStarting(false);
      pushToast(`Failed to start voice: ${e?.message ?? "unknown error"}`);
    }
  };

  const runQuery = async (q: string) => {
    if (!q.trim()) return;
    setLoading(true);
    try {
      const res = await queryKb({ query: q });
      setAnswer(res.answer);
      const texts = (res.sources ?? []).map((s) => s.text).filter(Boolean) as string[];
      setChunks(texts);
      setLanguage(res.language || "en");
      setDomain(res.domain || "general");
    } catch (e: any) {
      pushToast(e?.message ?? "Query failed");
    } finally {
      setLoading(false);
    }
  };

  const micEnabled = !!vapiPublicKey && !!vapiAssistantId;

  return (
    <div className="flex min-h-[70vh] items-center justify-center">
      <Card className="w-full max-w-5xl p-6">
        <div className="text-center">
          <div className="text-2xl font-semibold text-white">Try VoiceReach</div>
          <div className="mt-2 text-sm text-slate-400">
            Type your question or use the mic to start a live voice session via Vapi.
          </div>
        </div>

        <div className="mt-8 w-full">
          <div
            className={[
              "flex items-center gap-2 rounded-xl border bg-slate-950/40 px-3 py-2 transition focus-within:border-slate-500",
              callActive ? "border-red-500" : "border-slate-700",
            ].join(" ")}
          >
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !loading && query.trim()) runQuery(query);
              }}
              disabled={callActive}
              className="flex-1 bg-transparent text-sm text-slate-100 outline-none placeholder:text-slate-500 disabled:opacity-40"
              placeholder={
                callActive
                  ? "Voice call in progress..."
                  : "Ask about PM-JAY, PM Kisan, UPI safety, scholarships..."
              }
            />

            {/* Mic icon button */}
            <button
              onClick={handleMicClick}
              disabled={callStarting || !micEnabled}
              title={
                !micEnabled
                  ? "Set VITE_VAPI_PUBLIC_KEY and VITE_VAPI_ASSISTANT_ID to enable voice"
                  : callActive
                  ? "Stop voice call"
                  : "Start voice call"
              }
              className={[
                "flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full transition",
                callActive
                  ? "animate-pulse bg-red-500 text-white"
                  : callStarting
                  ? "bg-slate-700 text-slate-400"
                  : micEnabled
                  ? "text-slate-400 hover:bg-slate-700 hover:text-white"
                  : "cursor-not-allowed text-slate-600",
              ].join(" ")}
            >
              {callActive ? (
                // Stop square icon
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="h-4 w-4">
                  <rect x="6" y="6" width="12" height="12" rx="2" />
                </svg>
              ) : callStarting ? (
                // Spinner
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="h-4 w-4 animate-spin">
                  <circle cx="12" cy="12" r="10" strokeOpacity="0.25" />
                  <path d="M12 2a10 10 0 0 1 10 10" />
                </svg>
              ) : (
                // Mic icon
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="h-4 w-4">
                  <path d="M12 1a4 4 0 0 1 4 4v6a4 4 0 0 1-8 0V5a4 4 0 0 1 4-4zm-1 16.93V20H9a1 1 0 1 0 0 2h6a1 1 0 1 0 0-2h-2v-2.07A8.001 8.001 0 0 0 20 11a1 1 0 1 0-2 0 6 6 0 0 1-12 0 1 1 0 1 0-2 0 8.001 8.001 0 0 0 7 7.93z" />
                </svg>
              )}
            </button>

            {/* Ask button */}
            <Button
              variant="primary"
              disabled={loading || query.trim().length === 0 || callActive}
              onClick={() => runQuery(query)}
              className="flex-shrink-0 px-4 py-1.5 text-sm"
            >
              {loading ? "..." : "Ask"}
            </Button>
          </div>

          {/* Status line */}
          <div className="mt-2 h-4 text-xs">
            {callActive && (
              <span className="flex items-center gap-1.5 text-red-400">
                <span className="inline-block h-2 w-2 animate-pulse rounded-full bg-red-400" />
                Voice call active — speak now. Click the stop icon to end.
              </span>
            )}
            {callStarting && (
              <span className="text-slate-400">Connecting voice call...</span>
            )}
            {!micEnabled && (
              <span className="text-slate-600">
                Voice disabled — set VITE_VAPI_PUBLIC_KEY and VITE_VAPI_ASSISTANT_ID in frontend/.env
              </span>
            )}
          </div>
        </div>

        {(answer || chunks.length > 0) && (
          <div className="mt-6">
            <div className="mb-3 flex flex-wrap items-center gap-2">
              {language && <Badge tone="slate">■ {languageLabel(language)}</Badge>}
              {domain && <Badge tone={domainTone(domain) as any}>■ {domain}</Badge>}
            </div>

            <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
              <Card className="p-4">
                <div className="text-sm font-semibold text-white">■ Knowledge Retrieved</div>
                <div className="mt-2 space-y-2">
                  {chunks.length === 0 ? (
                    <div className="text-sm text-slate-400">
                      No matching knowledge found for this query.
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
