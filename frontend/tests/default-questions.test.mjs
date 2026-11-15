import test from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { defaultQuestionSets, defaultQuestionSource } from '../src/views/career-platform/default-questions.js'

test('built-in study questions are original, uniquely identified and carry explanatory reference points',()=>{
  const questions=defaultQuestionSets.flatMap(set=>set.questions)
  assert.equal(defaultQuestionSets.length,3)
  assert.equal(questions.length,9)
  assert.equal(new Set(questions.map(q=>q.id)).size,9)
  assert.match(defaultQuestionSource,/自编.*非真实面经/)
  for(const q of questions){assert.ok(q.question.length>10);assert.ok(q.key_points.length>=3);assert.ok(q.key_points.every(p=>typeof p==='string'&&p.length>10));assert.doesNotMatch(q.id,/^[0-9a-f]{8}-/)}
})

test('local self-practice cannot accidentally create formal sessions or store private answers',async()=>{
  const source=await readFile(new URL('../src/views/career-platform/DefaultPractice.vue',import.meta.url),'utf8')
  assert.doesNotMatch(source,/platformAPI|localStorage|sessionStorage|fetch\(|api\./)
  assert.match(source,/不调用模型、不保存历史/)
  assert.match(source,/onBeforeRouteLeave/)
})

test('resume optimization lives in the existing resume workspace and legacy links redirect there',async()=>{
  const router=await readFile(new URL('../src/router/index.js',import.meta.url),'utf8')
  const resume=await readFile(new URL('../src/views/resume/Index.vue',import.meta.url),'utf8')
  const nav=await readFile(new URL('../src/features/career-platform/CourseNav.vue',import.meta.url),'utf8')
  assert.match(router,/name:'PlatformResume',redirect:/)
  assert.match(router,/path:'\/resume',query:\{\.\.\.to.query,tab:'optimize'\}/)
  assert.match(resume,/<OptimizationPanel v-if="showOptimization"/)
  assert.match(resume,/v-show="!showOptimization"/)
  assert.doesNotMatch(nav,/title: '简历优化'/)
})
