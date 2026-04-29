import { Navigate, Route, Routes } from 'react-router-dom'

import { HomePage } from './pages/HomePage.jsx'
import { ConfigPage } from './pages/ConfigPage.jsx'
import { TrackerPage } from './pages/TrackerPage.jsx'
import { RolesPage } from './pages/RolesPage.jsx'
import { AnalyticsPage } from './pages/AnalyticsPage.jsx'
import { LoginPage } from './pages/LoginPage.jsx'
import { ForgotPasswordPage } from './pages/ForgotPasswordPage.jsx'
import { ResetPasswordPage } from './pages/ResetPasswordPage.jsx'
import { getAuthToken } from './auth.js'
import { AppShell } from './components/AppShell.jsx'

function RequireAuth({ children }) {
  const token = getAuthToken()
  if (!token) return <Navigate to="/login" replace />
  return <AppShell>{children}</AppShell>
}

export default function App() {
  return (
    <Routes>
      <Route
        path="/"
        element={
          getAuthToken() ? (
            <AppShell>
              <HomePage />
            </AppShell>
          ) : (
            <Navigate to="/login" replace />
          )
        }
      />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/forgot" element={<ForgotPasswordPage />} />
      <Route path="/reset" element={<ResetPasswordPage />} />
      <Route
        path="/tracker"
        element={
          <RequireAuth>
            <TrackerPage />
          </RequireAuth>
        }
      />
      <Route
        path="/roles"
        element={
          <RequireAuth>
            <RolesPage />
          </RequireAuth>
        }
      />
      <Route
        path="/config"
        element={
          <RequireAuth>
            <ConfigPage />
          </RequireAuth>
        }
      />
      <Route
        path="/analytics"
        element={
          <RequireAuth>
            <AnalyticsPage />
          </RequireAuth>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
