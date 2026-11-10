// Presentation only: keep unfinished lines buffered while the model is streaming.
// The caller retains the complete text for saving and request context.
export function createLineReveal(onUpdate, {
  requestFrame = globalThis.requestAnimationFrame,
  cancelFrame = globalThis.cancelAnimationFrame,
  now = () => performance.now(),
  immediate = () => false,
  lineInterval = 90,
} = {}) {
  let target = '', complete = false, lines = [], shown = 0
  let frame = null, previous = 0, elapsed = 0, disposed = false

  function publish() {
    const visible = lines.slice(0, shown).join('')
    onUpdate(visible, visible.length < target.length)
  }

  function flush() {
    if (frame !== null) cancelFrame(frame)
    frame = null
    shown = lines.length
    elapsed = 0
    publish()
  }

  function tick(time) {
    frame = null
    if (disposed) return
    if (immediate() || time - previous > 250) { flush(); return }
    elapsed += Math.max(0, time - previous)
    previous = time
    if (elapsed >= lineInterval) {
      shown = Math.min(lines.length, shown + 1)
      elapsed = 0
      publish()
    }
    if (shown < lines.length) frame = requestFrame(tick)
  }

  return {
    set(text, { complete: finished = false } = {}) {
      if (disposed || (text === target && finished === complete)) return
      if (!text.startsWith(target)) {
        if (frame !== null) cancelFrame(frame)
        frame = null
        shown = 0
        elapsed = 0
      }
      target = text
      complete = finished
      const ready = complete ? target : target.slice(0, target.lastIndexOf('\n') + 1)
      lines = ready.match(/[^\n]*\n|[^\n]+$/g) || []
      if (immediate()) { flush(); return }
      if (shown === 0 && lines.length) shown = 1
      publish()
      if (frame === null && shown < lines.length) {
        previous = now()
        elapsed = 0
        frame = requestFrame(tick)
      }
    },
    flush,
    dispose() {
      disposed = true
      if (frame !== null) cancelFrame(frame)
      frame = null
    },
  }
}
