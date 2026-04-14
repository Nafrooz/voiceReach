export type ButtonVariant = "primary" | "secondary" | "danger";

const variants: Record<ButtonVariant, string> = {
  primary: "bg-emerald-600 hover:bg-emerald-500 text-slate-950",
  secondary: "bg-slate-800 hover:bg-slate-700 text-slate-100",
  danger: "bg-rose-600 hover:bg-rose-500 text-slate-950",
};

export default function Button({
  children,
  variant = "secondary",
  className = "",
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant;
}) {
  return (
    <button
      {...props}
      className={[
        "inline-flex items-center justify-center rounded-xl px-4 py-2 text-sm font-semibold transition disabled:opacity-50",
        variants[variant],
        className,
      ].join(" ")}
    >
      {children}
    </button>
  );
}

