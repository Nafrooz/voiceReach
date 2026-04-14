import Badge from "../components/ui/Badge";
import Card from "../components/ui/Card";

type RecentQuery = {
  timestamp: string;
  query: string;
  language: string;
  domain: "healthcare" | "government" | "finance" | "education" | "general";
  latencyMs: number;
};

const mock = {
  totalQueriesToday: 42,
  avgResponseTimeMs: 1280,
  languagesDetected: 4,
  domainsServed: 4,
  recent: [
    {
      timestamp: "2026-04-14 10:12:03",
      query: "PM-JAY eligibility kaise check karein?",
      language: "hi",
      domain: "healthcare",
      latencyMs: 1540,
    },
    {
      timestamp: "2026-04-14 10:20:41",
      query: "PM Kisan ka paisa kyun ruk gaya?",
      language: "hi",
      domain: "government",
      latencyMs: 1190,
    },
    {
      timestamp: "2026-04-14 11:02:18",
      query: "UPI PIN share karna safe hai?",
      language: "en",
      domain: "finance",
      latencyMs: 980,
    },
    {
      timestamp: "2026-04-14 11:35:55",
      query: "National Scholarship Portal par apply kaise karu?",
      language: "hi",
      domain: "education",
      latencyMs: 1320,
    },
  ] satisfies RecentQuery[],
};

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

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Total Queries Today" value={`${mock.totalQueriesToday}`} />
        <StatCard label="Avg Response Time" value={`${mock.avgResponseTimeMs} ms`} />
        <StatCard label="Languages Detected" value={`${mock.languagesDetected}`} />
        <StatCard label="Domains Served" value={`${mock.domainsServed}`} />
      </div>

      <Card className="p-4">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-base font-semibold text-white">Recent queries</div>
            <div className="text-sm text-slate-400">
              Mock data for now — wire to <span className="font-mono">GET /api/v1/sessions/all</span>{" "}
              later.
            </div>
          </div>
        </div>

        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="text-slate-300">
              <tr className="border-b border-slate-800">
                <th className="py-2 pr-4 font-semibold">timestamp</th>
                <th className="py-2 pr-4 font-semibold">query preview</th>
                <th className="py-2 pr-4 font-semibold">language</th>
                <th className="py-2 pr-4 font-semibold">domain</th>
                <th className="py-2 pr-0 font-semibold">latency</th>
              </tr>
            </thead>
            <tbody className="text-slate-200">
              {mock.recent.map((row) => (
                <tr key={`${row.timestamp}-${row.query}`} className="border-b border-slate-900">
                  <td className="py-3 pr-4 whitespace-nowrap text-slate-400">{row.timestamp}</td>
                  <td className="py-3 pr-4">
                    <div className="max-w-[42rem] truncate">{row.query}</div>
                  </td>
                  <td className="py-3 pr-4">
                    <Badge tone="slate">{row.language.toUpperCase()}</Badge>
                  </td>
                  <td className="py-3 pr-4">
                    <Badge tone={domainTone(row.domain) as any}>
                      {row.domain.charAt(0).toUpperCase() + row.domain.slice(1)}
                    </Badge>
                  </td>
                  <td className="py-3 pr-0 whitespace-nowrap">{row.latencyMs} ms</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
