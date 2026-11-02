import assert from 'node:assert/strict'
import test from 'node:test'
import { skillGroups, normalizeIntroduction, introductionProgress, introductionProfile, introductionText, saveIntroductionDraft } from '../src/features/career-paths/self-introduction.js'

test('invalid drafts normalize to an editable empty form', () => {
  for (const input of [null, undefined, [], 'broken', 42]) {
    const form = normalizeIntroduction(input)
    assert.equal(form.name, '')
    assert.equal(form.goal, '')
    assert.deepEqual(form.skills, [])
    assert.deepEqual(introductionProgress(form), { completed: 0, total: 9, percent: 0 })
  }
  assert.equal(normalizeIntroduction({ name: {}, skills: 'Python' }).name, '')
})

test('draft normalization deduplicates skills and preserves legacy custom selections', () => {
  const form = normalizeIntroduction({ name: '同学', skills: ['Python 开发', '', ' ', null, 12, 'Python 开发', 'Vue'], ignored: 'x' })
  assert.deepEqual(form.skills, ['Python 开发', 'Vue'])
  assert.equal(form.name, '同学')
  assert.equal('ignored' in form, false)
})

test('all 24 original skill payload values remain available', () => {
  assert.deepEqual(skillGroups.map(group => group.items.length), [6, 6, 6, 6])
  assert.deepEqual(skillGroups.flatMap(group => group.items.map(skill => skill.value)), [
    'Python 开发', 'PostgreSQL 数据库', 'RESTfulAPI设计', '并发 / 异步编程', 'Linux 使用与脚本', 'Git / 版本管理',
    '数据分析', '机器学习', '深度学习框架', 'NLP', 'CV(图像处理)', '数据可视化(Plotly)',
    '基本电脑操作', '效率管理', '效率管理工具:任务管理', '英文资料阅读能力', '安全意识意识', '学习与问题解决能力',
    '线性代数与矩阵运算', '概率论与统计推断', '离散数学', '数据结构', '算法设计', '计算机网络',
  ])
})

test('profile and recommendation text retain the existing API contract', () => {
  const form = normalizeIntroduction({ name: '同学', school: '测试学校', major: '计算机', grade: '大三', gender: '女', skills: ['Python 开发', 'NLP'], otherSkills: '项目经历', selfDescription: '喜欢协作', goal: '工程师' })
  assert.deepEqual(introductionProfile(form), { name: '同学', school: '测试学校', major: '计算机', grade: '大三', gender: '女', skills: 'Python 开发,NLP', other_skills: '项目经历', self_introduction: '喜欢协作', career_goal: '工程师' })
  assert.equal(introductionText(form), '姓名: 同学\n学校: 测试学校\n专业: 计算机\n年级: 大三\n性别: 女\n技能: Python 开发、NLP\n其他技能: 项目经历\n条件自述: 喜欢协作\n职业期望: 工程师')
  assert.equal(introductionText(normalizeIntroduction()), '姓名: \n学校: \n专业: \n年级: \n性别: \n技能: 无\n其他技能: 无\n条件自述: 无\n职业期望: 无')
  assert.deepEqual(introductionProgress(form), { completed: 9, total: 9, percent: 100 })
})

test('progress ignores whitespace and counts skills as one item', () => {
  assert.deepEqual(introductionProgress(normalizeIntroduction({ name: '同学', goal: '  ', skills: ['NLP', '数据分析'] })), { completed: 2, total: 9, percent: 22 })
})

test('removed gender options restore as unselected and submit as null', () => {
  for (const gender of ['', null, '暂不填写', 'invalid']) {
    const form = normalizeIntroduction({ gender })
    assert.equal(form.gender, '')
    assert.equal(introductionProfile(form).gender, null)
    assert.equal(introductionProgress(form).completed, 0)
  }
  for (const gender of ['男', '女']) {
    assert.equal(introductionProfile(normalizeIntroduction({ gender })).gender, gender)
  }
})

test('draft save writes the existing storage key with normalized data', () => {
  const saved = new Map([['token', 'offline-session']])
  const storage = { getItem: key => saved.get(key), setItem: (key, value) => saved.set(key, value) }
  assert.equal(saveIntroductionDraft(storage, 'offline-session', { name: '同学' }), 'saved')
  assert.deepEqual(JSON.parse(saved.get('selfIntroduction')), normalizeIntroduction({ name: '同学' }))
})

test('pending save cannot resurrect a draft after logout or an account change', () => {
  for (const current of [null, 'another-session']) {
    const storage = { getItem: () => current, setItem: () => assert.fail('must not restore personal data') }
    assert.equal(saveIntroductionDraft(storage, 'original-session', { name: '同学' }), 'session-changed')
    assert.equal(saveIntroductionDraft(storage, '', { name: '同学' }), 'session-changed')
  }
})

test('storage failures are reported instead of claiming the draft was saved', () => {
  const denied = { getItem: () => { throw new Error('blocked') } }
  const full = { getItem: () => 'offline-session', setItem: () => { throw new Error('quota') } }
  for (const storage of [denied, full]) assert.equal(saveIntroductionDraft(storage, 'offline-session', {}), 'unavailable')
})
