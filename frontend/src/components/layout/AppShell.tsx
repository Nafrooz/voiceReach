import { NavLink } from "react-router-dom";
import Badge from "../ui/Badge";

function NavItem({ to, label }: { to: string; label: string }) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        [
          "rounded-lg px-3 py-2 text-sm font-medium transition",
          isActive ? "bg-slate-800 text-white" : "text-slate-300 hover:bg-slate-800/60",
        ].join(" ")
      }
    >
      {label}
    </NavLink>
  );
}

export default function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-full bg-slate-900 text-slate-100">
      <header className="border-b border-slate-800 bg-slate-950/50 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4">
          <div className="flex items-center gap-3">
            <div className="text-lg font-semibold">VoiceReach Admin</div>
            <Badge tone="green">LIVE</Badge>
          </div>
          <nav className="flex items-center gap-2">
            <NavItem to="/dashboard" label="Dashboard" />
            <NavItem to="/knowledge-base" label="Knowledge Base" />
            <NavItem to="/demo" label="Demo" />
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-8">{children}</main>
    </div>
  );
}

