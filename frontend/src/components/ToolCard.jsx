import { Link } from 'react-router-dom'

export function ToolCard({ to, title, description, icon: Icon }) {
  return (
    <Link
      to={to}
      className="mb-4 flex w-full max-w-md items-start gap-6 rounded-2xl border border-slate-100 bg-white p-8 shadow-sm transition-all hover:shadow-md no-underline"
    >
      <Icon className="mt-0.5 h-8 w-8 shrink-0 text-slate-400" aria-hidden="true" />
      <div className="min-w-0 flex-1">
        <div className="text-lg font-bold text-neutral-900">{title}</div>
        <p className="mt-1 text-sm leading-relaxed text-slate-500">{description}</p>
      </div>
    </Link>
  )
}
