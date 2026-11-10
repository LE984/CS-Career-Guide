import assert from 'node:assert/strict'
import test from 'node:test'
import { createLineReveal } from '../src/features/interview/line-reveal.js'

function harness() {
  let time = 0, serial = 0, visible = '', pending = false, immediate = false
  const callbacks = new Map()
  const reveal = createLineReveal((text, busy) => { visible = text; pending = busy }, {
    now: () => time,
    requestFrame: callback => { callbacks.set(++serial, callback); return serial },
    cancelFrame: id => callbacks.delete(id),
    immediate: () => immediate,
  })
  return {
    reveal,
    get visible() { return visible },
    get pending() { return pending },
    get scheduled() { return callbacks.size },
    step(ms = 30) {
      time += ms
      const active = [...callbacks.values()]
      callbacks.clear()
      active.forEach(callback => callback(time))
    },
    reduce() { immediate = true; reveal.flush() },
  }
}

test('review buffers unfinished lines instead of exposing a growing character tail', () => {
  const h = harness()
  h.reveal.set('第一行还没结束')
  assert.equal(h.visible, '')
  assert.equal(h.pending, true)
  assert.equal(h.scheduled, 0)
  h.reveal.set('第一行还没结束，现在完整了。\n第二行未完成')
  assert.equal(h.visible, '第一行还没结束，现在完整了。\n')
  h.step(100)
  assert.equal(h.visible, '第一行还没结束，现在完整了。\n')
  assert.equal(h.scheduled, 0)
})

test('bursty multiline reports reveal one full line per interval', () => {
  const h = harness()
  h.reveal.set('表现总结\n回答优点\n改进建议\n', { complete: true })
  assert.equal(h.visible, '表现总结\n')
  h.step(30)
  assert.equal(h.visible, '表现总结\n')
  h.step(60)
  assert.equal(h.visible, '表现总结\n回答优点\n')
  h.step(90)
  assert.equal(h.visible, '表现总结\n回答优点\n改进建议\n')
  assert.equal(h.pending, false)
  assert.equal(h.scheduled, 0)
})

test('the same text becoming complete releases the final line without a newline', () => {
  const h = harness(), text = '第一行\n最后一行👩‍💻'
  h.reveal.set(text)
  assert.equal(h.visible, '第一行\n')
  h.reveal.set(text, { complete: true })
  h.step(90)
  assert.equal(h.visible, text)
  assert.equal(h.pending, false)
})

test('split CRLF, blank lines, Unicode and network appends are preserved exactly', () => {
  const h = harness()
  h.reveal.set('完整的一行\r')
  assert.equal(h.visible, '')
  const text = '完整的一行\r\n\r\n下一行👩‍💻\r\n末行'
  h.reveal.set(text)
  h.step(90)
  h.step(90)
  assert.equal(h.visible, '完整的一行\r\n\r\n下一行👩‍💻\r\n')
  h.reveal.set(text, { complete: true })
  h.step(90)
  assert.equal(h.visible, text)
})

test('replacing a report cancels obsolete queued lines', () => {
  const h = harness()
  h.reveal.set('旧报告\n旧建议\n', { complete: true })
  h.reveal.set('新错误提示', { complete: true })
  h.step(90)
  assert.equal(h.visible, '新错误提示')
  assert.equal(h.scheduled, 0)
})

test('reduced motion flushes complete lines and releases the final tail on completion', () => {
  const h = harness(), text = '总结\n建议\n未结束的行'
  h.reveal.set(text)
  h.reduce()
  assert.equal(h.visible, '总结\n建议\n')
  assert.equal(h.scheduled, 0)
  h.reveal.set(text, { complete: true })
  assert.equal(h.visible, text)
  assert.equal(h.pending, false)
})

test('long frame gaps flush only received complete lines, and teardown cancels updates', () => {
  const h = harness()
  h.reveal.set('一\n二\n未结束')
  h.step(500)
  assert.equal(h.visible, '一\n二\n')
  h.reveal.set('一\n二\n未结束\n最后一行', { complete: true })
  h.reveal.dispose()
  const before = h.visible
  h.step(90)
  h.reveal.set('离开页面后的新内容', { complete: true })
  assert.equal(h.visible, before)
  assert.equal(h.scheduled, 0)
})
