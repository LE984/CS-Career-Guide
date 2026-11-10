import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'

const source = readFileSync(new URL('../src/views/resume/Index.vue', import.meta.url), 'utf8')
const ref = value => ({ value })
function navigation(push) {
  const state = { isOpeningInterview: ref(false), saveNotice: ref(''), saveFailed: ref(false) }
  const body = source.match(/const goToInterview = async \(\) => \{([\s\S]*?)\n\}/)[1]
  const run = new Function('router', ...Object.keys(state), `return async () => {${body}\n}`)({ push }, ...Object.values(state))
  return { ...state, run }
}

test('interview navigation gives immediate feedback and suppresses repeated clicks', async () => {
  let finish, calls = 0
  const state = navigation(path => {
    assert.equal(path, '/interview')
    calls++
    return new Promise(resolve => { finish = resolve })
  })
  const pending = state.run()
  assert.equal(state.isOpeningInterview.value, true)
  assert.match(state.saveNotice.value, /正在进入/)
  await state.run()
  assert.equal(calls, 1)
  finish()
  await pending
  assert.equal(state.isOpeningInterview.value, false)
})

test('rejected and aborted navigation show an error and allow retry', async () => {
  for (const push of [async () => { throw Error('offline') }, async () => new Error('aborted')]) {
    const state = navigation(push)
    await state.run()
    assert.equal(state.isOpeningInterview.value, false)
    assert.equal(state.saveFailed.value, true)
    assert.match(state.saveNotice.value, /重试/)
  }
})

test('live preview entry switches pane, scrolls to content and moves keyboard focus', async () => {
  const calls = [], mobilePane = ref('edit')
  const previewRef = ref({ scrollIntoView: options => calls.push(['scroll', options]), focus: options => calls.push(['focus', options]) })
  const body = source.match(/async function showPreview\(\) \{([\s\S]*?)\n\}/)[1]
  await new Function('mobilePane', 'previewRef', 'nextTick', `return async () => {${body}\n}`)(mobilePane, previewRef, async () => {})()
  assert.equal(mobilePane.value, 'preview')
  assert.deepEqual(calls.map(call => call[0]), ['scroll', 'focus'])
  assert.match(source, /<button[^>]*aria-controls="resume-live-preview"[^>]*@click="showPreview"/)
})
