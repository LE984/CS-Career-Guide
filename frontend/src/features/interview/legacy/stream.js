/** Decode the existing POST/SSE chat protocol; UI and audio APIs stay outside. */
export async function readLegacyStream(response, onEvent = () => {}) {
  if (!response.ok) throw new Error(`API请求失败，状态码: ${response.status}`)
  const reader = response.body.getReader()
  const decoder = new TextDecoder('utf-8')
  let buffer = ''
  let received = false

  async function dispatch(frame) {
    const data = frame.split(/\r?\n/)
      .filter(line => line.startsWith('data:'))
      .map(line => line.slice(5).trimStart()).join('\n').trim()
    if (!data || data === '[DONE]') return
    let event
    try { event = JSON.parse(data) } catch { return }
    await onEvent(event)
  }

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      received = true
      buffer += decoder.decode(value, { stream: true })
      const frames = buffer.split(/\r?\n\r?\n/)
      buffer = frames.pop()
      for (const frame of frames) await dispatch(frame)
    }
    buffer += decoder.decode()
    if (buffer.trim()) await dispatch(buffer)
  } finally {
    reader.releaseLock()
  }
  if (!received) throw new Error('未收到任何数据')
}
