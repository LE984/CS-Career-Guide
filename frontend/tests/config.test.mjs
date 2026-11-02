import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'
import { fileURLToPath } from 'node:url'
import { loadConfigFromFile } from 'vite'

const source = await readFile(new URL('../src/config.js', import.meta.url), 'utf8')
const viteConfigPath = fileURLToPath(new URL('../vite.config.js', import.meta.url))

async function clientConfig(env = {}) {
  const code = source.replaceAll('import.meta.env', JSON.stringify({ BASE_URL: '/', ...env }))
  return import(`data:text/javascript;base64,${Buffer.from(code).toString('base64')}`)
}

async function withEnv(values, callback) {
  const previous = Object.fromEntries(Object.keys(values).map(key => [key, process.env[key]]))
  for (const [key, value] of Object.entries(values)) process.env[key] = value
  try {
    return await callback()
  } finally {
    for (const [key, value] of Object.entries(previous)) {
      if (value === undefined) delete process.env[key]
      else process.env[key] = value
    }
  }
}

test('default requests and VAD assets stay on the current origin', async () => {
  const config = await clientConfig()
  assert.equal(config.apiUrl('/ai/llm/chat/'), '/api/ai/llm/chat/')
  assert.equal(config.COMPANY_API_BASE_URL, '/api')
  assert.equal(config.VAD_ASSET_BASE_URL, '/models/vad/')
  assert.equal(config.ENABLE_TTS, false)
  assert.equal(config.GEOCODING_URL, '')
})

test('absolute API URLs apply to streaming endpoints without duplicate slashes', async () => {
  const config = await clientConfig({
    VITE_API_BASE_URL: 'https://api.test/prefix/api///',
    VITE_COMPANY_API_BASE_URL: 'https://company.test/api/',
    VITE_VAD_ASSET_BASE_URL: 'https://assets.test/vad',
    VITE_ENABLE_TTS: 'TRUE', VITE_API_TIMEOUT_MS: '45000',
  })
  assert.equal(config.apiUrl('/ai/interview/save_review/'), 'https://api.test/prefix/api/ai/interview/save_review/')
  assert.equal(config.COMPANY_API_BASE_URL, 'https://company.test/api')
  assert.equal(config.VAD_ASSET_BASE_URL, 'https://assets.test/vad/')
  assert.equal(config.ENABLE_TTS, true)
  assert.equal(config.API_TIMEOUT, 45000)
})

test('default asset URLs follow the application base path', async () => {
  const config = await clientConfig({ BASE_URL: '/career/' })
  assert.equal(config.VAD_ASSET_BASE_URL, '/career/models/vad/')
  assert.match(config.AVATAR_MODEL_URL, /^\/career\/models\//)
})

test('invalid client timeout fails with the configuration name', async () => {
  await assert.rejects(clientConfig({ VITE_API_TIMEOUT_MS: 'wrong' }), /VITE_API_TIMEOUT_MS/)
})

test('development proxies honor environment targets and preserve company API routes', async () => {
  await withEnv({
    DEV_HOST: '0.0.0.0', DEV_PORT: '4321',
    VITE_API_BASE_URL: '/api', VITE_COMPANY_API_BASE_URL: '/company-api',
    DEV_API_PROXY_TARGET: 'http://backend.test:8100',
    DEV_COMPANY_API_PROXY_TARGET: 'http://company.test:3100',
  }, async () => {
    const { config } = await loadConfigFromFile({ command: 'serve', mode: 'test' }, viteConfigPath)
    assert.equal(config.server.host, '0.0.0.0')
    assert.equal(config.server.port, 4321)
    assert.equal(config.server.proxy['/api'].target, 'http://backend.test:8100')
    assert.equal(config.server.proxy['/company-api'].target, 'http://company.test:3100')
    assert.equal(config.server.proxy['/company-api'].rewrite('/company-api/search?q=test'), '/api/search?q=test')
  })
})

test('invalid dev port fails before a server starts', async () => {
  await withEnv({ DEV_PORT: '65536' }, async () => {
    await assert.rejects(loadConfigFromFile({ command: 'serve', mode: 'test' }, viteConfigPath), /DEV_PORT/)
  })
})
