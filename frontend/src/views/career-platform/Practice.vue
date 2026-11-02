<template><WorkspaceShell title="岗位题库练习" description="从有来源的题库开始文字练习；原自由模拟面试继续保留。"><form class="platform-form" @submit.prevent="run(()=>api.retrieve({role:role,topic:topic,difficulty:difficulty,top_k:5,request_id:newRequestId()}))"><label>岗位方向<input v-model="role" required /></label><label>知识点<input v-model="topic" /></label><label>难度<select v-model="difficulty"><option value="easy">基础</option><option value="medium">进阶</option><option value="hard">深入</option></select></label><div class="platform-actions"><button class="career-button career-button-primary" :disabled="busy">{{ busy ? '请求中…' : '检索候选题' }}</button></div></form><form class="platform-form" @submit.prevent="run(()=>api.start({role,topic,difficulty,request_id:newRequestId()}))"><div class="platform-actions"><button class="career-button" :disabled="busy">开始岗位练习</button></div></form><form class="platform-form" @submit.prevent="run(()=>api.answer(session,{question_id:question,answer,request_id:newRequestId()}))"><label>会话 ID<input v-model="session" required /></label><label>题目 ID<input v-model="question" required /></label><label>本题回答<textarea v-model="answer" required /></label><div class="platform-actions"><button class="career-button" :disabled="busy">提交本题回答</button><button type="button" class="career-button" :disabled="busy || !session" @click="run(()=>api.finish(session,{request_id:newRequestId()}))">结束练习</button></div></form><p class="platform-status" role="status">{{ status }}</p><section class="platform-result"><h2>候选题、来源与回答反馈</h2><p>该区域由负责成员接入实际业务结果。骨架不展示模拟成功或虚构内容。</p></section></WorkspaceShell></template>
<script setup>
import {ref,onMounted} from 'vue'
import WorkspaceShell from '@/features/career-platform/WorkspaceShell.vue'
import {platformAPI as api} from '@/features/career-platform'
import {newRequestId} from '@/features/career-platform/api.js'
import {useOperation} from '@/features/career-platform/useOperation.js'
const {busy,status,run}=useOperation()
const session=ref(''),question=ref(''),answer=ref('')
const role=ref('Java后端'),topic=ref(''),difficulty=ref('easy')

</script>
