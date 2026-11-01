import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { createRequire } from 'node:module'
import { pathToFileURL } from 'node:url'
import test from 'node:test'

const require = createRequire(import.meta.url)
const dataModule = source => `data:text/javascript;base64,${Buffer.from(source).toString('base64')}`
const configSource = (await readFile(new URL('../src/config.js', import.meta.url), 'utf8'))
  .replaceAll('import.meta.env', JSON.stringify({ BASE_URL: '/' }))
const apiSource = (await readFile(new URL('../src/api/index.js', import.meta.url), 'utf8'))
  .replace("from 'axios'", `from '${pathToFileURL(require.resolve('axios/unsafe/axios.js')).href}'`)
  .replace("from '../config'", `from '${dataModule(configSource)}'`)
  .replace("from './transport.js'", `from '${new URL('../src/api/transport.js', import.meta.url).href}'`)
const { default: api, resumeAPI, interviewAPI, companyInfoAPI } = await import(dataModule(apiSource))
globalThis.localStorage = { getItem: () => 'contract-test-token' }

test('existing resume routes preserve request bodies and multipart uploads', async () => {
  const requests = []
  api.defaults.adapter = async config => {
    requests.push(config)
    return { data: { name: 'round-trip', education: [] }, status: 200, statusText: 'OK', headers: {}, config }
  }
  const body = { name: 'round-trip', education: [], projects: [], skills: '' }
  const result = await resumeAPI.save(body)
  assert.equal(result.name, 'round-trip')
  await resumeAPI.get()
  const upload = new FormData()
  upload.append('avatar', new Blob(['test'], { type: 'image/png' }), 'avatar.png')
  await resumeAPI.uploadAvatar(upload)
  await resumeAPI.deleteAvatar()
  assert.deepEqual(requests.map(r => [r.method, r.url]), [
    ['post', '/resumes/my/'], ['get', '/resumes/my/'],
    ['post', '/resumes/upload_avatar/'], ['delete', '/resumes/delete_avatar/'],
  ])
  assert.deepEqual(JSON.parse(requests[0].data), body)
  assert.equal(requests[2].data, upload)
  assert.ok(requests.every(r => r.headers.get('Authorization') === 'Token contract-test-token'))
})

test('review save/list/detail and ASR use their existing Django routes', async () => {
  const requests = []
  api.defaults.adapter = async config => {
    requests.push(config)
    return { data: { success: true, review_id: 12 }, status: 200, statusText: 'OK', headers: {}, config }
  }
  const review = { session_id: 'session-1', review_content: 'existing report', interview_style: 'technical', question_count: 2, answer_count: 2 }
  assert.equal((await interviewAPI.saveReview(review)).review_id, 12)
  await interviewAPI.listReviews()
  await interviewAPI.getReview('session-1')
  await interviewAPI.getReview('session/with space')
  const audio = new FormData()
  audio.append('audio', new Blob(['audio']))
  await interviewAPI.transcribe(audio)
  assert.deepEqual(requests.map(r => r.url), [
    '/ai/interview/save_review/', '/ai/records/interview-reviews/',
    '/ai/records/interview-reviews/session-1/', '/ai/records/interview-reviews/session%2Fwith%20space/',
    '/asr/speech-to-text/',
  ])
  assert.deepEqual(JSON.parse(requests[0].data), review)
  assert.equal(requests[4].data, audio)
})

test('company information endpoint uses the singular Django router prefix', async () => {
  let sent
  api.defaults.adapter = async config => {
    sent = config
    return { data: { count: 0, results: [] }, status: 200, statusText: 'OK', headers: {}, config }
  }
  await companyInfoAPI.getCompanyInfos(2, 25)
  assert.equal(sent.url, '/company-reviews/company-info/')
  assert.deepEqual(sent.params, { page: 2, page_size: 25 })
})
