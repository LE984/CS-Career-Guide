import assert from 'node:assert/strict'
import test from 'node:test'
import { careerCategories, filterCareerCategories, hasIntroduction, normalizeCareerAnalysis, normalizeMatchScore, normalizeRecommendations, readEvaluationState, saveCareerSelection, selectedCareerName } from '../src/features/career-paths/evaluation.js'

function storageFor(values = {}) {
  const entries = new Map(Object.entries(values).map(([key, value]) => [key, JSON.stringify(value)]))
  return { getItem: key => entries.get(key) ?? null, setItem: (key, value) => entries.set(key, value) }
}

test('missing recommendation data stays empty without manufactured matches or analysis', () => {
  const state = readEvaluationState(storageFor())
  assert.deepEqual(state.recommendations, [])
  assert.deepEqual(state.analysis, { overall: '', careers: [], actionPlan: [] })
  assert.equal(state.hasIntroduction, false)
  assert.equal(state.selectedCareer, '')
})

test('match scores support numeric and percent strings, preserve zero, reject invalid ranges', () => {
  for (const [input, expected] of [[0, 0], ['0%', 0], ['90%', 90], [' 82.5％ ', 82.5], [100, 100]]) {
    assert.equal(normalizeMatchScore(input), expected)
  }
  for (const input of [null, undefined, '', ' ', false, {}, [], '90%%', 'abc', -1, 101, Infinity, NaN]) {
    assert.equal(normalizeMatchScore(input), null)
  }
})

test('legacy recommendation aliases work and malformed cards cannot break rendering', () => {
  const result = normalizeRecommendations([null, 'invalid', {}, { career: 'Web前端', matchScore: '90%', reason: 'Vue' }, { 职业: '测试工程师', 匹配度: 0, 推荐理由: '测试经验' }, { career: 'Web前端', matchScore: 99 }])
  assert.deepEqual(result, [{ career: 'Web前端', matchScore: 90, reason: 'Vue' }, { career: '测试工程师', matchScore: 0, reason: '测试经验' }])
  assert.deepEqual(normalizeRecommendations({ cards: [] }), [])
})

test('analysis tolerates missing careers and normalizes text and list fields', () => {
  assert.deepEqual(normalizeCareerAnalysis({ overall: '已有概述' }), { overall: '已有概述', careers: [], actionPlan: [] })
  const result = normalizeCareerAnalysis({ careers: [null, { title: 'Python', reasons: '已有项目', skills: ['Python', {}, 'Python'], nextStep: '补充项目', matchScore: '88%', salaryRange: {} }], actionPlan: { short: ['整理简历'], medium: '增加实践' } })
  assert.deepEqual(result.careers[0].reasons, ['已有项目'])
  assert.deepEqual(result.careers[0].skills, ['Python'])
  assert.deepEqual(result.careers[0].nextSteps, ['补充项目'])
  assert.equal(result.careers[0].matchScore, 88)
  assert.equal(result.careers[0].salaryRange, '')
  assert.equal(result.actionPlan.length, 2)
})

test('cards without an accordion do not invent Python-specific background', () => {
  const state = readEvaluationState(storageFor({ careerRecommendations: [{ career: 'Web前端', matchScore: 85, reason: '前端经验' }] }))
  assert.equal(state.recommendations[0].career, 'Web前端')
  assert.equal(state.analysis.overall, '')
  assert.deepEqual(state.analysis.careers, [])
})

test('analysis-only results keep provided scores and never infer a percentage from market heat', () => {
  const state = readEvaluationState(storageFor({ careerAnalysis: { careers: [{ title: 'Python', marketDemand: '高', reasons: ['项目经验'] }] } }))
  assert.equal(state.recommendations[0].reason, '项目经验')
  assert.equal(state.recommendations[0].matchScore, null)
})

test('malformed browser storage returns a notice while valid records remain available', () => {
  const storage = storageFor({ careerRecommendations: [{ career: 'Python', matchScore: 90 }] })
  storage.setItem('careerAnalysis', '{broken')
  const state = readEvaluationState(storage)
  assert.deepEqual(state.issues, ['careerAnalysis'])
  assert.equal(state.recommendations.length, 1)
  const unavailable = readEvaluationState({ getItem() { throw new Error('blocked') } })
  assert.equal(unavailable.issues.length, 4)
  assert.deepEqual(unavailable.recommendations, [])
})

test('selection restores a single known or recommended target, never chooses a recommendation implicitly', () => {
  for (const selected of [null, [], '', [''], [{ career: 'Python' }]]) assert.equal(selectedCareerName(selected), '')
  assert.equal(selectedCareerName(['Python', 'Java']), 'Python')
  assert.equal(readEvaluationState(storageFor({ careerRecommendations: [{ career: 'Web前端' }] })).selectedCareer, '')
  assert.equal(readEvaluationState(storageFor({ selectedCareers: ['Python'] })).selectedCareer, 'Python')
  assert.equal(readEvaluationState(storageFor({ selectedCareers: ['过期岗位'] })).selectedCareer, '')
  assert.equal(readEvaluationState(storageFor({ selectedCareers: ['新的推荐方向'], careerRecommendations: [{ career: '新的推荐方向' }] })).selectedCareer, '新的推荐方向')
})

test('search is case-insensitive, supports category names and removes repeated rows within a category', () => {
  assert.deepEqual(filterCareerCategories('pYtHoN').flatMap(group => group.roles), ['Python'])
  assert.equal(filterCareerCategories('前端').some(group => group.id === 'frontend' && group.roles.includes('React/Vue')), true)
  assert.deepEqual(filterCareerCategories('Python', 'ai'), [])
  assert.deepEqual(filterCareerCategories('unmatched-term'), [])
  assert.equal(careerCategories.length, 9)
  assert.equal(new Set(careerCategories.flatMap(group => group.roles)).size, 62)
  for (const group of careerCategories) assert.equal(new Set(group.roles).size, group.roles.length)
})

test('profile readiness rejects empty or corrupt objects without adding required fields', () => {
  for (const value of [null, [], '', {}, { goal: ' ', skills: [] }, { skills: {} }]) assert.equal(hasIntroduction(value), false)
  assert.equal(hasIntroduction({ major: '计算机' }), true)
  assert.equal(hasIntroduction({ skills: ['Python 开发'] }), true)
})

test('selection persistence preserves the existing array contract and respects logout', () => {
  const storage = storageFor()
  storage.setItem('token', 'session-a')
  assert.equal(saveCareerSelection(storage, 'session-a', 'Python'), 'saved')
  assert.deepEqual(JSON.parse(storage.getItem('selectedCareers')), ['Python'])
  assert.equal(saveCareerSelection(storage, 'session-a', ''), 'saved')
  assert.deepEqual(JSON.parse(storage.getItem('selectedCareers')), [])
  storage.setItem('token', 'session-b')
  assert.equal(saveCareerSelection(storage, 'session-a', 'Java'), 'session-changed')
  assert.deepEqual(JSON.parse(storage.getItem('selectedCareers')), [])
  assert.equal(saveCareerSelection({ getItem: () => 'a', setItem() { throw new Error('quota') } }, 'a', 'Python'), 'unavailable')
})
