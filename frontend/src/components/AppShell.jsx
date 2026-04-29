import { Link, useLocation } from 'react-router-dom'

import { ProfileMenu } from './ProfileMenu.jsx'

function NavLink({ to, label }) {
  const location = useLocation()
  const active = location.pathname === to
  return (
    <Link
      to={to}
      className={
        active
          ? 'text-charcoal border-b-2 border-charcoal py-1'
          : 'text-gray-400 hover:text-charcoal transition-colors py-1'
      }
    >
      {label}
    </Link>
  )
}

export function AppShell({ children }) {
  return (
    <div className="min-h-screen bg-[#FDFDFD] font-sans text-charcoal">
      <nav className="bg-white/80 backdrop-blur-md border-b border-gray-100 px-8 py-4 flex items-center justify-between sticky top-0 z-50 transition-all">
        <div className="flex items-center space-x-12">
          <Link to="/" className="text-lg font-bold text-charcoal-dark tracking-tight flex items-center">
            <div className="w-8 h-8 bg-charcoal text-white rounded-lg flex items-center justify-center mr-3 font-serif italic">
              M
            </div>
            My Job Tracker
          </Link>
          <div className="hidden md:flex space-x-8 text-sm font-medium">
            <NavLink to="/tracker" label="Tracker" />
            <NavLink to="/roles" label="Roles" />
            <NavLink to="/config" label="Config" />
            <NavLink to="/analytics" label="Analytics" />
          </div>
        </div>
        <ProfileMenu />
      </nav>

      {children}
    </div>
  )
}

