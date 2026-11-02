<template><WorkspaceShell title="岗位与题库" description="查询可追溯来源的岗位、企业和面试题；示例数据不代表真实招聘。"><form class="platform-form" @submit.prevent="run(()=>api.catalog(kind,{q:query,...(city?{city:city}:{})}))"><label>资料类型<select v-model="kind"><option value="jobs">岗位</option><option value="companies">企业</option><option value="questions">题库</option></select></label><label>关键词<input v-model="query" /></label><label>城市<input v-model="city" /></label><div class="platform-actions"><button class="career-button career-button-primary" :disabled="busy">{{ busy ? '请求中…' : '查询资料' }}</button></div></form><details><summary>管理员导入</summary><form class="platform-form" @submit.prevent="run(()=>api.importBatch({kind,records:JSON.parse(batch),dry_run:dryRun}))"><label>JSON 记录数组<textarea v-model="batch" required /></label><label><span><input v-model="dryRun" type="checkbox" />仅校验，不写入</span></label><button class="career-button" :disabled="busy">校验并导入</button></form></details><p class="platform-status" role="status">{{ status }}</p><section class="platform-result"><h2>岗位、企业与题目列表</h2><p>该区域由负责成员接入实际业务结果。骨架不展示模拟成功或虚构内容。</p></section></WorkspaceShell></template>
<script setup>
import {ref,onMounted} from 'vue'
import WorkspaceShell from '@/features/career-platform/WorkspaceShell.vue'
import {platformAPI as api} from '@/features/career-platform'
import {newRequestId} from '@/features/career-platform/api.js'
import {useOperation} from '@/features/career-platform/useOperation.js'
const {busy,status,run}=useOperation()
const batch=ref('[]'),dryRun=ref(true)
const kind=ref('jobs'),query=ref(''),city=ref('')
onMounted(()=>run(signal=>api.catalog('jobs',{},signal)))
</script>
