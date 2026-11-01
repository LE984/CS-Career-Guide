import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'
import { createInterviewService } from '../src/features/interview/service.js'
import { LegacyInterviewImplementation, formatLegacyResume } from '../src/features/interview/legacy/implementation.js'
import { readLegacyStream } from '../src/features/interview/legacy/stream.js'
import { createTextReveal } from '../src/features/interview/text-reveal.js'
import { createSessionClock } from '../src/features/interview/session-clock.js'
import { resumePreview } from '../src/features/interview/resume-preview.js'

const baseline = JSON.parse(await readFile(new URL('./fixtures/interview-legacy.json', import.meta.url), 'utf8'))

test('interview voice selection and cancellation reach each request; reviews remain text-only', async () => {
  const calls = []
  const implementation = new LegacyInterviewImplementation({readResume: () => null,
    chatStream: async (...args) => { calls.push(args); return response([{type:'chunk',content:'回复'}]) },
    saveReview() {}, transcribe() {},
  })
  const controller = new AbortController()
  const context = {style:'gentle',sessionId:'s1',enableTts:true,signal:controller.signal}
  await implementation.start(context)
  await implementation.answer({...context,answer:'回答'})
  await implementation.generateReview({...context,messages:[{type:'user',content:'经历'.repeat(50)}]})
  assert.deepEqual(calls.map(args => args[4].enableTts), [true,true,false])
  assert.ok(calls.every(args => args[4].signal === controller.signal))
})

function response(events) {
  return new Response(events.map(event => `data: ${JSON.stringify(event)}\n\n`).join('') + 'data: [DONE]\n\n')
}

for (const scenario of baseline.turns) {
  test(`legacy ${scenario.style}: start, answer and review match original requests`, async () => {
    const calls = []
    const service = createInterviewService(new LegacyInterviewImplementation({
      readResume: () => JSON.stringify(scenario.resume),
      chatStream: async (...args) => {
        calls.push(args)
        return response([{ type: 'chunk', content: '测试内容' }])
      },
      saveReview: async () => ({ success: true }), transcribe: async () => ({ result: 'success' })
    }))
    const context = { style: scenario.style, sessionId: 'baseline-session', durationMinutes: 15 }
    await service.start(context)
    await service.answer({ ...context, answer: scenario.answer })
    const review = await service.generateReview({ ...context, messages: scenario.conversation })
    assert.deepEqual(calls.map(args => args.slice(0, 4)), scenario.requests)
    assert.ok(calls.every(args => args[4].enableTts === false))
    assert.deepEqual(review, { skipped: false, content: '测试内容' })
  })
}

test('stream handles split UTF-8, CRLF, DONE followed by session, and an unterminated final event once', async () => {
  const text = 'data: {"type":"chunk","content":"下一题"}\r\n\r\ndata: [DONE]\r\n\r\ndata: {"type":"end","session_id":"s1"}'
  const bytes = new TextEncoder().encode(text)
  const stream = new ReadableStream({ start(controller) {
    for (const byte of bytes) controller.enqueue(Uint8Array.of(byte))
    controller.close()
  } })
  const events = []
  await readLegacyStream(new Response(stream), event => events.push(event))
  assert.deepEqual(events, [{ type: 'chunk', content: '下一题' }, { type: 'end', session_id: 's1' }])
  assert.equal(stream.locked, false)
})

test('stream forwards audio and errors, ignores debug comments and malformed data', async () => {
  const events = []
  await readLegacyStream(new Response(': ping\n\ndata: bad-json\n\ndata: {"type":"audio","audio":"fake"}\n\ndata: {"type":"error","content":"failed"}\n\n'), event => events.push(event))
  assert.deepEqual(events, [{ type: 'audio', audio: 'fake' }, { type: 'error', content: 'failed' }])
  await assert.rejects(readLegacyStream(new Response('', { status: 503 })), /503/)
  await assert.rejects(readLegacyStream(new Response('')), /未收到任何数据/)
})

test('review keeps existing save payload and excludes the closing placeholder', async () => {
  let saved
  const messages = [...baseline.turns[0].conversation, { type: 'ai', content: '面试结束，感谢你的参与！正在生成面试复盘...' }]
  const service = createInterviewService(new LegacyInterviewImplementation({
    readResume: () => null, chatStream: async () => response([{ type: 'chunk', content: '优点' }, { type: 'chunk', content: '与建议' }]),
    saveReview: async data => { saved = data; return { success: true } }, transcribe: async data => data
  }))
  const chunks = []
  const review = await service.generateReview({ messages, style: 'technical', sessionId: 's1' }, event => chunks.push(event.content))
  assert.deepEqual(chunks, ['优点', '与建议'])
  await service.saveReview({ messages, content: review.content, style: 'technical', sessionId: 's1', remainingTime: 720 })
  assert.deepEqual(saved, { session_id: 's1', review_content: '优点与建议', interview_style: 'technical', interview_duration: 3, question_count: 1, answer_count: 1 })
  const audio = new FormData()
  assert.equal(await service.transcribe(audio), audio)
})

test('short conversations do not call the model, and a missing resume stays optional', async () => {
  let calls = 0
  const implementation = new LegacyInterviewImplementation({
    readResume: () => null, chatStream: async () => { calls++; return response([{ type: 'chunk', content: '问题' }]) },
    saveReview() {}, transcribe() {}
  })
  const result = await implementation.generateReview({ messages: [], style: 'gentle' })
  assert.equal(result.skipped, true)
  assert.equal(calls, 0)
  assert.equal(formatLegacyResume(null), null)
  await implementation.start({ style: 'gentle', sessionId: '' })
  assert.equal(calls, 1)
})

test('an alternative implementation runs through the same facade without legacy HTTP dependencies', async () => {
  const alternative = {
    async start(context, onEvent) { await onEvent({ type: 'chunk', content: `new:${context.style}` }) },
    answer() { return this.marker }, generateReview() {}, saveReview() {}, transcribe() {}, marker: 'replacement'
  }
  const service = createInterviewService(alternative)
  const events = []
  await service.start({ style: 'technical' }, event => events.push(event))
  assert.deepEqual(events, [{ type: 'chunk', content: 'new:technical' }])
  assert.equal(service.answer(), 'replacement')
  assert.throws(() => createInterviewService({}), /must provide start/)
})

test('unavailable browser storage does not prevent a legacy interview from starting', async () => {
  let request
  const implementation = new LegacyInterviewImplementation({
    readResume() { throw new Error('storage unavailable') },
    chatStream: async (...args) => { request = args; return response([{ type: 'chunk', content: '你好' }]) },
    saveReview() {}, transcribe() {}
  })
  const original = console.error
  console.error = () => {}
  try {
    await implementation.start({ style: 'gentle', sessionId: 's1' })
  } finally {
    console.error = original
  }
  assert.ok(request[0].includes('现在开始面试。'))
  assert.ok(!request[0].includes('【面试者简历信息】'))
})

test('selected duration reaches the interviewer and review uses elapsed selected time', async () => {
  let prompt, saved
  const implementation = new LegacyInterviewImplementation({readResume: () => null,
    chatStream: async text => { prompt = text; return response([{type:'chunk',content:'问题'}]) },
    saveReview: data => { saved = data }, transcribe() {},
  })
  await implementation.start({style:'gentle'})
  assert.match(prompt, /45分钟/)
  await implementation.start({style:'gentle',durationMinutes:60})
  assert.match(prompt, /60分钟/)
  await implementation.saveReview({messages:[],content:'复盘',remainingTime:2580,totalDurationSeconds:2700})
  assert.equal(saved.interview_duration,2)
})

test('clock catches up after background throttling and excludes paused wall time', () => {
  let now = 0
  const clock = createSessionClock(2700, () => now)
  now = 125000
  assert.equal(clock.remaining(),2575)
  clock.pause(); now += 3600000
  assert.equal(clock.remaining(),2575)
  clock.resume(); now += 2575000
  assert.equal(clock.remaining(),0)
  now += 10000
  assert.equal(clock.remaining(),0)
})

function revealHarness() {
  let time=0, serial=0, callbacks=new Map(), visible='', pending=false, immediate=false
  const reveal=createTextReveal((text,busy)=>{visible=text;pending=busy},{now:()=>time,
    requestFrame:fn=>{callbacks.set(++serial,fn);return serial},cancelFrame:id=>callbacks.delete(id),immediate:()=>immediate})
  return {reveal, get visible(){return visible},get pending(){return pending},get scheduled(){return callbacks.size},
    reduce(){immediate=true;reveal.flush()},step(ms=16){time+=ms;const active=[...callbacks.values()];callbacks.clear();active.forEach(fn=>fn(time))}}
}

test('bursty text reveals across frames without losing emoji, appended chunks or the final tail', () => {
  const h=revealHarness(), first='你好👩‍💻，这里是面试。'.repeat(8)
  h.reveal.set(first)
  assert.equal(h.visible,'你')
  h.step(16)
  assert.ok(h.visible.length<first.length)
  h.reveal.set(first+'下一题。')
  for(let i=0;i<120;i++)h.step()
  assert.equal(h.visible,first+'下一题。')
  assert.equal(h.pending,false)
  assert.equal(h.scheduled,0)
})

test('replacement, reduced motion, and teardown never leave an obsolete animation running', () => {
  const h=revealHarness()
  h.reveal.set('旧回复'.repeat(30));h.step();h.reveal.set('新回复')
  h.reduce()
  assert.equal(h.visible,'新回复')
  h.reveal.set('尊重减少动态效果的设置。')
  assert.equal(h.visible,'尊重减少动态效果的设置。')
  const other=revealHarness();other.reveal.set('长回复'.repeat(20));other.reveal.dispose()
  assert.equal(other.scheduled,0)
})

test('resume preview includes all saved sections and tolerates empty optional records', () => {
  const preview=resumePreview({name:' 示例用户 ',target_position:'前端工程师',phone:'123',email:'demo@example.test',address:'示例城市',
    self_evaluation:'自评\n第二行',skills:'Vue、Python',education:[{school:'示例学校',major:'计算机',period:'2022—2026',description:'课程'}],
    experience:[{company:'示例企业',position:'实习生',description:'负责测试'}],projects:[{name:'面试项目',role:'开发',url:'javascript:example',description:'<img src=x onerror=alert(1)>'}],
    certificates:[{name:'证书',issuer:'示例机构'}],awards:[{name:'奖项',period:'2025'}]})
  assert.equal(preview.empty,false)
  assert.equal(preview.name,'示例用户')
  assert.equal(preview.contacts.length,3)
  assert.deepEqual(preview.sections.map(s=>s.title),['个人自评','专业技能','教育背景','实习与工作经历','项目经历','证书认证','获奖经历'])
  assert.equal(preview.sections[4].items[0].description,'<img src=x onerror=alert(1)>')
  assert.equal(preview.sections[4].items[0].url,'javascript:example')
  assert.equal(resumePreview({id:1,education:[null,{}, {id:2}],projects:'invalid'}).empty,true)
  assert.equal(resumePreview(null).empty,true)
})
