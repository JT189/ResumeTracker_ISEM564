import { Link } from 'react-router-dom'

export function RolesPage() {
  return (
    <div className="min-h-screen bg-white text-black">
      <div className="mx-auto w-full max-w-6xl px-6 py-10">
        <header className="flex items-center justify-between">
          <div className="text-2xl font-semibold tracking-tight">Daily Role Feed</div>
          <Link
            to="/"
            className="rounded-full border border-black/10 px-4 py-2 text-sm font-medium text-black/80 hover:border-black/20"
          >
            Back to dashboard
          </Link>
        </header>

        <main className="mt-10">
          <div className="rounded-2xl border border-black/10 p-6">
            <div className="text-sm font-medium text-black/70">Placeholder</div>
            <div className="mt-2 text-base leading-7 text-black/60">
              This page will show incoming roles from your RSS sources with rank scores.
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}

