import test from 'node:test'
import assert from 'node:assert/strict'
import {createPlatformAPI,newRequestId,platformFailure} from '../src/features/career-platform/api.js'

test('platform API preserves every request body, UUID and cancellation', async()=>{
  const calls=[]
  const client={get:async(...args)=>calls.push(['GET',...args]),post:async(...args)=>calls.push(['POST',...args])}
  const api=createPlatformAPI(client),signal=new AbortController().signal
  const body={request_id:newRequestId(),role:'Java后端',suggestion_edits:{a:'编辑建议'},retry_summary:true}
  await api.catalog('questions',{topic:'集合'},signal)
  await api.importBatch(body);await api.analyses(signal);await api.analyze(body)
  await api.analysis('id');await api.apply('id',body);await api.retrieve(body)
  await api.sessions(signal);await api.start(body);await api.session('id')
  await api.answer('id',body);await api.finish('id',body)
  await api.evaluations(signal);await api.evaluate(body);await api.evaluation('id');await api.exportEvaluation('id')
  assert.deepEqual(calls.map(c=>c.slice(0,2)),[
    ['GET','/career-platform/catalog/questions/'],['POST','/career-platform/catalog/imports/'],
    ['GET','/career-platform/resume-analyses/'],['POST','/career-platform/resume-analyses/'],
    ['GET','/career-platform/resume-analyses/id/'],['POST','/career-platform/resume-analyses/id/apply/'],
    ['POST','/career-platform/questions/retrieve/'],['GET','/career-platform/practice-sessions/'],
    ['POST','/career-platform/practice-sessions/'],['GET','/career-platform/practice-sessions/id/'],
    ['POST','/career-platform/practice-sessions/id/answers/'],['POST','/career-platform/practice-sessions/id/finish/'],
    ['GET','/career-platform/evaluation-runs/'],['POST','/career-platform/evaluation-runs/'],
    ['GET','/career-platform/evaluation-runs/id/'],['GET','/career-platform/evaluation-runs/id/export/'],
  ])
  assert.ok(calls.filter(c=>c[0]==='POST').every(c=>c[2]===body))
  assert.equal(calls[0][2].signal,signal)
  assert.equal(calls[2][2].signal,signal)
})

test('UUIDs are portable v4 identifiers, IDs cannot alter resource paths',async()=>{
  const ids=Array.from({length:200},newRequestId)
  assert.equal(new Set(ids).size,200)
  assert.ok(ids.every(id=>/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/.test(id)))
  let url
  await createPlatformAPI({get:async path=>{url=path}}).session('../foreign?owner=1')
  assert.equal(url,'/career-platform/practice-sessions/..%2Fforeign%3Fowner%3D1/')
})

test('unfinished, forbidden, missing and conflicting operations stay distinguishable',()=>{
  const messages=[501,403,404,409].map(status=>platformFailure({response:{status}}))
  assert.equal(new Set(messages).size,4)
  assert.match(messages[0],/功能待实现/)
  assert.doesNotMatch(platformFailure({response:{status:500,data:{secret:'do-not-display'}}}),/do-not-display/)
})
