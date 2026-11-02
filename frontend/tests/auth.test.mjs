import assert from 'node:assert/strict'
import test, { beforeEach } from 'node:test'
import axios from 'axios'
import { createMemoryHistory, createRouter } from 'vue-router'
import { clearSession, handleUnauthorized, safeRedirect } from '../src/auth/session.js'
import { createAuthGuard } from '../src/router/guard.js'
import { createApiFetch, installAuthInterceptors } from '../src/api/transport.js'

let redirects
beforeEach(() => {
  const data = new Map()
  globalThis.localStorage = {
    getItem: key => data.get(key) ?? null,
    setItem: (key, value) => data.set(key, value),
    removeItem: key => data.delete(key),
  }
  redirects = []
  globalThis.window = { location: {
    pathname: '/interview', search: '?mode=normal', hash: '#chat',
    replace: url => redirects.push(url),
  } }
})

const unauthorized = () => Object.assign(new Error('Unauthorized'), { response: { status: 401 } })
const route = path => ({ path: path.split('?')[0], fullPath: path })

test('all business pages and future paths require login with the original destination', async () => {
  const guard = createAuthGuard(() => assert.fail('No token must not trigger an API call'))
  for (const path of ['/', '/career-paths', '/career-paths/employment',
    '/career-paths/employment/self-introduction', '/company-reviews', '/resume',
    '/interview', '/career-evaluation', '/career-plan', '/users', '/future-page']) {
    assert.deepEqual(await guard(route(path)), { path: '/login', query: { redirect: path } })
  }
  assert.equal(await guard(route('/login')), true)
  assert.equal(await guard(route('/register')), true)
  assert.equal(await guard(route('/login/')), true)
  assert.equal(await guard(route('/REGISTER')), true)
})

test('router validates stored tokens before allowing navigation, including static detail pages', async () => {
  localStorage.setItem('token', 'forged')
  let calls = 0
  const guard = createAuthGuard(async () => { calls++; throw unauthorized() })
  assert.deepEqual(await guard(route('/career-paths/employment')), {
    path: '/login', query: { redirect: '/career-paths/employment' },
  })
  assert.equal(calls, 1)
  assert.equal(localStorage.getItem('token'), null)
  localStorage.setItem('token', 'valid')
  assert.equal(await createAuthGuard(async () => ({}))(route('/interview')), true)
})

test('real Vue Router navigation preserves query/hash through the login guard', async () => {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: ['/login', '/register', '/career-paths/:type', '/interview'].map(path => ({ path, component: {} })),
  })
  router.beforeEach(createAuthGuard(async () => ({})))
  await router.push('/career-paths/employment?from=home#details')
  assert.equal(router.currentRoute.value.path, '/login')
  assert.equal(router.currentRoute.value.query.redirect, '/career-paths/employment?from=home#details')
  localStorage.setItem('token', 'valid')
  await router.replace(safeRedirect(router.currentRoute.value.query.redirect))
  assert.equal(router.currentRoute.value.fullPath, '/career-paths/employment?from=home#details')
  await router.push('/register')
  assert.equal(router.currentRoute.value.path, '/register')
})

test('network failures fail closed without deleting a potentially valid token', async () => {
  localStorage.setItem('token', 'valid')
  const guard = createAuthGuard(async () => { throw new Error('offline') })
  assert.equal((await guard(route('/resume'))).path, '/login')
  assert.equal(localStorage.getItem('token'), 'valid')
})

test('safe redirects reject external URLs, auth loops and malformed inputs', () => {
  for (const value of [undefined, ['/interview'], 'https://evil.test', '//evil.test',
    '/\\evil.test', '/%2fevil.test', '/%5cevil.test', '/\nevil.test', '/%00evil',
    '/%', '/login', '/register?redirect=/login', '/a/../login', '/login/', '/%6cogin']) {
    assert.equal(safeRedirect(value), '/', String(value))
  }
  assert.equal(safeRedirect('/interview?mode=normal#chat'), '/interview?mode=normal#chat')
  assert.equal(safeRedirect('/career-paths/就业/self-introduction'), '/career-paths/%E5%B0%B1%E4%B8%9A/self-introduction')
})

test('401 clears the session, preserves the destination and does not redirect public pages', () => {
  localStorage.setItem('token', 'expired')
  localStorage.setItem('user', '{}')
  localStorage.setItem('resume', 'private')
  handleUnauthorized('expired')
  assert.equal(localStorage.getItem('token'), null)
  assert.equal(localStorage.getItem('user'), null)
  assert.equal(localStorage.getItem('resume'), null)
  assert.deepEqual(redirects, ['/login?redirect=%2Finterview%3Fmode%3Dnormal%23chat'])
  for (const path of ['/login', '/register']) {
    window.location.pathname = path
    localStorage.setItem('token', 'expired')
    handleUnauthorized('expired')
  }
  assert.equal(redirects.length, 1)
})

test('late 401 from an older session does not log out a newly logged-in account', () => {
  localStorage.setItem('token', 'new-session')
  handleUnauthorized('old-session')
  assert.equal(localStorage.getItem('token'), 'new-session')
  assert.deepEqual(redirects, [])
})

test('each Axios client attaches the token and handles 401 with the same policy', async () => {
  for (const baseURL of ['/api', '/company-api']) {
    localStorage.setItem('token', 'valid')
    const client = axios.create({ baseURL, adapter: async config => {
      assert.equal(config.headers.get('Authorization'), 'Token valid')
      return { data: { ok: true }, status: 200, statusText: 'OK', headers: {}, config }
    } })
    installAuthInterceptors(client)
    assert.deepEqual(await client.get('/business'), { ok: true })
    client.defaults.adapter = async config => {
      throw Object.assign(unauthorized(), { config })
    }
    await assert.rejects(client.get('/business'))
    assert.equal(localStorage.getItem('token'), null)
  }
  assert.equal(redirects.length, 2)
})

test('login and registration Axios requests omit stale tokens and do not cause 401 redirects', async () => {
  localStorage.setItem('token', 'expired')
  const client = axios.create({ headers: { Authorization: 'Token inherited' }, adapter: async config => {
    assert.equal(config.headers.get('Authorization'), undefined)
    throw Object.assign(unauthorized(), { config })
  } })
  installAuthInterceptors(client)
  for (const path of ['/users/auth/login/', '/users/auth/register/']) {
    await assert.rejects(client.post(path, {}, { publicAuth: true }))
  }
  assert.equal(localStorage.getItem('token'), 'expired')
  assert.deepEqual(redirects, [])
})

test('Axios guard probes leave 401 navigation to the router', async () => {
  localStorage.setItem('token', 'invalid')
  const client = axios.create({ adapter: async config => { throw Object.assign(unauthorized(), { config }) } })
  installAuthInterceptors(client)
  await assert.rejects(client.get('/users/profile/', { redirectOnUnauthorized: false }))
  assert.deepEqual(redirects, [])
})

test('fetch adds auth headers, keeps caller headers/signal and returns the unconsumed stream', async () => {
  localStorage.setItem('token', 'valid')
  const response = new Response(new ReadableStream({ start(controller) {
    controller.enqueue(new TextEncoder().encode('data: chunk\n\n'))
    controller.close()
  } }), { headers: { 'Content-Type': 'text/event-stream' } })
  const controller = new AbortController()
  const original = globalThis.fetch
  globalThis.fetch = async (url, options) => {
    assert.equal(url, '/api/ai/llm/chat/')
    assert.equal(options.headers.get('Authorization'), 'Token valid')
    assert.equal(options.headers.get('Content-Type'), 'application/json')
    assert.equal(options.signal, controller.signal)
    return response
  }
  try {
    const result = await createApiFetch(path => `/api${path}`)('/ai/llm/chat/', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: '{}', signal: controller.signal,
    })
    assert.equal(result, response)
    assert.equal(result.bodyUsed, false)
    assert.equal(result.body.locked, false)
    assert.equal(await result.text(), 'data: chunk\n\n')
  } finally { globalThis.fetch = original }
})

test('fetch 401 uses the same cleanup and redirect; never consumes the error body', async () => {
  localStorage.setItem('token', 'expired')
  const response = new Response('unauthorized', { status: 401 })
  const original = globalThis.fetch
  globalThis.fetch = async () => response
  try {
    await assert.rejects(createApiFetch(path => `/api${path}`)('/ai/llm/chat/'), { status: 401 })
    assert.equal(response.bodyUsed, false)
    assert.equal(localStorage.getItem('token'), null)
    assert.equal(redirects.length, 1)
  } finally { globalThis.fetch = original }
})

test('clearing the session preserves unrelated UI preferences', () => {
  localStorage.setItem('theme', 'dark')
  localStorage.setItem('token', 'valid')
  clearSession()
  assert.equal(localStorage.getItem('token'), null)
  assert.equal(localStorage.getItem('theme'), 'dark')
})
