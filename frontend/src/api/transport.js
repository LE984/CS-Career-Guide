import { getToken, handleUnauthorized } from '../auth/session.js'

export function installAuthInterceptors(client) {
  client.interceptors.request.use(config => {
    config.authToken = config.publicAuth ? null : getToken()
    if (config.authToken) config.headers.set('Authorization', `Token ${config.authToken}`)
    else config.headers.delete('Authorization')
    return config
  })
  client.interceptors.response.use(
    response => response.data,
    error => {
      if (error.response?.status === 401 && !error.config?.publicAuth && error.config?.redirectOnUnauthorized !== false) {
        handleUnauthorized(error.config?.authToken)
      }
      return Promise.reject(error)
    },
  )
}

// Only business API endpoints use this helper. Third-party and media fetches
// keep using native fetch, so they never receive the user's API token.
export function createApiFetch(buildUrl) {
  return async (endpoint, options = {}) => {
    const token = getToken()
    const headers = new Headers(options.headers)
    if (token) headers.set('Authorization', `Token ${token}`)
    else headers.delete('Authorization')
    const response = await fetch(buildUrl(endpoint), { ...options, headers })
    if (response.status === 401) {
      handleUnauthorized(token)
      const error = new Error('请登录后继续操作')
      error.status = 401
      throw error
    }
    // Return the untouched Response, including its streaming body.
    return response
  }
}
