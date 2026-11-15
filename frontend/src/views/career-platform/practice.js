import { newRequestId, platformFailure } from '../../features/career-platform/api.js'

export const payload = response => response?.data ?? response
export const questionId = question => String(question?.question_id || '')
export const difficultyLabel = value => ({ easy: '基础', medium: '进阶', hard: '深入' })[value] || '未指定'

export function practiceContext(form) {
  const role = form.role.trim(), topic = form.topic.trim(), jd = form.jd_text.trim()
  if (!role) throw new Error('请填写岗位方向。')
  const result = { role, difficulty: form.difficulty }
  if (topic) result.topic = topic
  if (jd) result.jd_text = jd
  return result
}

// Retain the same request ID after an uncertain network result. A changed payload
// is a new operation, not a replay. Keep retries in memory, never in localStorage.
export function createPracticeActions(api, makeId = newRequestId) {
  const receipts = new Map()
  async function mutate(action, data, send) {
    const key = JSON.stringify([action, data])
    if (!receipts.has(key)) receipts.set(key, makeId())
    return payload(await send({ ...data, request_id: receipts.get(key) }))
  }
  return {
    retrieve: async form => {
      const context = practiceContext(form)
      const result = payload(await api.retrieve({ ...context, top_k: form.top_k, request_id: makeId() }))
      if (!Array.isArray(result?.results) || !result.retrieval_id) throw new Error('检索结果格式异常，请重新检索。')
      return { ...result, context }
    },
    start: (retrieval, selected) => {
      const ids = retrieval.results.map(questionId).filter(id => selected.includes(id))
      if (!ids.length) throw new Error('请至少选择一道题。')
      return mutate('start', { ...retrieval.context, question_ids: ids, retrieval_id: retrieval.retrieval_id }, data => api.start(data))
    },
    answer: (sessionId, id, answer) => {
      if (!answer.trim() || answer.length > 20000) throw new Error('请填写 1 至 20000 字的回答。')
      return mutate(`answer:${sessionId}`, { question_id: id, answer }, data => api.answer(sessionId, data))
    },
    finish: sessionId => mutate(`finish:${sessionId}`, {}, data => api.finish(sessionId, data)),
    retryFeedback: (sessionId, answerId) => mutate(`retry:${sessionId}:${answerId}`, {}, data => api.retryFeedback(sessionId, answerId, data)),
    // An explicit later retry gets a new ID; an uncertain retry reuses its old ID.
    resetFeedbackRetry: (sessionId, answerId) => receipts.delete(JSON.stringify([`retry:${sessionId}:${answerId}`, {}])),
  }
}

export function practiceFailure(error) {
  const status = error?.response?.status
  if (!error?.response && error instanceof Error && !error.isAxiosError) return error.message
  if (status === 400) return '条件或内容不符合要求，请检查输入；岗位方向需与题库一致。'
  if (status === 401) return '登录已失效，请重新登录后查看自己的练习。'
  if (status === 409) return '会话状态或检索凭证已变化。请刷新会话；尚未开始时请重新检索。'
  if ([502, 503, 504].includes(status)) return '服务暂时不可用。已提交的回答可能已保存，请刷新会话确认后重试反馈。'
  if (!status) return '连接中断，结果尚未确认。请重试原操作或刷新会话，不要重复创建练习。'
  return platformFailure(error)
}
