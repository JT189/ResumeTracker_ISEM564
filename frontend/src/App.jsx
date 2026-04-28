import { Navigate, Route, Routes } from 'react-router-dom'

import { HomePage } from './pages/HomePage.jsx'
import { ConfigPage } from './pages/ConfigPage.jsx'
import { TrackerPage } from './pages/TrackerPage.jsx'
import { RolesPage } from './pages/RolesPage.jsx'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/tracker" element={<TrackerPage />} />
      <Route path="/roles" element={<RolesPage />} />
      <Route path="/config" element={<ConfigPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
