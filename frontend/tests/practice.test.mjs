import test from 'node:test'
import assert from 'node:assert/strict'
import { createPracticeActions, practiceContext, practiceFailure } from '../src/views/career-platform/practice.js'

const form = {role:' Java后端 ',topic:' 集合 ',difficulty:'easy',jd_text:' ',top_k:5}
const result = {retrieval_id:'receipt',results:[{question_id:'q1'},{question_id:'q2'}]}
function setup(api){let id=0;return createPracticeActions(api,()=>`request-${++id}`)}

test('retrieve uses the formal endpoint payload and freezes the context used to start',async()=>{
  let retrievalBody,startBody
  const actions=setup({retrieve:async data=>{retrievalBody=data;return {data:result}},start:async data=>{startBody=data;return {id:'session'}}})
  const retrieved=await actions.retrieve(form)
  assert.deepEqual(retrievalBody,{role:'Java后端',topic:'集合',difficulty:'easy',top_k:5,request_id:'request-1'})
  const changed={...form,role:'Python后端'}
  await actions.start(retrieved,['q2','q1','foreign'])
  assert.equal(changed.role,'Python后端')
  assert.deepEqual(startBody,{role:'Java后端',topic:'集合',difficulty:'easy',question_ids:['q1','q2'],retrieval_id:'receipt',request_id:'request-2'})
})

test('uncertain start and finish requests replay the original request ID',async()=>{
  const starts=[],finishes=[]
  const actions=setup({start:async data=>{starts.push(data);if(starts.length===1)throw new Error('offline');return {id:'session'}},finish:async(id,data)=>{finishes.push(data);return {status:'ended'}}})
  const retrieved={...result,context:practiceContext(form)}
  await assert.rejects(actions.start(retrieved,['q1']))
  await actions.start(retrieved,['q1'])
  await actions.finish('s');await actions.finish('s')
  assert.equal(starts[0].request_id,starts[1].request_id)
  assert.equal(finishes[0].request_id,finishes[1].request_id)
  assert.notEqual(starts[0].request_id,finishes[0].request_id)
})

test('answers preserve actual text and reuse IDs only for identical question, session and text',async()=>{
  const calls=[],actions=setup({answer:async(id,data)=>{calls.push([id,data]);return data}})
  await actions.answer('s','q',' 实际回答\n第二行 ')
  await actions.answer('s','q',' 实际回答\n第二行 ')
  await actions.answer('s','q','修改回答')
  await actions.answer('other','q','修改回答')
  assert.equal(calls[0][1].answer,' 实际回答\n第二行 ')
  assert.equal(calls[0][1].request_id,calls[1][1].request_id)
  assert.notEqual(calls[1][1].request_id,calls[2][1].request_id)
  assert.notEqual(calls[2][1].request_id,calls[3][1].request_id)
  assert.throws(()=>actions.answer('s','q','  '),/填写/)
  assert.throws(()=>actions.answer('s','q','x'.repeat(20001)),/20000/)
})

test('feedback retries never submit a second answer and explicit later retries get new IDs',async()=>{
  const calls=[],actions=setup({retryFeedback:async(...args)=>{calls.push(args);return {status:'succeeded'}}})
  await actions.retryFeedback('s','a');await actions.retryFeedback('s','a')
  actions.resetFeedbackRetry('s','a');await actions.retryFeedback('s','a')
  assert.deepEqual(calls[0].slice(0,2),['s','a'])
  assert.equal(calls[0][2].request_id,calls[1][2].request_id)
  assert.notEqual(calls[1][2].request_id,calls[2][2].request_id)
  assert.deepEqual(Object.keys(calls[0][2]),['request_id'])
})

test('empty selections, blank roles and malformed retrieval results cannot create sessions',async()=>{
  const actions=setup({retrieve:async()=>({results:[]})})
  assert.throws(()=>practiceContext({...form,role:' '}),/岗位方向/)
  assert.throws(()=>actions.start({...result,context:{}},[]),/至少/)
  await assert.rejects(actions.retrieve(form),/格式异常/)
})

test('no-hit retrieval remains empty, optional JD is sent without inventing a job ID',async()=>{
  let body
  const actions=setup({retrieve:async data=>{body=data;return {results:[],retrieval_id:'empty'}}})
  const response=await actions.retrieve({...form,jd_text:' Spring 开发 '})
  assert.deepEqual(response.results,[])
  assert.equal(body.jd_text,'Spring 开发')
  assert.equal(body.job_id,undefined)
})

test('errors distinguish login, receipt conflict, saved-answer failures and network uncertainty without leaking details',()=>{
  for(const [status,expected] of [[401,/登录/],[409,/凭证/],[503,/可能已保存/],[400,/岗位方向/]]){
    const message=practiceFailure({response:{status,data:{message:'private-secret'}}})
    assert.match(message,expected);assert.doesNotMatch(message,/private-secret/)
  }
  assert.match(practiceFailure({isAxiosError:true}),/结果尚未确认/)
})
