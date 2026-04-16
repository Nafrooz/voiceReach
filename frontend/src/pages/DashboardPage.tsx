import { useEffect, useState } from "react";
import Badge from "../components/ui/Badge";
import Card from "../components/ui/Card";
import { fetchDashboard, type DashboardStats } from "../api/client";

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <Card className="p-4">
      <div className="text-sm text-slate-400">{label}</div>
      <div className="mt-1 text-2xl font-semibold text-white">{value}</div>
    </Card>
  );
}

function domainTone(domain: string) {
  switch (domain) {
    case "healthcare": return "green";
    case "government": return "blue";
    case "finance": return "amber";
    case "education": return "purple";
    default: return "slate";
  }
}

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchDashboard()
      .then(setStats)
      .catch((e) => setError(e?.message ?? "Failed to load dashboard"));
  }, []);

  if (error) {
    return (
      <div className="rounded-xl border border-red-800 bg-red-950/30 p-4 text-sm text-red-400">
        {error}
      </div>
    );
  }

  if (!stats) {
    return <div className="text-sm text-slate-400">Loading...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Total Queries Today" value={`${stats.total_queries_today}`} />
        <StatCard label="Avg Response Time" value={stats.avg_response_time_ms ? `${stats.avg_response_time_ms} ms` : "—"} />
        <StatCard label="Languages Detected" value={`${stats.languages_detected}`} />
        <StatCard label="Domains Served" value={`${stats.domains_served}`} />
      </div>

      <Card className="p-4">
        <div className="text-base font-semibold text-white">Recent queries</div>
        <div className="text-sm text-slate-400 mt-1">Live data from Qdrant sessions</div>

        {stats.recent.length === 0 ? (
          <div className="mt-4 text-sm text-slate-400">No queries yet — try asking something in the Demo tab.</div>
        ) : (
          <div className="mt-4 overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="text-slate-300">
                <tr className="border-b border-slate-800">
                  <th className="py-2 pr-4 font-semibold">timestamp</th>
                  <th className="py-2 pr-4 font-semibold">query preview</th>
                  <th className="py-2 pr-4 font-semibold">language</th>
                  <th className="py-2 pr-4 font-semibold">domain</th>
                  <th className="py-2 pr-4 font-semibold">status</th>
                  <th className="py-2 pr-0 font-semibold">latency</th>
                </tr>
              </thead>
              <tbody className="text-slate-200">
                {stats.recent.map((row, i) => (
                  <tr key={i} className="border-b border-slate-900">
                    <td className="py-3 pr-4 whitespace-nowrap text-slate-400">
                      {row.timestamp ? new Date(row.timestamp).toLocaleString() : "—"}
                    </td>
                    <td className="py-3 pr-4">
                      <div className="max-w-[36rem] truncate">{row.query}</div>
                    </td>
                    <td className="py-3 pr-4">
                      <Badge tone="slate">{(row.language ?? "?").toUpperCase()}</Badge>
                    </td>
                    <td className="py-3 pr-4">
                      <Badge tone={domainTone(row.domain) as any}>
                        {row.domain ? row.domain.charAt(0).toUpperCase() + row.domain.slice(1) : "—"}
                      </Badge>
                    </td>
                    <td className="py-3 pr-4">
                      {row.answered === false ? (
                        <span className="inline-flex items-center gap-1 rounded-full bg-red-950/60 px-2 py-0.5 text-xs font-semibold text-red-400">
                          Couldn't answer due to lack of data
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 rounded-full bg-green-950/60 px-2 py-0.5 text-xs font-semibold text-green-400">
                          Answered
                        </span>
                      )}
                    </td>
                    <td className="py-3 pr-0 whitespace-nowrap">
                      {row.latency_ms ? `${row.latency_ms} ms` : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
