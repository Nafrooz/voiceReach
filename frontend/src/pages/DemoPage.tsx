import { useEffect, useMemo, useState } from "react";
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
    case "general":
      return "slate";
    default:
      return "slate";
  }
}

function languageLabel(code: string | null) {
  switch ((code || "").toLowerCase()) {
    case "hi":
      return "Hindi";
    case "te":
      return "Telugu";
    case "ta":
      return "Tamil";
    case "en":
    default:
      return "English";
  }
}

export default function DemoPage() {
  const { pushToast } = useToast();
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [voiceStarting, setVoiceStarting] = useState(false);
  const [lastVoiceEvent, setLastVoiceEvent] = useState<string>("");

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
      setVoiceStarting(false);
      setLastVoiceEvent("call-start");
      pushToast("Voice connected. You can start speaking.");
    };
    const onCallEnd = () => {
      setVoiceStarting(false);
      setLastVoiceEvent("call-end");
      pushToast("Voice ended.");
    };
    const onCallStartFailed = (evt: any) => {
      setVoiceStarting(false);
      const stage = typeof evt?.stage === "string" ? evt.stage : "unknown";
      const err = typeof evt?.error === "string" ? evt.error : "unknown error";
      setLastVoiceEvent(`call-start-failed: ${stage}: ${err}`);
      pushToast(`Voice start failed (${stage}): ${err}`);
    };
    const onError = (evt: any) => {
      setVoiceStarting(false);
      const message =
        typeof evt?.error?.message === "string"
          ? evt.error.message
          : typeof evt?.message === "string"
            ? evt.message
            : typeof evt?.error === "string"
              ? evt.error
              : "Unknown voice error";
      setLastVoiceEvent(`error: ${message}`);
      pushToast(`Voice error: ${message}`);
    };

    // Vapi Web SDK events (see @vapi-ai/web docs)
    vapi.on("call-start", onCallStart);
    vapi.on("call-end", onCallEnd);
    vapi.on("call-start-failed", onCallStartFailed);
    vapi.on("error", onError);

    return () => {
      // The SDK's public types don't expose `off`, but it does expose `removeAllListeners`.
      // Remove listeners for these events to avoid duplicate toasts on hot reload.
      vapi.removeAllListeners("call-start");
      vapi.removeAllListeners("call-end");
      vapi.removeAllListeners("call-start-failed");
      vapi.removeAllListeners("error");
    };
  }, [vapi, pushToast]);

  const runQuery = async (q: string) => {
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

  const preflightMic = async (): Promise<boolean> => {
    if (typeof navigator === "undefined") return true;
    if (!navigator.mediaDevices?.getUserMedia) {
      pushToast("Your browser does not support microphone access (getUserMedia missing).");
      return false;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      stream.getTracks().forEach((t) => t.stop());
      return true;
    } catch (e: any) {
      const name = typeof e?.name === "string" ? e.name : "MicError";
      const msg = typeof e?.message === "string" ? e.message : "Microphone permission denied";
      pushToast(`Microphone blocked: ${name} (${msg})`);
      return false;
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
            disabled={!vapi || !vapiAssistantId || voiceStarting}
            onClick={async () => {
              if (!vapi) {
                pushToast("Set VITE_VAPI_PUBLIC_KEY to enable voice.");
                return;
              }
              if (!vapiAssistantId) {
                pushToast("Set VITE_VAPI_ASSISTANT_ID to enable voice.");
                return;
              }

              const ok = await preflightMic();
              if (!ok) return;

              setVoiceStarting(true);
              pushToast("Starting voice… (check mic permission prompt)");
              try {
                setLastVoiceEvent("start() called");
                await vapi.start(vapiAssistantId);
              } catch (e: any) {
                const msg = typeof e?.message === "string" ? e.message : "Failed to start voice";
                setVoiceStarting(false);
                setLastVoiceEvent(`start() rejected: ${msg}`);
                pushToast(`Voice start error: ${msg}`);
              }
            }}
            className="h-12 w-56"
          >
            {voiceStarting ? "Starting…" : "Microphone"}
          </Button>
          <div className="text-xs text-slate-400">
            {!vapiPublicKey || !vapiAssistantId ? (
              <>
                Set <span className="font-mono">VITE_VAPI_PUBLIC_KEY</span> and{" "}
                <span className="font-mono">VITE_VAPI_ASSISTANT_ID</span> to enable browser voice.
              </>
            ) : (
              <>Browser voice is enabled.</>
            )}
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
              {language && <Badge tone="slate">■ {languageLabel(language)}</Badge>}
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
