// VITE_* variables are public and are embedded when the frontend is built.
function positiveInteger(value, fallback, name) {
  const result = Number(value || fallback)
  if (!Number.isInteger(result) || result < 1) throw new Error(`${name} must be a positive integer`)
  return result
}

export const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/+$/, '')
export const COMPANY_API_BASE_URL = (import.meta.env.VITE_COMPANY_API_BASE_URL || API_BASE_URL).replace(/\/+$/, '')
export const VAD_ASSET_BASE_URL = `${(import.meta.env.VITE_VAD_ASSET_BASE_URL || `${import.meta.env.BASE_URL}models/vad/`).replace(/\/+$/, '')}/`
export const AVATAR_MODEL_URL = import.meta.env.VITE_AVATAR_MODEL_URL || `${import.meta.env.BASE_URL}models/d51675667acfc8a42b8e40d4c3e9799a.glb`
export const GEOCODING_URL = import.meta.env.VITE_GEOCODING_URL || ''
export const IP_GEOLOCATION_URL = import.meta.env.VITE_IP_GEOLOCATION_URL || ''
export const ENABLE_TTS = /^(true|1|yes|on)$/i.test(import.meta.env.VITE_ENABLE_TTS || 'false')
export const API_TIMEOUT = positiveInteger(import.meta.env.VITE_API_TIMEOUT_MS, 120000, 'VITE_API_TIMEOUT_MS')
export const COMPANY_API_TIMEOUT = positiveInteger(import.meta.env.VITE_COMPANY_API_TIMEOUT_MS, 30000, 'VITE_COMPANY_API_TIMEOUT_MS')

export function apiUrl(endpoint) {
  return `${API_BASE_URL}/${endpoint.replace(/^\/+/, '')}`
}
