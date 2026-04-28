import { Navigate, Route, Routes } from 'react-router-dom'

import { Home } from './components/Home.jsx'
import { ToolPlaceholder } from './components/ToolPlaceholder.jsx'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route
        path="/tracker"
        element={
          <ToolPlaceholder
            title="Job Tracker"
            description="This area will hold your pipeline, filters, and saved roles."
          />
        }
      />
      <Route
        path="/roles"
        element={
          <ToolPlaceholder
            title="Daily Role Feed"
            description="This area will stream new roles from RSS with scores you can trust."
          />
        }
      />
      <Route
        path="/config"
        element={
          <ToolPlaceholder
            title="Settings"
            description="This area will host sources, ranking rules, and account options."
          />
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
