// Presentation only: callers keep complete model text for history and saving.
export function createTextReveal(onUpdate, {
  requestFrame = globalThis.requestAnimationFrame,
  cancelFrame = globalThis.cancelAnimationFrame,
  now = () => performance.now(),
  immediate = () => false,
} = {}) {
  const segmenter = new Intl.Segmenter('zh', { granularity: 'grapheme' })
  let target = '', units = [], shown = 0, credit = 0, frame = null, previous = 0
  function publish() { onUpdate(units.slice(0, shown).join(''), shown < units.length) }
  function tick(time) {
    frame = null
    if (immediate()) { flush(); return }
    if (time - previous > 250) { flush(); return }
    const elapsed = Math.min(64, Math.max(0, time - previous))
    previous = time
    // A large network chunk catches up within about half a second instead of
    // making the reader wait through a long, artificially slow typewriter.
    credit += elapsed * Math.max(45, (units.length - shown) / 0.45) / 1000
    const count = Math.floor(credit)
    credit -= count
    shown = Math.min(units.length, shown + count)
    publish()
    if (shown < units.length) frame = requestFrame(tick)
  }
  function flush() {
    if (frame !== null) cancelFrame(frame)
    frame = null; shown = units.length; credit = 0
    publish()
  }
  return {
    set(text) {
      if (text === target) return
      const appended = text.startsWith(target)
      target = text
      units = Array.from(segmenter.segment(text), part => part.segment)
      if (!appended) { shown = 0; credit = 0 }
      if (immediate()) { flush(); return }
      if (frame === null) {
        previous = now(); credit = 0
        if (shown === 0 && units.length) shown = 1
        publish()
        if (shown < units.length) frame = requestFrame(tick)
      }
    },
    flush,
    dispose() { if (frame !== null) cancelFrame(frame); frame = null },
  }
}
