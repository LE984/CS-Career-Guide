<template><WorkspaceShell title="练习记录" description="查看自己的题目、实际回答、反馈与结束总结。"><form class="platform-form" @submit.prevent="run(()=>api.session(id))"><label>会话 ID<input v-model="id" required pattern="[0-9a-fA-F-]{36}" /></label><div class="platform-actions"><button class="career-button career-button-primary" :disabled="busy">{{ busy ? '请求中…' : '查看详情' }}</button></div></form><p class="platform-status" role="status">{{ status }}</p><section class="platform-result"><h2>练习列表与单次详情</h2><p>该区域由负责成员接入实际业务结果。骨架不展示模拟成功或虚构内容。</p></section></WorkspaceShell></template>
<script setup>
import {ref,onMounted} from 'vue'
import WorkspaceShell from '@/features/career-platform/WorkspaceShell.vue'
import {platformAPI as api} from '@/features/career-platform'
import {newRequestId} from '@/features/career-platform/api.js'
import {useOperation} from '@/features/career-platform/useOperation.js'
const {busy,status,run}=useOperation()
const id=ref('')
onMounted(()=>run(signal=>api.sessions(signal)))
</script>
