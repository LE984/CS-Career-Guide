import assert from 'node:assert/strict'
import test from 'node:test'
import { createPageLoader, displayDate, errorMessage, externalUrl, fieldErrors, pageNumbers, plainText, readBrowseQuery, splitPoints } from '../src/features/company-reviews/browse.js'
const state = () => ({ items: [], count: 0, loading: false, error: '' })

test('query restores valid tabs, search, sort and bounded page settings', () => {
  assert.deepEqual(readBrowseQuery({ tab: 'advice', q: ' Vue ', page: '12', size: '50', sort: 'rating' }), { tab: 'advice', search: 'Vue', page: 12, pageSize: 50, ordering: 'rating' })
  const invalid = readBrowseQuery({ tab: ['jobs'], page: '-5', size: 1000000, q: {}, sort: 'invalid' })
  assert.equal(invalid.page, 1); assert.equal(invalid.pageSize, 10); assert.equal(invalid.tab, 'jobs')
  assert.equal(readBrowseQuery({ job_title: '前端开发' }).search, '前端开发')
  assert.equal(readBrowseQuery({ q: '', job_title: '前端开发' }).search, '')
})
test('pagination renders bounded controls even for one hundred thousand pages', () => {
  assert.deepEqual(pageNumbers(3, 5), [1, 2, 3, 4, 5])
  const pages = pageNumbers(50000, 100000)
  assert.ok(pages.length <= 7); assert.ok(pages.includes(1)); assert.ok(pages.includes(100000))
})
test('large dataset requires only one request per page', async () => {
  const current = state(), calls = []
  const loader = createPageLoader(current, async params => { calls.push(params); return { count: 100000, results: Array.from({ length: params.page_size }, (_, i) => ({ id: (params.page-1)*params.page_size+i })) } })
  await loader.load({ page: 1, page_size: 10 }); assert.equal(calls.length, 1); assert.equal(current.items.length, 10)
  await loader.load({ page: 2, page_size: 10 }); assert.equal(calls.length, 2); assert.equal(current.items[0].id, 10)
})
test('older search response cannot overwrite newer results and abort is requested', async () => {
  const current = state(), pending = []
  const loader = createPageLoader(current, (params, options) => new Promise(resolve => pending.push({ resolve, options })))
  const a = loader.load({ search: 'old' }), b = loader.load({ search: 'new' })
  assert.equal(pending[0].options.signal.aborted, true)
  pending[1].resolve({ count: 1, results: [{ id: 'new' }] }); await b
  pending[0].resolve({ count: 5, results: [{ id: 'old' }] }); await a
  assert.equal(current.items[0].id, 'new'); assert.equal(current.count, 1)
})
test('cancelling on tab change prevents late updates', async () => {
  const current = state(); let resolve
  const loader = createPageLoader(current, () => new Promise(done => { resolve = done }))
  const pending = loader.load({}); loader.cancel(); resolve({ count: 1, results: [1] }); await pending
  assert.deepEqual(current.items, []); assert.equal(current.loading, false)
})
test('failure, empty and malformed responses remain distinguishable and retry works', async () => {
  const current = state(); let attempt = 0
  const loader = createPageLoader(current, async () => {
    if (!attempt++) throw { response: { status: 503, data: { code: 'JOBS_UNAVAILABLE', message: '职位数据暂时无法读取，请稍后重试。' } } }
    return { count: 0, results: [] }
  })
  await loader.load({}); assert.match(current.error, /无法读取/)
  await loader.load({}); assert.equal(current.error, ''); assert.equal(current.count, 0)
  await createPageLoader(current, async () => ({ count: 'bad' })).load({}); assert.match(current.error, /格式异常/)
})
test('errors explain network timeout permissions and server failure without dumping traces', () => {
  assert.match(errorMessage({ code: 'ECONNABORTED' }), /超时/)
  assert.match(errorMessage({}), /无法连接/)
  assert.match(errorMessage({ response: { status: 403 } }), /权限/)
  assert.match(errorMessage({ response: { status: 404 } }), /第一页/)
  assert.match(errorMessage({ response: { status: 500, data: '<html>private trace</html>' } }), /HTTP 500/)
  assert.deepEqual(fieldErrors({ response: { data: { errors: { company: ['必填'], unrelated: ['hidden'] } } } }), { company: '必填' })
})
test('optional display fields, external links and Chinese comma input are safe', () => {
  assert.equal(plainText(null), ''); assert.equal(plainText('A<br/>B'), 'A B')
  assert.equal(externalUrl('javascript:alert(1)'), ''); assert.equal(externalUrl('https://example.com/job'), 'https://example.com/job')
  assert.equal(displayDate('invalid'), '日期未提供')
  assert.deepEqual(splitPoints('导师，交流,导师\n项目'), ['导师', '交流', '项目'])
})
