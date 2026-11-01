import axios from 'axios'
import { API_BASE_URL, COMPANY_API_BASE_URL, API_TIMEOUT, COMPANY_API_TIMEOUT, apiUrl } from '../config'
import { createApiFetch, installAuthInterceptors } from './transport.js'

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: API_TIMEOUT,
  headers: { 'Content-Type': 'application/json' }
})

export const dbApi = axios.create({
  baseURL: COMPANY_API_BASE_URL,
  timeout: COMPANY_API_TIMEOUT,
  headers: { 'Content-Type': 'application/json' }
})

installAuthInterceptors(api)
installAuthInterceptors(dbApi)

// Streaming requests use fetch so callers can consume the response body.
export const apiFetch = createApiFetch(apiUrl)

export default api
