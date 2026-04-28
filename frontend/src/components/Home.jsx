import { Briefcase, Rss, Settings } from 'lucide-react'

import { ToolCard } from './ToolCard.jsx'

export function Home() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-white px-6 font-[Inter,ui-sans-serif,system-ui,sans-serif]">
      <p className="mb-10 text-xs font-bold uppercase tracking-[0.35em] text-neutral-900">
        RESUME TRACKER PRO
      </p>
      <div className="flex w-full max-w-md flex-col items-center">
        <ToolCard
          to="/tracker"
          title="Job Tracker"
          description="Save roles, statuses, and notes in one calm view."
          icon={Briefcase}
        />
        <ToolCard
          to="/roles"
          title="Daily Role Feed"
          description="Scan fresh listings from your feeds with ranking applied."
          icon={Rss}
        />
        <ToolCard
          to="/config"
          title="Settings"
          description="Tune sources, ranking rules, and profile details."
          icon={Settings}
        />
      </div>
    </div>
  )
}
