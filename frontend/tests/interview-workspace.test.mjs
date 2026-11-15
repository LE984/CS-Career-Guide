import test from 'node:test'
import assert from 'node:assert/strict'
import { saveInterviewWorkspace,restoreInterviewWorkspace,clearInterviewWorkspace,createConversationFollow } from '../src/features/interview/workspace-state.js'
import { clearSession } from '../src/auth/session.js'
import { LegacyInterviewImplementation } from '../src/features/interview/legacy/implementation.js'

test('navigation recovery retains session, draft and partial reply with isolated copies',()=>{
 const state={sessionId:'s',messages:[{type:'ai',content:'partial'}],inputMessage:'draft',remainingTime:123}
 saveInterviewWorkspace('owner-a',state);state.messages[0].content='changed'
 const restored=restoreInterviewWorkspace('owner-a');assert.equal(restored.messages[0].content,'partial');assert.equal(restored.inputMessage,'draft')
 restored.messages=[];assert.equal(restoreInterviewWorkspace('owner-a').messages.length,1)
})
test('account changes and logout discard private workspace',()=>{
 saveInterviewWorkspace('a',{sessionId:'private'});assert.equal(restoreInterviewWorkspace('b'),null);assert.equal(restoreInterviewWorkspace('a'),null)
 saveInterviewWorkspace('a',{sessionId:'private'});globalThis.localStorage={removeItem(){}};clearSession();assert.equal(restoreInterviewWorkspace('a'),null);clearInterviewWorkspace()
})
test('user input immediately interrupts following, tracking resumes only near bottom',()=>{
 const follow=createConversationFollow();assert.equal(follow.following,true)
 follow.interrupt();assert.equal(follow.following,false)
 follow.track({scrollHeight:1000,clientHeight:300,scrollTop:200});assert.equal(follow.following,false)
 follow.track({scrollHeight:1000,clientHeight:300,scrollTop:699});assert.equal(follow.following,true)
 follow.interrupt();follow.resume();assert.equal(follow.following,true)
})
test('first answer invites project and second answer starts one project question',async()=>{
 const calls=[];const impl=new LegacyInterviewImplementation({chatStream:async(...args)=>{calls.push(args);return new Response('data: {"type":"chunk","content":"下一步"}\n\n')},readResume:()=>null})
 await impl.answer({answer:'自我介绍',answerNumber:1,style:'technical',sessionId:'s'})
 await impl.answer({answer:'项目介绍',answerNumber:2,style:'technical',sessionId:'s'})
 assert.match(calls[0][0],/刚完成自我介绍/);assert.match(calls[1][0],/刚完成项目介绍/)
 assert.equal(calls[0][3],'s');assert.equal(calls[1][3],'s')
})
