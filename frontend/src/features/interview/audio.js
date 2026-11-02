// Playback is independent of the model stream and microphone permission.
export function createInterviewAudio({ AudioClass = globalThis.Audio, MediaSourceClass = globalThis.MediaSource,
  urls = globalThis.URL, onBlocked = () => {} } = {}) {
  let player, media, buffer, url, paused = false, ended = false, queue = [], chunks = [], generation = 0

  function stop() {
    generation++
    player?.pause()
    if (player) { player.removeAttribute('src'); player.load() }
    if (url) urls.revokeObjectURL(url)
    player = media = buffer = url = null
    queue = []; chunks = []; ended = false
  }

  function play() {
    if (!player || paused) return
    const current = generation
    const active = player
    Promise.resolve(active.play()).then(() => {
      // A pending play() must not undo a later pause or teardown.
      if (current !== generation || paused) active.pause()
    }).catch(() => {
      if (current === generation && !paused) onBlocked()
    })
  }

  function drain() {
    if (!buffer || buffer.updating || media.readyState !== 'open') return
    if (queue.length) {
      try { buffer.appendBuffer(queue.shift()) } catch { onBlocked() }
    } else if (ended) {
      try { media.endOfStream() } catch { /* A later updateend can retry. */ }
    }
  }

  function begin({ startPaused = false } = {}) {
    stop()
    paused = startPaused
    player = new AudioClass()
    if (MediaSourceClass?.isTypeSupported?.('audio/mpeg')) {
      media = new MediaSourceClass()
      url = urls.createObjectURL(media)
      player.src = url
      const current = generation
      media.addEventListener('sourceopen', () => {
        if (current !== generation) return
        try {
          buffer = media.addSourceBuffer('audio/mpeg')
          buffer.addEventListener('updateend', () => { if (current === generation) drain() })
          drain()
          play()
        } catch { onBlocked() }
      }, { once: true })
    }
  }

  function append(base64) {
    if (!player || !base64) return
    const bytes = Uint8Array.from(atob(base64), c => c.charCodeAt(0))
    if (media) { queue.push(bytes); drain(); play() }
    else chunks.push(bytes)
  }

  function finish() {
    if (!player || ended) return
    ended = true
    if (media) drain()
    else if (chunks.length) {
      url = urls.createObjectURL(new Blob(chunks, { type: 'audio/mpeg' }))
      player.src = url
      play()
      chunks = []
    }
  }

  return { begin, append, finish, stop,
    pause() { paused = true; player?.pause() },
    resume() { paused = false; play() },
  }
}
