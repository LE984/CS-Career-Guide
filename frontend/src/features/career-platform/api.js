// Pure API factory: tests supply a client; production uses the existing authenticated client.
export function newRequestId() {
  const bytes = crypto.getRandomValues(new Uint8Array(16))
  bytes[6] = (bytes[6] & 15) | 64; bytes[8] = (bytes[8] & 63) | 128
  const h = Array.from(bytes, b => b.toString(16).padStart(2, '0')).join('')
  return `${h.slice(0,8)}-${h.slice(8,12)}-${h.slice(12,16)}-${h.slice(16,20)}-${h.slice(20)}`
}
export function createPlatformAPI(client) {
  const base = '/career-platform/'
  return {
    catalog: (kind, params = {}, signal) => client.get(base + `catalog/${kind}/`, {params,signal}),
    importBatch: data => client.post(base + 'catalog/imports/', data),
    analyses: signal => client.get(base + 'resume-analyses/', {signal}),
    analyze: data => client.post(base + 'resume-analyses/', data),
    analysis: id => client.get(base + `resume-analyses/${encodeURIComponent(id)}/`),
    apply: (id,data) => client.post(base + `resume-analyses/${encodeURIComponent(id)}/apply/`,data),
    retrieve: data => client.post(base + 'questions/retrieve/',data),
    sessions: signal => client.get(base + 'practice-sessions/',{signal}),
    start: data => client.post(base + 'practice-sessions/',data),
    session: id => client.get(base + `practice-sessions/${encodeURIComponent(id)}/`),
    answer: (id,data) => client.post(base + `practice-sessions/${encodeURIComponent(id)}/answers/`,data),
    finish: (id,data) => client.post(base + `practice-sessions/${encodeURIComponent(id)}/finish/`,data),
    evaluations: signal => client.get(base + 'evaluation-runs/',{signal}),
    evaluate: data => client.post(base + 'evaluation-runs/',data),
    evaluation: id => client.get(base + `evaluation-runs/${encodeURIComponent(id)}/`),
    exportEvaluation: id => client.get(base + `evaluation-runs/${encodeURIComponent(id)}/export/`),
  }
}
export function platformFailure(error) {
  if (error.response?.status === 501) return '功能待实现。当前仅提供开发骨架。'
  if (error.response?.status === 403) return '此操作需要管理员权限。'
  if (error.response?.status === 404) return '记录不存在或你没有访问权限。'
  if (error.response?.status === 409) return '内容已经变化，请刷新后重试。'
  return '请求未完成，请检查输入或稍后重试。'
}
