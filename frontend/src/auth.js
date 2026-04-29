export function getAuthToken() {
  return window.localStorage.getItem('rt_auth_token') || ''
}

export function setAuthToken(token) {
  if (!token) {
    window.localStorage.removeItem('rt_auth_token')
    window.dispatchEvent(new Event('rt-auth-changed'))
    return
  }
  window.localStorage.setItem('rt_auth_token', token)
  window.dispatchEvent(new Event('rt-auth-changed'))
}

export async function apiFetch(url, options = {}) {
  const token = getAuthToken()
  const headers = new Headers(options.headers || {})
  if (token) headers.set('Authorization', `Bearer ${token}`)
  return fetch(url, { ...options, headers })
}

