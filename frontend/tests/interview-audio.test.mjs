import assert from 'node:assert/strict'
import test from 'node:test'
import { createInterviewAudio } from '../src/features/interview/audio.js'
import { interviewPlainText } from '../src/features/interview/plain-text.js'

function harness({ mse = true, deferredPlay = false } = {}) {
  const players = [], sources = [], revoked = []
  let resolvePlay
  class Audio {
    constructor() { players.push(this); this.plays = this.pauses = 0 }
    play() { this.plays++; return deferredPlay ? new Promise(resolve => { resolvePlay = resolve }) : Promise.resolve() }
    pause() { this.pauses++ }
    removeAttribute() {}
    load() {}
  }
  class MediaSource {
    static isTypeSupported() { return mse }
    constructor() { this.readyState = 'open'; this.events = {}; sources.push(this) }
    addEventListener(name, callback) { this.events[name] = callback }
    addSourceBuffer() {
      this.buffer = { updating: false, events: {}, added: [],
        addEventListener(name, callback) { this.events[name] = callback },
        appendBuffer(bytes) { this.added.push(bytes); this.updating = true },
      }
      return this.buffer
    }
    endOfStream() { this.ended = true }
  }
  const audio = createInterviewAudio({ AudioClass: Audio, MediaSourceClass: MediaSource,
    urls: { createObjectURL: () => 'blob:fake', revokeObjectURL: url => revoked.push(url) } })
  return { audio, players, sources, revoked, resolvePlay: () => resolvePlay?.() }
}

test('paused playback stays paused when late chunks and sourceopen arrive', async () => {
  const h = harness()
  h.audio.begin()
  h.audio.pause()
  h.audio.append(btoa('mp3'))
  h.sources[0].events.sourceopen()
  assert.equal(h.players[0].plays, 0)
  h.audio.append(btoa('later'))
  assert.equal(h.players[0].plays, 0)
  h.audio.resume()
  assert.equal(h.players[0].plays, 1)
})

test('a pending play promise cannot undo a user pause', async () => {
  const h = harness({ deferredPlay: true })
  h.audio.begin()
  h.sources[0].events.sourceopen()
  h.audio.pause()
  const pauses = h.players[0].pauses
  h.resolvePlay()
  await Promise.resolve()
  assert.equal(h.players[0].pauses, pauses + 1)
})

test('end of stream waits for buffered chunks, and late sourceopen cannot revive stopped playback', () => {
  const h = harness()
  h.audio.begin()
  const source = h.sources[0]
  source.events.sourceopen()
  h.audio.append(btoa('mp3'))
  h.audio.finish()
  assert.equal(source.ended, undefined)
  source.buffer.updating = false
  source.buffer.events.updateend()
  assert.equal(source.ended, true)
  h.audio.stop()
  const plays = h.players[0].plays
  source.events.sourceopen()
  assert.equal(h.players[0].plays, plays)
  assert.equal(h.revoked.length, 1)
})

test('browsers without MP3 MediaSource still play a complete audio blob, respecting pause', () => {
  const h = harness({ mse: false })
  h.audio.begin()
  h.audio.append(btoa('mp3'))
  h.audio.pause()
  h.audio.finish()
  assert.equal(h.players[0].plays, 0)
  h.audio.resume()
  assert.equal(h.players[0].plays, 1)
})

test('text-only setup never constructs an audio device', () => {
  const h = harness()
  assert.equal(h.players.length, 0)
  h.audio.stop()
  assert.equal(h.players.length, 0)
})

test('legacy Markdown becomes readable inert text, retaining technical operators', () => {
  assert.equal(interviewPlainText('# 总结\n**优点**：清晰\n- 熟悉 `C++`\n```text\na * b < c\n```'),
    '总结\n优点：清晰\n• 熟悉 C++\na * b < c\n')
})
