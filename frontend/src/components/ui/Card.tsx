export default function Card({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={["rounded-2xl border border-slate-800 bg-slate-950/40", className].join(" ")}>
      {children}
    </div>
  );
}

