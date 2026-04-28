import { LayoutDashboard, Newspaper, Settings } from 'lucide-react'
import { Link } from 'react-router-dom'

function Tile({ to, title, subtitle, icon: Icon }) {
  return (
    <Link
      to={to}
      className="group rounded-2xl border border-black/10 bg-white p-6 transition-colors hover:border-black/20 focus:outline-none focus:ring-2 focus:ring-black/20"
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="text-lg font-semibold tracking-tight text-black">{title}</div>
          <div className="mt-1 text-sm leading-6 text-black/60">{subtitle}</div>
        </div>
        <div className="rounded-xl border border-black/10 p-3 transition-colors group-hover:border-black/20">
          <Icon className="h-6 w-6 text-black" aria-hidden="true" />
        </div>
      </div>
    </Link>
  )
}

export function HomePage() {
  return (
    <div className="min-h-screen bg-white text-black">
      <div className="mx-auto w-full max-w-6xl px-6 py-10">
        <header className="flex items-center justify-between">
          <div className="text-2xl font-semibold tracking-tight">Resume Tracker Pro</div>
        </header>

        <main className="mt-10">
          <div className="max-w-2xl">
            <h1 className="text-4xl font-semibold tracking-tight">Your job search, organized</h1>
            <p className="mt-3 text-base leading-7 text-black/65">
              Track roles, review daily feed items, and tune ranking rules in one place.
            </p>
          </div>

          <section className="mt-10 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
            <Tile
              to="/tracker"
              title="Job Tracker"
              subtitle="Statuses, notes, and progress at a glance"
              icon={LayoutDashboard}
            />
            <Tile
              to="/roles"
              title="Daily Role Feed"
              subtitle="Fresh roles from RSS sources with ranking"
              icon={Newspaper}
            />
            <Tile
              to="/config"
              title="Settings and Config"
              subtitle="Sources, rules, and preferences"
              icon={Settings}
            />
          </section>
        </main>
      </div>
    </div>
  )
}

