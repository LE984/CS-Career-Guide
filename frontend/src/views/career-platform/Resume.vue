<template><WorkspaceShell title="简历优化" description="对照目标岗位提出有原文依据的建议，确认前保持原简历。"><form class="platform-form" @submit.prevent="run(()=>api.analyze({jd_text:jd,resume_revision:revision,request_id:newRequestId()}))"><label>目标岗位 JD<textarea v-model="jd" maxlength="20000" required /></label><label>当前简历版本<input v-model.number="revision" type="number" min="0" /></label><div class="platform-actions"><button class="career-button career-button-primary" :disabled="busy">{{ busy ? '请求中…' : '分析简历' }}</button></div></form><form class="platform-form" @submit.prevent="run(()=>api.apply(analysis,{base_revision:revision,accepted_suggestion_ids:accepted.split(',').map(s=>s.trim()),request_id:newRequestId()}))"><label>分析记录 ID<input v-model="analysis" required /></label><label>已确认建议 ID（逗号分隔）<input v-model="accepted" required /></label><button class="career-button" :disabled="busy">确认应用已选建议</button></form><p class="platform-status" role="status">{{ status }}</p><section class="platform-result"><h2>原文、证据与修改建议</h2><p>该区域由负责成员接入实际业务结果。骨架不展示模拟成功或虚构内容。</p></section></WorkspaceShell></template>
<script setup>
import {ref,onMounted} from 'vue'
import WorkspaceShell from '@/features/career-platform/WorkspaceShell.vue'
import {platformAPI as api} from '@/features/career-platform'
import {newRequestId} from '@/features/career-platform/api.js'
import {useOperation} from '@/features/career-platform/useOperation.js'
const {busy,status,run}=useOperation()
const analysis=ref(''),accepted=ref('')
const jd=ref(''),revision=ref(0)
onMounted(()=>run(signal=>api.analyses(signal)))
</script>
