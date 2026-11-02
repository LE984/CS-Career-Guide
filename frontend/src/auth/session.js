const publicPaths = new Set(['/login', '/register'])

export const getToken = () => localStorage.getItem('token')
export const isPublicPath = path => publicPaths.has(path.replace(/\/+$/, '').toLowerCase())

export function clearSession() {
  for (const key of [
    'token', 'user', 'selfIntroduction', 'careerAnalysis', 'careerRecommendations',
    'careerRecommendationRaw', 'careerRecommendationSessionId', 'selectedCareers',
    'careerReport', 'aiResponse', 'resume',
  ]) localStorage.removeItem(key)
}

// Redirects are router paths only; reject external, encoded and backslash variants.
export function safeRedirect(value) {
  if (typeof value !== 'string' || !value.startsWith('/') || value.startsWith('//')) return '/'
  try {
    const path = decodeURIComponent(value.split(/[?#]/)[0])
    if (path.startsWith('//') || /[\\\u0000-\u0020]/.test(path) || /[\\\u0000-\u001f]/.test(value)) return '/'
    if (isPublicPath(new URL(path, 'https://internal.invalid').pathname)) return '/'
    const url = new URL(value, 'https://internal.invalid')
    if (url.origin !== 'https://internal.invalid' || isPublicPath(url.pathname)) return '/'
    return `${url.pathname}${url.search}${url.hash}`
  } catch {
    return '/'
  }
}

export function handleUnauthorized(sentToken) {
  // An older in-flight request must not sign out a newly logged-in account.
  if (getToken() !== sentToken) return
  clearSession()
  const { pathname, search, hash } = window.location
  if (!isPublicPath(pathname)) {
    const redirect = safeRedirect(`${pathname}${search}${hash}`)
    window.location.replace(`/login?redirect=${encodeURIComponent(redirect)}`)
  }
}
