import { Link } from 'react-router-dom'

export function ToolPlaceholder({ title, description }) {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-white px-6 font-[Inter,ui-sans-serif,system-ui,sans-serif]">
      <h1 className="text-center text-xl font-bold text-neutral-900">{title}</h1>
      <p className="mt-3 max-w-md text-center text-sm leading-relaxed text-slate-500">{description}</p>
      <Link
        to="/"
        className="mt-10 rounded-2xl border border-slate-100 bg-white px-8 py-3 text-sm font-bold text-neutral-900 shadow-sm transition-all hover:shadow-md no-underline"
      >
        Back to home
      </Link>
    </div>
  )
}
