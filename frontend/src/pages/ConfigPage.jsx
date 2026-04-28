import { useEffect, useMemo, useRef, useState } from 'react'
import { LogOut, Plus, RotateCcw, Rss, ShieldCheck, Trash2, UploadCloud, User } from 'lucide-react'
import { Link } from 'react-router-dom'

export function ConfigPage() {
  const apiBaseUrl = useMemo(() => import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000', [])

  const [rules, setRules] = useState([
    { id: 1, name: 'Senior Technical Program Manager', attribute: 'title', operator: 'contains', value: '', weight: 30 },
  ])
  const [agenticMode, setAgenticMode] = useState(false)
  const [resumeFile, setResumeFile] = useState(null)
  const [profileSummary, setProfileSummary] = useState('')
  const [attributes, setAttributes] = useState([
    { value: 'title', label: 'Title' },
    { value: 'company', label: 'Company' },
    { value: 'description', label: 'Role requirement' },
  ])
  const [profileBalloon, setProfileBalloon] = useState({ open: false, mode: 'message', title: '', content: '' })
  const profileBalloonTimerRef = useRef(null)
  const [isUpdatingProfile, setIsUpdatingProfile] = useState(false)
  const lastProfileSnapshotRef = useRef('')
  const resumeInputRef = useRef(null)

  useEffect(() => {
    let isActive = true
    fetch(`${apiBaseUrl}/job_attributes`)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error('attributes fetch failed'))))
      .then((data) => {
        if (!isActive) return
        if (Array.isArray(data)) setAttributes(data)
      })
      .catch(() => {})
    return () => {
      isActive = false
    }
  }, [apiBaseUrl])

  useEffect(() => {
    const stored = window.localStorage.getItem('rt_profile_snapshot')
    if (stored) lastProfileSnapshotRef.current = stored
  }, [])

  useEffect(() => {
    return () => {
      if (profileBalloonTimerRef.current) window.clearTimeout(profileBalloonTimerRef.current)
    }
  }, [])

  function closeProfileBalloonSoon(delayMs) {
    if (profileBalloonTimerRef.current) window.clearTimeout(profileBalloonTimerRef.current)
    profileBalloonTimerRef.current = window.setTimeout(() => {
      setProfileBalloon((b) => ({ ...b, open: false }))
    }, delayMs)
  }

  function showProfileBalloon(next) {
    if (profileBalloonTimerRef.current) window.clearTimeout(profileBalloonTimerRef.current)
    setProfileBalloon({ ...next, open: true })
  }

  function getStoredUserId() {
    const stored = window.localStorage.getItem('rt_user_id')
    if (stored) {
      const n = Number(stored)
      if (!Number.isNaN(n) && Number.isFinite(n)) return n
      window.localStorage.removeItem('rt_user_id')
    }
    return null
  }

  async function handleUpdateProfile() {
    if (isUpdatingProfile) return

    if (!resumeFile || !(resumeFile instanceof File) || !resumeFile.name || resumeFile.size <= 0) {
      showProfileBalloon({ mode: 'message', title: 'Resume required', content: 'Please upload resume.' })
      closeProfileBalloonSoon(2400)
      return
    }

    const snapshot = JSON.stringify({
      name: resumeFile.name,
      size: resumeFile.size,
      type: resumeFile.type,
      lastModified: resumeFile.lastModified,
    })
    if (lastProfileSnapshotRef.current && snapshot === lastProfileSnapshotRef.current) {
      showProfileBalloon({ mode: 'message', title: 'No change', content: 'Your profile is already up to date.' })
      closeProfileBalloonSoon(2200)
      return
    }

    setIsUpdatingProfile(true)
    showProfileBalloon({ mode: 'message', title: 'Updating profile', content: 'Please wait while we save your data.' })

    let timeoutId = null
    try {
      const fd = new FormData()
      fd.append('file', resumeFile)

      const controller = new AbortController()
      timeoutId = window.setTimeout(() => controller.abort(), 60000)

      const res = await fetch(`${apiBaseUrl}/profile_from_resume`, { method: 'POST', body: fd, signal: controller.signal })

      if (!res.ok) throw new Error('profile update failed')
      const data = await res.json()
      const summary = String(data.profile_summary || '')
      setProfileSummary(summary)

      if (data && data.user_id) window.localStorage.setItem('rt_user_id', String(data.user_id))

      lastProfileSnapshotRef.current = snapshot
      window.localStorage.setItem('rt_profile_snapshot', snapshot)

      showProfileBalloon({ mode: 'message', title: 'Profile updated', content: 'Your profile is saved.' })
      closeProfileBalloonSoon(900)

      setResumeFile(null)
      if (resumeInputRef.current) resumeInputRef.current.value = ''
    } catch (err) {
      const msg = String(err && err.message ? err.message : err || '')
      if (err && err.name === 'AbortError') {
        showProfileBalloon({
          mode: 'message',
          title: 'Update timed out',
          content: 'The upload is taking too long. Please try again.',
        })
        closeProfileBalloonSoon(2600)
        return
      }
      showProfileBalloon({
        mode: 'message',
        title: 'Update failed',
        content: msg ? 'Start the backend server and try again.' : 'Start the backend server and try again.',
      })
      closeProfileBalloonSoon(2600)
    } finally {
      if (timeoutId) window.clearTimeout(timeoutId)
      setIsUpdatingProfile(false)
    }
  }

  async function handleViewProfile() {
    try {
      const userId = getStoredUserId()
      if (!userId) {
        showProfileBalloon({
          mode: 'message',
          title: 'No profile loaded',
          content: 'Use Update Profile to upload a resume.',
        })
        closeProfileBalloonSoon(2400)
        return
      }
      const res = await fetch(`${apiBaseUrl}/users/${userId}/profile`)
      if (!res.ok) {
        showProfileBalloon({
          mode: 'message',
          title: 'No profile loaded',
          content: 'Use Update Profile to save your data.',
        })
        closeProfileBalloonSoon(2400)
        return
      }
      const data = await res.json()
      const summary = String(data.profile_summary || '')
      setProfileSummary(summary)
      showProfileBalloon({ mode: 'data', title: 'Profile loaded', content: summary || 'No profile data' })
    } catch (err) {
      showProfileBalloon({
        mode: 'message',
        title: 'View failed',
        content: 'Start the backend server and try again.',
      })
      closeProfileBalloonSoon(2600)
    }
  }

  async function handleSaveRules() {
    const userId = getStoredUserId()
    if (!userId) {
      showProfileBalloon({ mode: 'message', title: 'Profile required', content: 'Upload a resume before saving rules.' })
      closeProfileBalloonSoon(2400)
      return
    }
    const payload = {
      user_id: userId,
      rules: rules.map((r) => ({
        user_id: userId,
        name: r.name || 'Rule',
        attribute: r.attribute || 'title',
        condition: r.operator || 'contains',
        match_value: r.value || '',
        weight: Number(r.weight) || 0,
        is_active: true,
      })),
    }

    const res = await fetch(`${apiBaseUrl}/ranking_rules/replace`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    if (!res.ok) throw new Error('rules save failed')
  }

  function ProfileBalloon() {
    if (!profileBalloon.open) return null

    const isData = profileBalloon.mode === 'data'
    return (
      <div
        className="absolute right-0 top-full mt-3 w-[min(520px,calc(100vw-48px))] origin-top-right"
        style={{
          animation: 'rtInflate 350ms ease-out',
        }}
      >
        <style>{`
@keyframes rtInflate {
  0% { transform: scale(0.92); opacity: 0; }
  100% { transform: scale(1); opacity: 1; }
}
        `}</style>
        <div className="bg-white border border-gray-200 rounded-2xl shadow-subtle overflow-hidden">
          <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between gap-3">
            <div className="text-sm font-semibold text-charcoal-dark">{profileBalloon.title}</div>
            <button
              type="button"
              onClick={() => setProfileBalloon((b) => ({ ...b, open: false }))}
              className="text-xs text-gray-400 hover:text-charcoal transition-colors"
            >
              Close
            </button>
          </div>
          <div className={isData ? 'p-0' : 'px-5 py-4'}>
            {isData ? (
              <div className="max-h-[360px] overflow-auto">
                <pre className="whitespace-pre-wrap text-sm text-charcoal-dark px-5 py-4">{profileBalloon.content}</pre>
              </div>
            ) : (
              <div className="text-sm text-gray-600 leading-6">{profileBalloon.content}</div>
            )}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-[#FDFDFD] font-sans text-charcoal">
      <nav className="bg-white/80 backdrop-blur-md border-b border-gray-100 px-8 py-4 flex items-center justify-between sticky top-0 z-50 transition-all">
        <div className="flex items-center space-x-12">
          <Link to="/" className="text-lg font-bold text-charcoal-dark tracking-tight flex items-center">
            <div className="w-8 h-8 bg-charcoal text-white rounded-lg flex items-center justify-center mr-3 font-serif italic">
              R
            </div>
            Tracker Pro
          </Link>
          <div className="hidden md:flex space-x-8 text-sm font-medium">
            <Link to="/tracker" className="text-gray-400 hover:text-charcoal transition-colors py-1">
              Tracker
            </Link>
            <Link to="/roles" className="text-gray-400 hover:text-charcoal transition-colors py-1">
              Roles
            </Link>
            <Link to="/config" className="text-charcoal border-b-2 border-charcoal py-1">
              Config
            </Link>
          </div>
        </div>
        <div className="w-8 h-8 rounded-full bg-gray-100 border border-gray-200 flex items-center justify-center text-sm font-semibold text-gray-500">
          JD
        </div>
      </nav>

      <main className="max-w-3xl mx-auto py-12 px-6 space-y-10">
        <header className="mb-10">
          <h1 className="text-3xl font-bold text-charcoal-dark tracking-tight mb-2">Configuration</h1>
          <p className="text-gray-500">Manage your profile, adjust ranking weights, and configure feed sources.</p>
        </header>

        <section className="bg-white border border-gray-100 rounded-2xl shadow-subtle overflow-hidden">
          <div className="px-8 py-5 border-b border-gray-50 flex items-center">
            <div className="p-2 bg-gray-50 rounded-lg mr-3">
              <User className="w-5 h-5 text-charcoal-light" />
            </div>
            <h2 className="font-semibold text-charcoal-dark text-lg">User Profile</h2>
          </div>
          <div className="p-8 space-y-8">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div className="space-y-2 md:col-span-2">
                <div className="text-sm text-gray-500">
                  Upload your resume and we will extract your profile details.
                </div>
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-xs font-semibold uppercase tracking-wider text-gray-400">Resume Upload</label>
              <label
                onDragOver={(e) => e.preventDefault()}
                onDrop={(e) => {
                  e.preventDefault()
                  const file = e.dataTransfer.files[0]
                  if (file && (file.type === 'application/pdf' || file.name.endsWith('.docx'))) setResumeFile(file)
                }}
                className="group flex flex-col items-center justify-center w-full border-2 border-dashed border-gray-200 rounded-xl p-8 hover:border-charcoal hover:bg-gray-50 transition-all cursor-pointer"
              >
                <input
                  type="file"
                  accept=".pdf,.docx"
                  className="hidden"
                  ref={resumeInputRef}
                  onChange={(e) => {
                    if (e.target.files[0]) setResumeFile(e.target.files[0])
                  }}
                />
                {resumeFile ? (
                  <>
                    <UploadCloud className="w-8 h-8 text-charcoal mb-3" />
                    <p className="text-sm font-medium text-charcoal-dark mb-1">{resumeFile.name}</p>
                    <p className="text-xs text-gray-400">{(resumeFile.size / 1024).toFixed(1)} KB</p>
                  </>
                ) : (
                  <>
                    <UploadCloud className="w-8 h-8 text-gray-400 group-hover:text-charcoal mb-3 transition-colors" />
                    <p className="text-sm font-medium text-charcoal-dark mb-1">Click to upload or drag and drop</p>
                    <p className="text-xs text-gray-400">PDF, DOCX up to 5MB</p>
                  </>
                )}
              </label>
            </div>

            <div className="flex flex-wrap gap-3 relative">
              <button
                type="button"
                onClick={() => handleUpdateProfile()}
                disabled={isUpdatingProfile}
                className={`bg-charcoal text-white px-6 py-2.5 rounded-lg text-sm font-medium transition-colors shadow-sm ${
                  isUpdatingProfile ? 'opacity-60 cursor-not-allowed' : 'hover:bg-black'
                }`}
              >
                Update Profile
              </button>
              <button
                type="button"
                onClick={() => handleViewProfile()}
                className="bg-white text-charcoal px-6 py-2.5 rounded-lg text-sm font-medium border border-gray-200 hover:bg-gray-50 transition-colors"
              >
                View Profile
              </button>
              <ProfileBalloon />
            </div>

            <div className="space-y-2">
              <label className="text-xs font-semibold uppercase tracking-wider text-gray-400">Personal Bio</label>
              <textarea
                className="w-full bg-gray-50/50 border border-gray-200 rounded-lg px-4 py-3 text-sm focus:bg-white focus:ring-2 focus:ring-gray-200 focus:border-gray-400 outline-none resize-none transition-all h-28"
                placeholder="Tell us about your career goals..."
              />
            </div>
          </div>
        </section>

        <section className="bg-white border border-gray-100 rounded-2xl shadow-subtle overflow-hidden">
          <div className="px-8 py-5 border-b border-gray-50 flex items-center justify-between">
            <div className="flex items-center">
              <div className="p-2 bg-gray-50 rounded-lg mr-3">
                <ShieldCheck className="w-5 h-5 text-charcoal-light" />
              </div>
              <h2 className="font-semibold text-charcoal-dark text-lg">Ranking Rules</h2>
            </div>

            <div className="flex items-center space-x-3 bg-gray-50 px-4 py-2 rounded-lg border border-gray-100">
              <span className="text-xs text-charcoal-light font-medium uppercase tracking-wide">Agentic Scoring</span>
              <button
                onClick={() => setAgenticMode(!agenticMode)}
                className={`w-11 h-6 rounded-full relative transition-colors duration-300 focus:outline-none ${
                  agenticMode ? 'bg-charcoal' : 'bg-gray-200'
                }`}
              >
                <div
                  className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-transform duration-300 shadow-sm ${
                    agenticMode ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>
          </div>

          <div className="p-8">
            <div className="overflow-x-auto rounded-lg border border-gray-100">
              <table className="w-full text-sm">
                <thead className="bg-gray-50/50">
                  <tr className="text-left text-gray-500 text-xs uppercase tracking-wider">
                    <th className="px-4 py-3 font-semibold">Rule Name</th>
                    <th className="px-4 py-3 font-semibold">Attribute</th>
                    <th className="px-4 py-3 font-semibold">Condition</th>
                    <th className="px-4 py-3 font-semibold">Value</th>
                    <th className="px-4 py-3 font-semibold">Weight</th>
                    <th className="px-4 py-3" />
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 bg-white">
                  {rules.map((rule) => (
                    <tr key={rule.id} className="hover:bg-gray-50/30 transition-colors group">
                      <td className="px-4 py-3 font-medium text-charcoal-dark">
                        <input
                          type="text"
                          value={rule.name}
                          onChange={(e) =>
                            setRules(rules.map((r) => (r.id === rule.id ? { ...r, name: e.target.value } : r)))
                          }
                          className="w-full bg-transparent outline-none focus:bg-gray-50 focus:border-charcoal rounded px-1 py-0.5 transition-colors"
                          placeholder="Rule name..."
                        />
                      </td>
                      <td className="px-4 py-3">
                        <select
                          className="bg-gray-50 border border-gray-200 rounded px-2 py-1.5 text-sm text-gray-600 outline-none focus:border-charcoal"
                          value={rule.attribute}
                          onChange={(e) =>
                            setRules(
                              rules.map((r) => (r.id === rule.id ? { ...r, attribute: e.target.value } : r)),
                            )
                          }
                        >
                          {attributes.map((a) => (
                            <option key={a.value} value={a.value}>
                              {a.label}
                            </option>
                          ))}
                        </select>
                      </td>
                      <td className="px-4 py-3">
                        <select
                          className="bg-gray-50 border border-gray-200 rounded px-2 py-1.5 text-sm text-gray-600 outline-none focus:border-charcoal"
                          value={rule.operator}
                          onChange={(e) =>
                            setRules(rules.map((r) => (r.id === rule.id ? { ...r, operator: e.target.value } : r)))
                          }
                        >
                          <option value="contains">contains</option>
                          <option value="excludes">excludes</option>
                        </select>
                      </td>
                      <td className="px-4 py-3">
                        <input
                          type="text"
                          value={rule.value}
                          onChange={(e) =>
                            setRules(rules.map((r) => (r.id === rule.id ? { ...r, value: e.target.value } : r)))
                          }
                          className="w-24 bg-gray-50 border border-gray-200 rounded px-3 py-1.5 text-sm outline-none focus:border-charcoal focus:bg-white transition-colors"
                          placeholder="..."
                        />
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center">
                          <span className="text-green-600 font-medium mr-1">+</span>
                          <input
                            type="number"
                            value={rule.weight}
                            min={0}
                            max={100}
                            onChange={(e) => {
                              const val = Math.max(0, Math.min(100, Number(e.target.value) || 0))
                              setRules(rules.map((r) => (r.id === rule.id ? { ...r, weight: val } : r)))
                            }}
                            className="w-16 bg-gray-50 border border-gray-200 rounded px-3 py-1.5 text-sm outline-none focus:border-charcoal focus:bg-white transition-colors"
                          />
                        </div>
                      </td>
                      <td className="px-4 py-3 text-right">
                        <button
                          onClick={() => setRules(rules.filter((r) => r.id !== rule.id))}
                          className="text-gray-300 hover:text-red-500 transition-colors opacity-0 group-hover:opacity-100 p-1"
                          aria-label="Delete rule"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {(() => {
              const total = rules.reduce((sum, r) => sum + r.weight, 0)
              const isValid = total === 100
              return (
                <div className="mt-4 space-y-2">
                  <div className="flex items-center justify-between text-xs font-medium">
                    <span className={isValid ? 'text-green-600' : 'text-red-500'}>Total weight: {total} / 100</span>
                    {!isValid && (
                      <span className="text-red-500">
                        {total < 100 ? `${100 - total} remaining` : `${total - 100} over limit`}
                      </span>
                    )}
                  </div>
                  <div className="h-2 w-full bg-gray-100 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-300 ${
                        total === 100 ? 'bg-green-500' : total > 100 ? 'bg-red-500' : 'bg-amber-400'
                      }`}
                      style={{ width: `${Math.min(total, 100)}%` }}
                    />
                  </div>
                </div>
              )
            })()}

            <button
              onClick={() =>
                setRules([
                  ...rules,
                  { id: Date.now(), name: '', attribute: 'title', operator: 'contains', value: '', weight: 0 },
                ])
              }
              className="mt-5 flex items-center text-xs font-bold text-charcoal hover:text-black uppercase tracking-widest transition-colors py-2 px-4 rounded-lg hover:bg-gray-50"
            >
              <Plus className="w-4 h-4 mr-2" /> Add New Rule
            </button>

            <button
              onClick={() => handleSaveRules().catch(() => {})}
              className="mt-3 bg-charcoal text-white px-6 py-2.5 rounded-lg text-sm font-medium hover:bg-black transition-colors shadow-sm"
            >
              Save Rules
            </button>
          </div>
        </section>

        <section className="bg-white border border-gray-100 rounded-2xl shadow-subtle overflow-hidden">
          <div className="px-8 py-5 border-b border-gray-50 flex items-center">
            <div className="p-2 bg-gray-50 rounded-lg mr-3">
              <Rss className="w-5 h-5 text-charcoal-light" />
            </div>
            <h2 className="font-semibold text-charcoal-dark text-lg">RSS Sources</h2>
          </div>
          <div className="p-8 space-y-6">
            <div className="flex space-x-3">
              <input
                type="text"
                className="flex-1 bg-gray-50/50 border border-gray-200 rounded-lg px-4 py-2.5 text-sm focus:bg-white focus:ring-2 focus:ring-gray-200 focus:border-gray-400 outline-none transition-all"
                placeholder="Enter feed URL (for example https://example.com/feed.xml)"
              />
              <button className="bg-charcoal text-white px-6 py-2.5 rounded-lg text-sm font-medium hover:bg-black transition-colors shadow-sm">
                Add Feed
              </button>
            </div>

            <div className="border border-gray-100 rounded-xl divide-y divide-gray-50 overflow-hidden">
              <div className="p-4 text-sm text-gray-600 flex justify-between items-center hover:bg-gray-50 transition-colors">
                <span className="truncate pr-4 font-medium">https://news.ycombinator.com/rss</span>
                <button className="text-gray-300 hover:text-red-500 transition-colors" aria-label="Delete RSS source">
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
              <div className="p-4 text-sm text-gray-600 flex justify-between items-center hover:bg-gray-50 transition-colors">
                <span className="truncate pr-4 font-medium">https://www.linkedin.com/jobs/rss/</span>
                <button className="text-gray-300 hover:text-red-500 transition-colors" aria-label="Delete RSS source">
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
              <div className="p-4 text-sm text-gray-600 flex justify-between items-center hover:bg-gray-50 transition-colors">
                <span className="truncate pr-4 font-medium">https://indeed.com/rss/tech-jobs</span>
                <button className="text-gray-300 hover:text-red-500 transition-colors" aria-label="Delete RSS source">
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        </section>

        <footer className="flex justify-between pt-8 pb-12 border-t border-gray-100">
          <button className="flex items-center text-sm text-gray-400 hover:text-charcoal transition-colors font-medium px-4 py-2 rounded-lg hover:bg-gray-50">
            <RotateCcw className="w-4 h-4 mr-2" /> Reset Defaults
          </button>
          <button className="flex items-center text-sm text-gray-400 hover:text-red-600 transition-colors font-medium px-4 py-2 rounded-lg hover:bg-red-50">
            <LogOut className="w-4 h-4 mr-2" /> Sign Out
          </button>
        </footer>
      </main>
    </div>
  )
}

