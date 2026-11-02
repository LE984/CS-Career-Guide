import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig(({ mode }) => {
  // DEV_* values configure the dev server only; Vite exposes only VITE_* to browsers.
  const env = loadEnv(mode, process.cwd(), '')
  const port = Number(env.DEV_PORT || 3002)
  if (!Number.isInteger(port) || port < 1 || port > 65535) {
    throw new Error('DEV_PORT must be an integer between 1 and 65535')
  }
  const proxy = {}
  const apiBase = (env.VITE_API_BASE_URL || '/api').replace(/\/+$/, '')
  const companyBase = (env.VITE_COMPANY_API_BASE_URL || apiBase).replace(/\/+$/, '')
  if (env.DEV_API_PROXY_TARGET && apiBase.startsWith('/')) {
    proxy[apiBase] = { target: env.DEV_API_PROXY_TARGET, changeOrigin: true }
  }
  if (env.DEV_COMPANY_API_PROXY_TARGET && companyBase.startsWith('/')) {
    if (companyBase === apiBase) {
      throw new Error('Use a separate VITE_COMPANY_API_BASE_URL for the company service proxy')
    }
    proxy[companyBase] = {
      target: env.DEV_COMPANY_API_PROXY_TARGET,
      changeOrigin: true,
      rewrite: requestPath => `/api${requestPath.slice(companyBase.length)}`
    }
  }
  return {
    plugins: [vue()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
        '/models': path.resolve(__dirname, './public/models')
      }
    },
    server: {
      host: env.DEV_HOST || '127.0.0.1',
      port,
      proxy
    }
  }
})
