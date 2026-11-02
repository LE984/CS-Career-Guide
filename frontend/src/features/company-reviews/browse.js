export const tabs = [
  { id: 'jobs', label: '职位列表' }, { id: 'red', label: '红榜' },
  { id: 'black', label: '黑榜' }, { id: 'safety', label: '求职安全' },
  { id: 'advice', label: '学长学姐建议' },
]
export const pageSizes = [10, 20, 50]
export const text = value => typeof value === 'string' ? value : ''
export function readBrowseQuery(query) {
  const id = text(query.tab)
  return {
    tab: tabs.some(tab => tab.id === id) ? id : 'jobs',
    search: text(query.q ?? query.job_title).trim().slice(0, 200),
    page: /^\d+$/.test(text(query.page)) && Number(query.page) > 0 && Number(query.page) <= 1000000 ? Number(query.page) : 1,
    pageSize: pageSizes.includes(Number(query.size)) ? Number(query.size) : 10,
    ordering: query.sort === 'rating' ? 'rating' : 'recent',
  }
}
export function pageNumbers(page, total) {
  if (total <= 7) return Array.from({ length: total }, (_, index) => index + 1)
  const values = [...new Set([1, page - 1, page, page + 1, total])].filter(n => n > 0 && n <= total).sort((a, b) => a - b)
  return values.flatMap((n, index) => index && n - values[index - 1] > 1 ? ['…', n] : [n])
}
export function externalUrl(value) {
  try { const url = new URL(text(value)); return ['http:', 'https:'].includes(url.protocol) ? url.href : '' } catch { return '' }
}
export function plainText(value) { return text(value).replace(/<br\s*\/?\s*>/gi, ' ').replace(/<[^>]*>/g, '').trim() }
export function displayDate(value) {
  if (!value) return '日期未提供'
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? '日期未提供' : new Intl.DateTimeFormat('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' }).format(date)
}
export function splitPoints(value) { return [...new Set(text(value).split(/[,，\n]/).map(item => item.trim()).filter(Boolean))] }
export const fieldLabels = { company: '公司名称', position: '职位名称', senior_name: '姓名', graduation_year: '毕业年份', current_company: '当前公司', advice: '详细建议', salary_info: '薪资信息', rating: '评分', pros: '值得关注', cons: '需要了解', non_field_errors: '表单' }
export function fieldErrors(error) {
  const fields = error?.response?.data?.errors
  if (!fields || typeof fields !== 'object' || Array.isArray(fields)) return {}
  return Object.fromEntries(Object.entries(fields).filter(([key]) => key in fieldLabels).map(([key, value]) => [key, (Array.isArray(value) ? value : [value]).filter(item => typeof item === 'string').join('；') || '请检查此项内容。']))
}
export function errorMessage(error) {
  if (error?.code === 'ECONNABORTED' || error?.code === 'ETIMEDOUT') return '请求超时，请检查网络后重试。'
  if (error?.code === 'INVALID_PAGE_DATA') return '服务返回的数据格式异常，请稍后重试。'
  const status = error?.response?.status
  const data = error?.response?.data
  if (!status) return '无法连接服务，请检查网络或确认本地后端已启动。'
  if (status === 401) return '登录已过期，请重新登录。'
  if (status === 403) return '当前账号没有访问权限。'
  if (status === 404) return '请求的页码或资源不存在，可能已发生变化。请返回第一页重试。'
  if (status === 429) return '请求过于频繁，请稍后再试。'
  if (status >= 500) {
    const safeCodes = ['JOBS_UNAVAILABLE', 'ADVICE_UNAVAILABLE', 'JOB_FAIRS_UNAVAILABLE']
    return safeCodes.includes(data?.code) && typeof data.message === 'string' ? data.message : `服务暂时不可用（HTTP ${status}），请稍后重试。`
  }
  return text(data?.message) || text(data?.detail) || `请求未完成（HTTP ${status}），请检查输入后重试。`
}

// 每次只请求一页；过期响应不能覆盖后一次搜索或分页的结果。
export function createPageLoader(state, request) {
  let sequence = 0
  let controller
  function cancel() { sequence++; controller?.abort(); state.loading = false }
  async function load(params) {
    controller?.abort()
    controller = new AbortController()
    const current = ++sequence
    state.loading = true; state.error = ''; state.items = []; state.count = 0
    try {
      const result = await request(params, { signal: controller.signal })
      if (current !== sequence) return
      if (!Array.isArray(result?.results) || !Number.isInteger(result.count) || result.count < 0) throw { code: 'INVALID_PAGE_DATA' }
      state.items = result.results; state.count = result.count
    } catch (error) {
      if (current !== sequence || error?.code === 'ERR_CANCELED' || error?.name === 'AbortError') return
      state.error = errorMessage(error)
    } finally { if (current === sequence) state.loading = false }
  }
  return { load, cancel }
}
