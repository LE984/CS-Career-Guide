import { clearSession, getToken, isPublicPath } from '../auth/session.js'

export function createAuthGuard(validateSession) {
  return async to => {
    if (isPublicPath(to.path)) return true
    const login = { path: '/login', query: { redirect: to.fullPath } }
    const token = getToken()
    if (!token) return login
    try {
      await validateSession()
      return getToken() === token ? true : login
    } catch (error) {
      if (error.response?.status === 401 && getToken() === token) clearSession()
      // Fail closed on network/server errors too; retain the token for retry.
      return login
    }
  }
}
